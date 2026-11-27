(() => {
  "use strict";

  if (window.__cognioLearningLoaded) return;
  window.__cognioLearningLoaded = true;

  const API = "/api/v1/learning";
  const NUDGE_COOLDOWN_MS = 180000; // only reconsider after 3 minutes
  const SESSION_ID = `page-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

  const state = {
    startedAt: Date.now(),
    lastActiveAt: Date.now(),
    activeMs: 0,
    totalAttempts: 0,
    wrongAttempts: 0,
    correctAttempts: 0,
    wrongStreak: 0,
    hintsUsed: 0,
    rereads: 0,
    navClicks: 0,
    attemptStartedAt: 0,
    firstLatency: 0,
    latencies: [],
    lastScrollY: window.scrollY,
    maxScrollY: window.scrollY,
    lastAnalysisAt: 0,
    lastNudgeAt: 0,
    lastNudgeLevel: "",
    nudgePending: false,
    nudgeHandled: false,
    inFlight: false,
    pendingAttempt: false,
    lastOutcomeText: "",
    attemptTimer: null,
    blurAt: null
  };

  // The explanation UI now lives inside the main Cognio widget (content.js, "Learning" tab).
  // This file only keeps a small strain indicator in the bottom-left corner.
  const ui = window.__cognioUI;
  if (!ui) {
    console.warn("Cognio widget not found; learning signals disabled on this page.");
    return;
  }

  const host = document.createElement("div");
  host.id = "cognio-learning-companion";
  host.style.cssText =
    "all:initial;position:fixed;left:18px;bottom:18px;z-index:2147483646;";

  const shadow = host.attachShadow({ mode: "closed" });

  shadow.innerHTML = `
    <style>
      * {
        box-sizing:border-box;
        font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      }
      .launcher {
        border:1px solid #444;
        background:#242424;
        color:#f5f5f5;
        border-radius:22px;
        padding:8px 12px;
        box-shadow:0 5px 20px #0006;
        cursor:pointer;
        font-size:11px;
        font-weight:650;
        display:flex;
        gap:8px;
        align-items:center;
      }
      .dot { width:9px;height:9px;border-radius:50%;background:#21b981; }
      .moderate .dot { background:#f5a524; }
      .high .dot { background:#ef5555; }
      .count { color:#aaa;font-weight:500; }
      .consent { position:absolute;left:0;bottom:49px;width:260px;background:#242424;
        color:#f5f5f5;border:1px solid #555;border-radius:13px;padding:13px;
        box-shadow:0 8px 30px #0008;font-size:12px;line-height:1.5; }
      .consent-heading { font-weight:750;font-size:13px;margin-bottom:5px; }
      .consent-desc { color:#ccc;margin-bottom:11px; }
      .consent-actions { display:flex;gap:8px; }
      .consent-actions button { cursor:pointer;border:0;border-radius:8px;
        background:#8b5cf6;color:white;padding:7px 12px;font-size:12px; }
      .consent-actions button.secondary { background:#444;color:white; }
    </style>
    <button class="launcher low" id="launcher"
            title="Cognio strain estimate. Click to open Cognio.">
      <span class="dot"></span>
      <span id="label">LOW</span>
      <span class="count" id="count">✗ 0/0 · 💡 0</span>
    </button>
  `;

  (document.documentElement || document.body).appendChild(host);

  const $ = id => shadow.getElementById(id);

  const status = ui.learnStatus;
  const launcher = $("launcher");
  const analyzeButton = ui.analyzeBtn;
  let currentLevel = "LOW";

  launcher.addEventListener("click", () => ui.open("learning"));

  function hostName() {
    return location.hostname.toLowerCase();
  }

  function activeTimeMs() {
    const current = Date.now();
    return state.activeMs +
      (document.visibilityState === "visible"
        ? Math.max(0, current - state.lastActiveAt)
        : 0);
  }

  function average(values) {
    return values.length
      ? values.reduce((a, b) => a + b, 0) / values.length
      : 0;
  }

  function buildFeatures() {
    const mean = average(state.latencies);
    const last = state.latencies.length
      ? state.latencies[state.latencies.length - 1]
      : 0;

    const attempts = state.totalAttempts;
    const wrong = state.wrongAttempts;

    return {
      latency_delta: last || mean,
      error_rate: attempts ? wrong / attempts : 0,
      attempt_burst: state.wrongStreak >= 3 ? 1 : 0,
      attention_drop: mean >= 5000 ? 1 : 0,
      hint_reliance: attempts
        ? state.hintsUsed / attempts
        : (state.hintsUsed ? 1 : 0),
      cold_start_latency: state.firstLatency,
      exit_flag_ratio: state.navClicks
        ? Math.min(1, state.navClicks / Math.max(1, attempts + state.navClicks))
        : 0,
      reread_normalized: attempts
        ? state.rereads / attempts
        : (state.rereads ? 1 : 0),
      wrong_streak: state.wrongStreak,
      total_attempts: attempts,
      hints_used: state.hintsUsed,
      rereads: state.rereads,
      avg_response_time: mean,
      response_time_spread: state.latencies.length > 1
        ? Math.max(...state.latencies) - Math.min(...state.latencies)
        : 0,
      correct_attempts: state.correctAttempts,
      active_seconds: Math.round(activeTimeMs() / 1000),
      navigation_clicks: state.navClicks
    };
  }

  function updateSignals() {
    ui.signals.textContent =
      `Attempts: ${state.totalAttempts} · Incorrect: ${state.wrongAttempts} · Hints: ${state.hintsUsed}`;
    $("count").textContent =
      `✗ ${state.wrongAttempts}/${state.totalAttempts} · 💡 ${state.hintsUsed}`;
  }

  function setLevel(level) {
    level = ["LOW", "MODERATE", "HIGH"].includes(level) ? level : "LOW";
    launcher.className = `launcher ${level.toLowerCase()}`;
    $("label").textContent = level;
    currentLevel = level;
  }

  
async function api(path, bodyData) {
  const response = await chrome.runtime.sendMessage({
    type: "jsonApi",
    path,
    body: bodyData
  });

  if (!response || !response.ok) {
    const detail = response?.data?.detail;

    let message = "Request failed.";

    if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail)) {
      message = detail.map(error => {
        const field = Array.isArray(error.loc)
          ? error.loc.join(" → ")
          : "Request";

        return `${field}: ${error.msg || "Invalid value"}`;
      }).join("; ");
    } else if (detail && typeof detail === "object") {
      message = JSON.stringify(detail);
    } else if (response?.error) {
      message = response.error;
    }

    throw new Error(message);
  }

  return response.data;
}


  function pageContentForApprovedAdaptation() {
    const selected = String(window.getSelection?.() || "").trim();

    const text = selected.length >= 40
      ? selected
      : (document.body?.innerText || "");

    return text
      .replace(/\n{3,}/g, "\n\n")
      .slice(0, 8000);
  }

  function behaviorSummary(features) {
    const notes = [];

    if (features.wrong_streak >= 3) {
      notes.push("Several consecutive incorrect attempts");
    } else if (features.error_rate >= 0.4) {
      notes.push("Repeated incorrect attempts");
    }

    if (features.hints_used >= 2) notes.push("Repeated hint use");
    if (features.rereads >= 2) notes.push("Repeated rereading");
    if (features.avg_response_time >= 8000) notes.push("Long response times");
    if (features.active_seconds >= 120) notes.push("Extended time on the page");

    return notes.length
      ? notes.join(", ")
      : "Learner requested assistance";
  }

  // All model-generated explanations require a deliberate learner action.

  let adaptBusy = false;
  let lastExplanation = "";
  const chatHistory = []; // { role: "user" | "assistant", text }

  function remember(role, text) {
    chatHistory.push({ role, text: String(text || "").slice(0, 1500) });
    if (chatHistory.length > 8) chatHistory.shift();
  }

  function sendFeedback(decision, level) {
    return api(`${API}/feedback`, {
      decision,
      strain_level: level,
      page_host: hostName()
    }).catch(() => {});
  }

  async function requestAdaptation(level, summary, features, auto = false) {
    if (adaptBusy) return;

    level = ["LOW", "MODERATE", "HIGH"].includes(level) ? level : currentLevel;

    // Called only from a user click, never by the strain detector.
    ui.open("learning");
    ui.hideConsentNudge?.();

    const content = pageContentForApprovedAdaptation();

    if (!content.trim()) {
      ui.addBot(
        "I couldn't find readable text on this page. Select the part you're stuck on and try again.",
        { error: true }
      );
      return;
    }

    adaptBusy = true;
    ui.setBusy(true);
    status.textContent = "Preparing your explanation with the local model...";
    const typing = ui.addTyping();

    try {
      const result = await api(`${API}/adapt`, {
        approved: true,
        page_title: document.title || "Learning material",
        content,
        behavior_summary: summary,
        strain_level: level,
        features
      });

      typing.remove();

      lastExplanation = result.adaptation || "";
      ui.addBot(
        lastExplanation || "No adapted explanation was returned.",
        { title: auto ? "A SIMPLER WAY TO SEE IT" : "YOUR ADAPTED EXPLANATION" }
      );
      remember("assistant", lastExplanation);

      status.textContent =
        "Adaptation ready. The original webpage has not been changed.";

      sendFeedback("accepted", level);

    } catch (error) {
      typing.remove();
      ui.addBot(`Adaptation failed: ${error.message}`, { error: true });
      status.textContent = `Adaptation failed: ${error.message}`;
    } finally {
      adaptBusy = false;
      ui.setBusy(false);
    }
  }

  async function sendFollowUp(message) {
    message = String(message || "").trim();
    if (!message || adaptBusy) return;

    ui.open("learning");
    ui.addUser(message);
    remember("user", message);

    adaptBusy = true;
    ui.setBusy(true);
    const typing = ui.addTyping();

    try {
      const result = await api(`${API}/chat`, {
        message,
        strain_level: currentLevel,
        page_title: document.title || "Learning material",
        content: pageContentForApprovedAdaptation().slice(0, 4000),
        last_explanation: lastExplanation.slice(0, 1500),
        history: chatHistory.slice(0, -1)
      });

      typing.remove();

      const reply = result.reply || "Sorry, I couldn't come up with a good answer to that.";
      ui.addBot(reply);
      remember("assistant", reply);

      if (/\b(helped|thanks|thank you|got it|makes sense)\b/i.test(message)) {
        sendFeedback("accepted", currentLevel);
      } else if (/\b(confus|still (don'?t|do not)|didn'?t help|not helpful|don'?t get)\b/i.test(message)) {
        sendFeedback("dismissed", currentLevel);
      }

    } catch (error) {
      typing.remove();
      ui.addBot(`Chat unavailable: ${error.message}`, { error: true });
    } finally {
      adaptBusy = false;
      ui.setBusy(false);
    }
  }

  // The two boxes in the Learning tab.
  ui.onSimpler(() =>
    requestAdaptation(
      currentLevel,
      "Learner requested a simpler explanation.",
      buildFeatures()
    )
  );

  ui.onConcept(() =>
    requestAdaptation(
      currentLevel,
      "Learner asked to simplify the core concept: give the key idea in plain language, in short steps, with one short real-world analogy.",
      buildFeatures()
    )
  );

  ui.onSend(sendFollowUp);

  function showNudge(prediction, summary, features) {
    const level = prediction.strain_level || "MODERATE";
    // The bubble lives beside the small strain indicator; no panel is opened.
    state.nudgePending = true;
    ui.setStrain(level, prediction.confidence);
    showConsentBubble(level, () => {
      state.nudgePending = false;
      state.nudgeHandled = true;
      hideConsentBubble();
      sendFeedback("accepted", level);
      // This explicit click is the only route from a nudge to adaptation.
      requestAdaptation(level, summary, features);
    }, () => {
      state.nudgePending = false;
      state.nudgeHandled = true;
      hideConsentBubble();
      sendFeedback("dismissed", level);
    });
  }

  let consentBubble = null;
  function hideConsentBubble() {
    if (consentBubble) consentBubble.remove();
    consentBubble = null;
  }
  function showConsentBubble(level, onApprove, onDismiss) {
    hideConsentBubble();
    const panel = document.createElement("div");
    panel.className = "consent";
    const heading = document.createElement("div");
    heading.className = "consent-heading";
    heading.textContent = level === "HIGH" ? "Need a little help?" : "Want a simpler explanation?";
    const desc = document.createElement("div");
    desc.className = "consent-desc";
    desc.textContent = "Cognio noticed some difficulty. Open an explanation?";
    const actions = document.createElement("div");
    actions.className = "consent-actions";
    const accept = document.createElement("button");
    accept.textContent = "Help me";
    const decline = document.createElement("button");
    decline.textContent = "Not now";
    decline.className = "secondary";
    accept.addEventListener("click", onApprove);
    decline.addEventListener("click", onDismiss);
    actions.append(accept, decline);
    panel.append(heading, desc, actions);
    shadow.append(panel);
    consentBubble = panel;
  }

  async function analyze(force = false) {
    if (state.inFlight) return;

    const features = buildFeatures();

    const enoughSignals =
      features.total_attempts >= 1 ||
      features.hints_used >= 1 ||
      features.rereads >= 2 ||
      features.active_seconds >= 120;

    if (!enoughSignals) {
      status.textContent =
        "Collecting learning signals. Manual adaptation is available anytime.";
      return;
    }

    if (!force && Date.now() - state.lastAnalysisAt < 30000) return;

    state.inFlight = true;
    state.lastAnalysisAt = Date.now();
    status.textContent = "Analysing learning signals...";

    try {
      const result = await api(`${API}/analyze`, {
        student_id: SESSION_ID,
        content_id: `${hostName()}${location.pathname}`.slice(0, 512),
        features
      });

      const prediction = result.prediction || {};
      const level = prediction.strain_level || "LOW";

      setLevel(level);
      ui.setStrain(level, prediction.confidence);

      status.textContent =
        `Latest estimate: ${level} · ${Math.round((prediction.confidence || 0) * 100)}% confidence`;

      const shouldNudge =
        ["HIGH", "MODERATE"].includes(level) &&
        (prediction.trigger_adaptation !== false || level === "HIGH") &&
        (prediction.confidence == null || prediction.confidence >= 0.5);

      if (level === "LOW") {
        hideConsentBubble();
        state.nudgePending = false;
        state.nudgeHandled = false;
        state.lastNudgeLevel = "";
      }
      const cooledDown = !state.nudgePending && !state.nudgeHandled &&
        (level !== state.lastNudgeLevel || Date.now() - state.lastNudgeAt > NUDGE_COOLDOWN_MS);

      if (shouldNudge && cooledDown) {
        state.lastNudgeAt = Date.now();
        state.lastNudgeLevel = level;

        showNudge(
          prediction,
          result.behavior_summary || behaviorSummary(features),
          features
        );
      }

      console.info("Cognio strain analysis", {
        level,
        confidence: prediction.confidence,
        features,
        prediction
      });

    } catch (error) {
      status.textContent = `Strain analysis unavailable: ${error.message}`;
      console.error("Cognio analysis error:", error);
    } finally {
      state.inFlight = false;
      updateSignals();
    }
  }

  analyzeButton.addEventListener("click", () => analyze(true));

  // -------------------------------
  // Submission outcome detection
  // -------------------------------

  function getResultText() {
    const selectors = [
      '[data-e2e-locator="submission-result"]',
      '[data-e2e-locator="submission-result-status"]',
      '[data-cy="submission-result"]',
      '[class*="result"]',
      '[class*="status"]',
      '[role="alert"]'
    ];

    const chunks = [];

    for (const selector of selectors) {
      document.querySelectorAll(selector).forEach(element => {
        if (element.innerText) chunks.push(element.innerText);
      });
    }

    chunks.push((document.body?.innerText || "").slice(-12000));

    return chunks.join("\n").toLowerCase();
  }

  function classifyResult(text) {
    const correct =
      /\baccepted\b|\ball test cases passed\b|\bcorrect answer\b|\ball tests passed\b/.test(text);

    const wrong =
      /\bwrong answer\b|\bincorrect\b|\btest cases? failed\b|\bnot quite\b/.test(text);

    if (correct && !wrong) return true;
    if (wrong && !correct) return false;

    return null;
  }

  function recordOutcome(outcome) {
    if (!state.pendingAttempt) return;

    state.pendingAttempt = false;
    clearTimeout(state.attemptTimer);

    const elapsed = Math.max(250, Date.now() - state.attemptStartedAt);

    state.totalAttempts += 1;
    state.latencies.push(elapsed);

    if (state.latencies.length > 20) state.latencies.shift();
    if (!state.firstLatency) state.firstLatency = elapsed;

    if (outcome === true) {
      state.correctAttempts += 1;
      state.wrongStreak = 0;
    } else if (outcome === false) {
      state.wrongAttempts += 1;
      state.wrongStreak += 1;
    }

    updateSignals();

    console.info("Cognio submission recorded", {
      outcome,
      totalAttempts: state.totalAttempts,
      wrongAttempts: state.wrongAttempts,
      wrongStreak: state.wrongStreak
    });

    analyze(true);
  }

  function checkPendingResult() {
    if (!state.pendingAttempt) return;

    const text = getResultText();

    if (text === state.lastOutcomeText) return;
    state.lastOutcomeText = text;

    const result = classifyResult(text);

    if (result !== null) {
      recordOutcome(result);
    }
  }

  function recordAttemptStart() {
    if (state.pendingAttempt) return;

    state.pendingAttempt = true;
    state.attemptStartedAt = Date.now();
    state.lastOutcomeText = "";

    clearTimeout(state.attemptTimer);

    // Check repeatedly because coding platforms render results asynchronously.
    let checks = 0;

    const poll = () => {
      if (!state.pendingAttempt) return;

      checkPendingResult();
      checks++;

      if (state.pendingAttempt && checks < 12) {
        state.attemptTimer = setTimeout(poll, 1000);
      } else if (state.pendingAttempt) {
        // Record an attempt without inventing its correctness.
        recordOutcome(null);
      }
    };

    state.attemptTimer = setTimeout(poll, 700);
  }

  const hintPattern =
    /\b(hint|clue|show hint|need help|help me)\b/i;

  const attemptPattern =
    /\b(submit|check answer|run code|run tests|verify|test solution|evaluate|execute)\b/i;

  document.addEventListener("click", event => {
    const target = event.target?.closest?.(
      "button,[role='button'],input[type='submit'],a"
    );

    if (!target || host.contains(target)) return;

    const label = [
      target.innerText || "",
      target.getAttribute("aria-label") || "",
      target.value || ""
    ].join(" ").trim();

    if (hintPattern.test(label)) {
      state.hintsUsed++;
      updateSignals();
      analyze(true);
      return;
    }

    if (attemptPattern.test(label)) {
      recordAttemptStart();
      return;
    }

    if (target.tagName === "A" && target.href) {
      state.navClicks++;
    }
  }, true);

  document.addEventListener("submit", event => {
    if (!host.contains(event.target)) recordAttemptStart();
  }, true);

  const observer = new MutationObserver(() => {
    if (state.pendingAttempt) checkPendingResult();
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
    characterData: true
  });

  // -------------------------------
  // Rereading and active time
  // -------------------------------

  window.addEventListener("scroll", () => {
    const y = window.scrollY;

    if (state.maxScrollY > 700 && state.lastScrollY - y > 450) {
      state.rereads++;
      updateSignals();
      analyze(true);
    }

    state.maxScrollY = Math.max(state.maxScrollY, y);
    state.lastScrollY = y;
  }, { passive: true });

  document.addEventListener("visibilitychange", () => {
    const now = Date.now();

    if (document.visibilityState === "hidden") {
      state.activeMs += Math.max(0, now - state.lastActiveAt);
    } else {
      state.lastActiveAt = now;
    }
  });

  window.addEventListener("focus", () => {
    if (document.visibilityState === "visible") {
      state.lastActiveAt = Date.now();
    }
  });

  window.addEventListener("blur", () => {
    if (document.visibilityState === "visible") {
      state.activeMs += Math.max(0, Date.now() - state.lastActiveAt);
      state.lastActiveAt = Date.now();
    }
  });

  setInterval(() => {
    analyze(false);
  }, 30000);

  console.info("Cognio learning signals enabled", {
    host: hostName(),
    session: SESSION_ID
  });
})();