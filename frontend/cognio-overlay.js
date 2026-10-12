(function () {
  "use strict";

  var API_URL = "http://localhost:8000/api/v1/visual/solve";
  var $ = function (id) { return document.getElementById(id); };

  function escapeHtml(v) {
    return String(v)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }
  function multiline(t) { return escapeHtml(t).replace(/\n/g, "<br>"); }

  function isChatOpen() { var c = $("cognio-chat"); return !!c && c.classList.contains("open"); }
  function showNotif() {
    if (isChatOpen()) return;
    var n = $("cognio-notif"); if (n) n.classList.add("visible");
    var p = $("cognio-icon-pulse"); if (p) p.classList.add("active");
  }
  function hideNotif() {
    var n = $("cognio-notif"); if (n) n.classList.remove("visible");
    var p = $("cognio-icon-pulse"); if (p) p.classList.remove("active");
  }
  function openChat() { var c = $("cognio-chat"); if (c) c.classList.add("open"); hideNotif(); }
  function closeChat() { var c = $("cognio-chat"); if (c) c.classList.remove("open"); }
  function toggleChat() { isChatOpen() ? closeChat() : openChat(); }

  // ── Public API used by tracker.js ─────────────────────────────────────────
  window.showOverlay = function (message, meta) {
    var panel = $("cognio-chat-body"); if (!panel) return;
    meta = meta || {};
    var strain = String(meta.strain_level || "LOW");
    var conf = (meta.confidence !== undefined && meta.confidence !== null && meta.confidence !== "")
      ? Math.round(Number(meta.confidence) * 100) + "%" : "";

    panel.innerHTML =
      '<div class="adapt-badge adapt-' + escapeHtml(strain) + '">' + escapeHtml(strain) + ' STRAIN</div>' +
      '<h3 class="adapt-title">Cognio Learning Companion</h3>' +
      '<div class="adapt-text">' + multiline(message || "No adaptation text returned.") + '</div>' +
      '<div class="adapt-meta">' +
        '<div><strong>Why this changed:</strong> ' + escapeHtml(meta.explanation_note || "") + '</div>' +
        '<div><strong>Observed behavior:</strong> ' + escapeHtml(meta.behavior_summary || "") + '</div>' +
        (conf ? '<div><strong>Model confidence:</strong> ' + escapeHtml(conf) + '</div>' : "") +
      '</div>';

    if (isChatOpen()) panel.scrollTop = 0; else showNotif();
  };

  window.clearOverlay = function () {
    var panel = $("cognio-chat-body"); if (!panel) return;
    panel.innerHTML =
      '<div class="companion-empty"><div class="companion-icon">✦</div>' +
      '<p>Interact with the lesson and Cognio will adapt the explanation to your learning pattern in real time.</p></div>';
    hideNotif();
    closeChat();
  };

  window.cognioSetLoading = function () {
    var panel = $("cognio-chat-body"); if (!panel) return;
    if (isChatOpen()) {
      panel.innerHTML =
        '<div class="companion-empty"><div class="companion-icon">✦</div><p>Analysing your learning pattern…</p></div>';
    }
    var p = $("cognio-icon-pulse"); if (p) p.classList.add("active");
  };

  // ── Visual solver ─────────────────────────────────────────────────────────
  function appendMessage(label, content, isUser) {
    var panel = $("cognio-chat-body"); if (!panel) return;
    var empty = panel.querySelector(".companion-empty"); if (empty) empty.remove();

    var msg = document.createElement("div");
    msg.className = "solver-message " + (isUser ? "solver-user-message" : "solver-answer-message");
    var h = document.createElement("span");
    h.className = "solver-message-label"; h.textContent = label;
    var b = document.createElement("div"); b.textContent = content;  // never parsed as HTML
    msg.appendChild(h); msg.appendChild(b);
    panel.appendChild(msg);
    panel.scrollTop = panel.scrollHeight;
  }

  function wireVisualSolver() {
    var fileInput = $("cognio-solver-file"), attachBtn = $("cognio-solver-attach"),
        fileName = $("cognio-solver-filename"), questionEl = $("cognio-solver-question"),
        solveBtn = $("cognio-solver-submit"), status = $("cognio-solver-status");
    if (!fileInput || !attachBtn || !solveBtn) return;

    var say = function (t) { if (status) status.textContent = t; };

    attachBtn.addEventListener("click", function () { fileInput.click(); });
    fileInput.addEventListener("change", function () {
      var f = fileInput.files && fileInput.files[0];
      if (fileName) fileName.textContent = f ? f.name : "Attach a question image";
      say("");
    });

    solveBtn.addEventListener("click", async function () {
      var file = fileInput.files && fileInput.files[0];
      var question = questionEl ? questionEl.value.trim() : "";
      if (!file) return say("Choose an image first.");
      if (["image/jpeg", "image/png", "image/webp"].indexOf(file.type) === -1)
        return say("Use a JPG, PNG or WEBP image.");
      if (file.size > 10 * 1024 * 1024) return say("Image must be 10 MB or smaller.");

      var fd = new FormData();
      fd.append("file", file);
      fd.append("question", question);

      openChat();
      appendMessage("YOU", "Image: " + file.name + (question ? "\n" + question : ""), true);
      solveBtn.disabled = true; attachBtn.disabled = true;
      say("Qwen is solving locally…");

      try {
        var res = await fetch(API_URL, { method: "POST", body: fd });
        var data = await res.json().catch(function () { return {}; });
        if (!res.ok) throw new Error(data.detail || "Could not solve the image. Check Ollama and the backend.");
        appendMessage("COGNIO · VISUAL SOLVER", data.answer || "No answer was returned.", false);
        say("Solved locally with Qwen.");
        fileInput.value = "";
        if (fileName) fileName.textContent = "Attach a question image";
        if (questionEl) questionEl.value = "";
      } catch (err) {
        appendMessage("COGNIO · ERROR", err.message || "The solver failed. Check the backend logs.", false);
        say("Solver unavailable.");
      } finally {
        solveBtn.disabled = false; attachBtn.disabled = false;
      }
    });
  }

  // ── Wiring: open/close is wired FIRST and independently of the solver ─────
  function wireWidget() {
    var notif = $("cognio-notif"), icon = $("cognio-icon-btn"), close = $("cognio-chat-close");
    if (notif) notif.addEventListener("click", openChat);
    if (icon) icon.addEventListener("click", toggleChat);
    if (close) close.addEventListener("click", closeChat);
    try { wireVisualSolver(); } catch (e) { console.error("Cognio solver wiring failed:", e); }
    console.log("Cognio overlay loaded");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wireWidget);
  else wireWidget();
})();
