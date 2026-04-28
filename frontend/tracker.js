const BASE_URL = "http://localhost:8000";

let totalAttempts = 0;
let wrongAttempts = 0;
let correctAttempts = 0;
let wrongStreak = 0;
let hintsUsed = 0;
let rereads = 0;
let questionStart = Date.now();
let latencies = [];
let lastTriggeredState = null;
let requestInFlight = false;

function avg(arr) {
  if (!arr.length) return 0;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function updateMetric(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function logToScreen(message, type = "") {
  const log = document.getElementById("demo-log");
  if (!log) return;
  const line = document.createElement("div");
  line.className = `log-entry new ${type}`;
  line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  log.prepend(line);
  setTimeout(() => line.classList.remove("new"), 1500);
}

function buildFeatures() {
  const averageLatency = avg(latencies);

  return {
    latency_delta: Number((latencies.at(-1) || 0).toFixed(2)),
    error_rate: totalAttempts === 0 ? 0 : Number((wrongAttempts / totalAttempts).toFixed(2)),
    attempt_burst: wrongStreak >= 3 ? 1 : 0,
    attention_drop: averageLatency >= 5000 ? 1 : 0,
    hint_reliance: totalAttempts === 0 ? 0 : Number((hintsUsed / totalAttempts).toFixed(2)),
    cold_start_latency: latencies[0] || 0,
    exit_flag_ratio: 0,
    reread_normalized: totalAttempts === 0 ? 0 : Number((rereads / totalAttempts).toFixed(2)),
    wrong_streak: wrongStreak,
    total_attempts: totalAttempts,
    hints_used: hintsUsed,
    rereads: rereads,
    avg_response_time: Number(averageLatency.toFixed(2)),
    correct_attempts: correctAttempts
  };
}

function guessStrain(features) {
  if (features.wrong_streak >= 3) return "HIGH";

  let moderateSignals = 0;
  if (features.hints_used >= 2 || features.hint_reliance >= 0.5) moderateSignals += 1;
  if (features.rereads >= 2 || features.reread_normalized >= 0.5) moderateSignals += 1;
  if (features.avg_response_time >= 5000) moderateSignals += 1;
  if (features.error_rate >= 0.4) moderateSignals += 1;

  if (moderateSignals >= 2) return "MODERATE";

  return "LOW";
}

function getBehaviorSummary(features, strain) {
  if (strain === "HIGH") {
    return "The learner is making repeated mistakes in quick succession and appears stuck on the current concept.";
  }
  if (strain === "MODERATE") {
    return "The learner shows partial confusion through hints, rereads, or slower response behavior.";
  }
  return "The learner is progressing steadily and may benefit from a slightly deeper explanation.";
}

function updateDashboard() {
  const features = buildFeatures();
  const guessed = guessStrain(features);

  updateMetric("metric-attempts", totalAttempts);
  updateMetric("metric-wrongstreak", wrongStreak);
  updateMetric("metric-hints", hintsUsed);
  updateMetric("metric-rereads", rereads);
  updateMetric("metric-avgtime", `${Math.round(features.avg_response_time)} ms`);

  const strainEl = document.getElementById("metric-strain");
  if (strainEl) {
    strainEl.textContent = guessed;
    strainEl.className = `metric-value strain-${guessed}`;
  }

  const mcStreak = document.getElementById("mc-streak");
  const mcHints = document.getElementById("mc-hints");
  const mcRereads = document.getElementById("mc-rereads");

  if (mcStreak) mcStreak.className = `metric-card ${wrongStreak >= 3 ? "active-high" : ""}`;
  if (mcHints) mcHints.className = `metric-card ${hintsUsed >= 2 ? "active-moderate" : ""}`;
  if (mcRereads) mcRereads.className = `metric-card ${rereads >= 2 ? "active-moderate" : ""}`;
}

function normalizeAdaptation(adaptation) {
  if (!adaptation) return null;

  if (typeof adaptation === "string") {
    return adaptation;
  }

  if (typeof adaptation === "object") {
    const parts = [];

    if (adaptation.headline) parts.push(adaptation.headline);
    if (adaptation.explanation) parts.push(adaptation.explanation);
    if (adaptation.analogy) parts.push(`Analogy: ${adaptation.analogy}`);
    if (Array.isArray(adaptation.steps) && adaptation.steps.length) {
      parts.push(adaptation.steps.join(" "));
    }
    if (adaptation.visual_hint) parts.push(adaptation.visual_hint);

    const joined = parts.join("\n\n").trim();
    return joined || null;
  }

  return String(adaptation);
}

function showLoading() {
  const panel = document.getElementById("adaptive-output");
  if (!panel) return;

  panel.innerHTML = `
    <div class="companion-empty">
      <div class="companion-icon">✦</div>
      <p>Analysing your learning pattern…</p>
    </div>`;
}

async function sendAdaptiveEvent(triggerReason) {
  if (requestInFlight) return;
  requestInFlight = true;

  const features = buildFeatures();

  const HINT_SUMMARIES = {
    "HINT_REQUESTED": "The learner clicked the Hint button. Provide a direct, concrete hint for Two Sum. Nudge them toward using a hash map to store seen numbers. Do NOT give the full solution — just the next step.",
    "HIGH":    "The learner is stuck with multiple wrong answers. Give a clear, simple hint to get unstuck.",
    "MODERATE":"The learner is struggling. Give a supportive hint pointing toward the hash map approach.",
    "LOW":     "The learner is doing well. Offer a brief tip about optimizing their approach."
  };

  const behaviorSummary = HINT_SUMMARIES[triggerReason] || getBehaviorSummary(features, triggerReason);

  const payload = {
    student_id: "STU_DEMO",
    content_id: "UNIT_DEMO",
    features,
    behavior_summary: behaviorSummary,
    disable_cache: true
  };

  logToScreen("Sending adaptive event to backend...");
  showLoading();

  try {
    const response = await fetch(`${BASE_URL}/api/v1/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const text = await response.text();
    let data = {};

    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      throw new Error(`Backend returned non-JSON response: ${text}`);
    }

    if (!response.ok) {
      throw new Error(data?.detail || `HTTP ${response.status}`);
    }

    const adapt = data?.adapt;
    const backendStrain = adapt?.prediction?.strain_level || "UNKNOWN";
    const adaptationText = normalizeAdaptation(adapt?.adaptation);

    const raw = document.getElementById("raw-response");
    if (raw) raw.textContent = JSON.stringify(data, null, 2);

    if (adaptationText && window.showOverlay) {
      window.showOverlay(adaptationText, {
        strain_level: backendStrain,
        explanation_note: adapt?.explanation_note || "",
        behavior_summary: adapt?.behavior_summary || behaviorSummary,
        confidence: adapt?.prediction?.confidence || ""
      });

      logToScreen(
        `Adaptation received — ${backendStrain} strain, ${Math.round((adapt?.prediction?.confidence || 0) * 100)}% confidence`,
        "success"
      );
    } else {
      logToScreen("No adaptation text returned", "error");
      if (window.showOverlay) {
        window.showOverlay("No adaptation text returned from backend.", {
          strain_level: backendStrain,
          explanation_note: adapt?.explanation_note || "",
          behavior_summary: adapt?.behavior_summary || behaviorSummary,
          confidence: adapt?.prediction?.confidence || ""
        });
      }
    }
  } catch (error) {
    console.error(error);
    logToScreen(`Error: ${error.message}`, "error");
    if (window.showOverlay) {
      window.showOverlay("The adaptation request failed.", {
        strain_level: "UNKNOWN",
        explanation_note: "Backend request failed.",
        behavior_summary: "",
        confidence: ""
      });
    }
  } finally {
    requestInFlight = false;
  }
}

function maybeTriggerAdaptation(lastActionWasCorrect) {
  const features = buildFeatures();
  const guessed = guessStrain(features);

  if (guessed === "HIGH" && lastTriggeredState !== "HIGH") {
    lastTriggeredState = "HIGH";
    sendAdaptiveEvent("HIGH");
    return;
  }

  if (guessed === "MODERATE" && lastTriggeredState !== "MODERATE") {
    lastTriggeredState = "MODERATE";
    sendAdaptiveEvent("MODERATE");
    return;
  }

  const stableLow =
    guessed === "LOW" &&
    wrongAttempts === 0 &&
    wrongStreak === 0 &&
    correctAttempts >= 2 &&
    hintsUsed === 0 &&
    rereads === 0 &&
    lastActionWasCorrect &&
    lastTriggeredState === null;

  if (stableLow) {
    lastTriggeredState = "LOW";
    sendAdaptiveEvent("LOW");
  }
}

function registerAttempt(isCorrect) {
  const now = Date.now();
  const responseTime = now - questionStart;
  latencies.push(responseTime);
  totalAttempts += 1;

  if (isCorrect) {
    correctAttempts += 1;
    wrongStreak = 0;
    logToScreen(`✓ Correct — ${responseTime}ms`, "success");
  } else {
    wrongAttempts += 1;
    wrongStreak += 1;
    logToScreen(`✗ Wrong — streak=${wrongStreak}, ${responseTime}ms`, "error");
  }

  questionStart = Date.now();
  updateDashboard();
  maybeTriggerAdaptation(isCorrect);
}

async function useHintAction() {
  hintsUsed += 1;
  logToScreen(`💡 Hint used — total=${hintsUsed}`);
  updateDashboard();

  if (requestInFlight) return;

  // Switch to Adaptive Output tab immediately
  const adaptTab = document.getElementById('btab-adapt');
  if (adaptTab) adaptTab.click();

  const features = buildFeatures();
  const payload = {
    student_id: "STU_DEMO",
    content_id: "UNIT_DEMO",
    features,
    behavior_summary: "The learner explicitly clicked the hint button. Give a direct, concrete hint for the Two Sum problem. Guide them toward the hash map approach without revealing the full solution.",
    disable_cache: true
  };

  logToScreen("Sending hint request...");
  showLoading();
  requestInFlight = true;

  try {
    const response = await fetch(`${BASE_URL}/api/v1/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const text = await response.text();
    let data = {};
    try { data = text ? JSON.parse(text) : {}; } catch { throw new Error("Non-JSON: " + text); }
    if (!response.ok) throw new Error(data?.detail || `HTTP ${response.status}`);

    const adapt = data?.adapt;
    const strainLevel = adapt?.prediction?.strain_level || "LOW";
    const adaptationText = normalizeAdaptation(adapt?.adaptation);

    if (adaptationText && window.showOverlay) {
      window.showOverlay(adaptationText, {
        strain_level: strainLevel,
        explanation_note: adapt?.explanation_note || "",
        behavior_summary: adapt?.behavior_summary || "",
        confidence: adapt?.prediction?.confidence || ""
      });
      logToScreen(`💡 Hint received (${strainLevel} strain)`, "success");
    } else {
      logToScreen("No hint text returned", "error");
      if (window.showOverlay) window.showOverlay("No hint returned from backend.", { strain_level: strainLevel });
    }
  } catch (error) {
    console.error(error);
    logToScreen(`Hint error: ${error.message}`, "error");
    if (window.showOverlay) window.showOverlay("Hint request failed: " + error.message, { strain_level: "UNKNOWN" });
  } finally {
    requestInFlight = false;
  }
}

function rereadContentAction() {
  rereads += 1;
  logToScreen(`↩ Reread — total=${rereads}`);
  updateDashboard();
  maybeTriggerAdaptation(false);
}

function resetDemoAction() {
  totalAttempts = 0;
  wrongAttempts = 0;
  correctAttempts = 0;
  wrongStreak = 0;
  hintsUsed = 0;
  rereads = 0;
  questionStart = Date.now();
  latencies = [];
  lastTriggeredState = null;
  requestInFlight = false;

  const log = document.getElementById("demo-log");
  if (log) log.innerHTML = '<div class="log-entry">Waiting for interactions…</div>';

  const raw = document.getElementById("raw-response");
  if (raw) raw.textContent = "";

  if (window.clearOverlay) window.clearOverlay();

  updateDashboard();
}

window.addEventListener("load", () => {
  updateDashboard();
  if (window.clearOverlay) window.clearOverlay();

  const btnWrong = document.getElementById("btn-wrong");
  const btnCorrect = document.getElementById("btn-correct");
  const btnHint = document.getElementById("btn-hint");
  const btnReread = document.getElementById("btn-reread");
  const btnReset = document.getElementById("btn-reset");

  if (btnWrong) btnWrong.addEventListener("click", () => registerAttempt(false));
  if (btnCorrect) btnCorrect.addEventListener("click", () => registerAttempt(true));
  if (btnHint) btnHint.addEventListener("click", useHintAction);
  if (btnReread) btnReread.addEventListener("click", rereadContentAction);
  if (btnReset) btnReset.addEventListener("click", resetDemoAction);

  console.log("Cognio tracker loaded successfully");
});