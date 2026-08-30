(function () {
  function getChatBody() {
    return document.getElementById("cognio-chat-body");
  }

  function getNotif() {
    return document.getElementById("cognio-notif");
  }

  function getChat() {
    return document.getElementById("cognio-chat");
  }

  function getIconPulse() {
    return document.getElementById("cognio-icon-pulse");
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatMultilineText(text) {
    return escapeHtml(text).replace(/\n/g, "<br><br>");
  }

  function isChatOpen() {
    const chat = getChat();
    return !!chat && chat.classList.contains("open");
  }

  function showNotif() {
    // Don't interrupt with a notification bubble if the chat is already open —
    // just update the content directly in that case.
    if (isChatOpen()) return;
    const notif = getNotif();
    if (notif) notif.classList.add("visible");
    const pulse = getIconPulse();
    if (pulse) pulse.classList.add("active");
  }

  function hideNotif() {
    const notif = getNotif();
    if (notif) notif.classList.remove("visible");
    const pulse = getIconPulse();
    if (pulse) pulse.classList.remove("active");
  }

  function openChat() {
    const chat = getChat();
    if (chat) chat.classList.add("open");
    hideNotif();
  }

  function closeChat() {
    const chat = getChat();
    if (chat) chat.classList.remove("open");
  }

  function toggleChat() {
    if (isChatOpen()) {
      closeChat();
    } else {
      openChat();
    }
  }

  // ── Public API (kept the same names tracker.js already calls) ──────────────
  window.showOverlay = function (message, meta) {
    const panel = getChatBody();
    if (!panel) return;

    const strain = String(meta?.strain_level || "LOW");
    const explanation = meta?.explanation_note || "";
    const behavior = meta?.behavior_summary || "";
    const confidence =
      meta?.confidence !== undefined && meta?.confidence !== null && meta?.confidence !== ""
        ? `${Math.round(Number(meta.confidence) * 100)}%`
        : "";

    panel.innerHTML = `
      <div class="adapt-badge adapt-${strain}">${escapeHtml(strain)} STRAIN</div>
      <h3 class="adapt-title">Cognio Learning Companion</h3>
      <div class="adapt-text">${formatMultilineText(message || "No adaptation text returned.")}</div>
      <div class="adapt-meta">
        <div><strong>Why this changed:</strong> ${escapeHtml(explanation)}</div>
        <div><strong>Observed behavior:</strong> ${escapeHtml(behavior)}</div>
        ${confidence ? `<div><strong>Model confidence:</strong> ${escapeHtml(confidence)}</div>` : ""}
      </div>
    `;

    // Surface it: a quiet notification bubble first, or — if the chat is
    // already open — just refresh the content in place.
    if (isChatOpen()) {
      panel.scrollTop = 0;
    } else {
      showNotif();
    }
  };

  window.clearOverlay = function () {
    const panel = getChatBody();
    if (!panel) return;

    panel.innerHTML = `
      <div class="companion-empty">
        <div class="companion-icon">✦</div>
        <p>Interact with the lesson and Cognio will adapt the explanation to your learning pattern in real time.</p>
      </div>
    `;

    hideNotif();
    closeChat();
  };

  // Lightweight loading indicator, called by tracker.js while a request is in flight.
  window.cognioSetLoading = function () {
    const panel = getChatBody();
    if (!panel) return;

    if (isChatOpen()) {
      panel.innerHTML = `
        <div class="companion-empty">
          <div class="companion-icon">✦</div>
          <p>Analysing your learning pattern…</p>
        </div>`;
    }

    const pulse = getIconPulse();
    if (pulse) pulse.classList.add("active");
  };

  // ── Wire up the widget ──────────────────────────────────────────────────────
  // Works no matter where/when this script executes: if the DOM is already
  // parsed (script at end of body) wire immediately; otherwise wait for it.
  function wireWidget() {
    const notif = getNotif();
    const iconBtn = document.getElementById("cognio-icon-btn");
    const closeBtn = document.getElementById("cognio-chat-close");

    if (notif) notif.addEventListener("click", openChat);
    if (iconBtn) iconBtn.addEventListener("click", toggleChat);
    if (closeBtn) closeBtn.addEventListener("click", closeChat);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wireWidget);
  } else {
    wireWidget();
  }
})();