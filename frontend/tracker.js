const BASE_URL = "http://localhost:8000";

let totalAttempts = 0;
let wrongAttempts = 0;
let wrongStreak = 0;
let hintsUsed = 0;
let rereads = 0;
let questionStart = Date.now();
let latencies = [];

function logToScreen(message) {
  const log = document.getElementById("demo-log");
  if (!log) return;

  const line = document.createElement("div");
  line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  log.prepend(line);
}

function avg(values) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function buildFeatures() {
  const averageLatency = avg(latencies);

  return {
    latency_delta: Number(averageLatency.toFixed(2)),
    error_rate: totalAttempts === 0 ? 0 : Number((wrongAttempts / totalAttempts).toFixed(2)),
    attempt_burst: wrongStreak >= 3 ? 1 : 0,
    attention_drop: wrongStreak >= 2 ? 1 : 0,
    hint_reliance: totalAttempts === 0 ? 0 : Number((hintsUsed / totalAttempts).toFixed(2)),
    cold_start_latency: latencies[0] || averageLatency || 0,
    exit_flag_ratio: 0,
    reread_normalized: Number((rereads / Math.max(totalAttempts, 1)).toFixed(2))
  };
}

async function sendLiveEvent() {
  const payload = {
    student_id: "STU_DEMO",
    content_id: "UNIT_DEMO",
    features: buildFeatures()
  };

  logToScreen("Sending live event to backend...");
  console.log("REQUEST PAYLOAD:", payload);

  try {
    const response = await fetch(`${BASE_URL}/api/v1/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    console.log("BACKEND RESPONSE:", data);

    const adapt = data?.adapt;
    const adaptationText = adapt?.adaptation;
    const strainLevel = adapt?.prediction?.strain_level;
    const explanationNote = adapt?.explanation_note;

    if (adaptationText && window.showOverlay) {
      window.showOverlay(adaptationText, {
        strain_level: strainLevel,
        explanation_note: explanationNote
      });
      logToScreen(`Adaptation received. Strain=${strainLevel}`);
    } else {
      logToScreen("No adaptation returned.");
    }

    const raw = document.getElementById("raw-response");
    if (raw) {
      raw.textContent = JSON.stringify(data, null, 2);
    }
  } catch (error) {
    console.error("SEND ERROR:", error);
    logToScreen(`Error: ${error.message}`);
  }
}

function registerAttempt(isCorrect) {
  const now = Date.now();
  const responseTime = now - questionStart;
  latencies.push(responseTime);

  totalAttempts += 1;

  if (isCorrect) {
    wrongStreak = 0;
    logToScreen(`Correct answer submitted. Response time=${responseTime}ms`);
  } else {
    wrongAttempts += 1;
    wrongStreak += 1;
    logToScreen(`Wrong answer submitted. Wrong streak=${wrongStreak}, response time=${responseTime}ms`);
  }

  questionStart = Date.now();

  if (wrongStreak >= 3) {
    sendLiveEvent();
  }
}

window.submitWrongAnswer = function () {
  registerAttempt(false);
};

window.submitCorrectAnswer = function () {
  registerAttempt(true);
};

window.useHint = function () {
  hintsUsed += 1;
  logToScreen(`Hint used. Total hints=${hintsUsed}`);
};

window.rereadContent = function () {
  rereads += 1;
  logToScreen(`Student reread the content. Total rereads=${rereads}`);
};

window.resetDemo = function () {
  totalAttempts = 0;
  wrongAttempts = 0;
  wrongStreak = 0;
  hintsUsed = 0;
  rereads = 0;
  questionStart = Date.now();
  latencies = [];

  if (window.hideOverlay) window.hideOverlay();

  const raw = document.getElementById("raw-response");
  if (raw) raw.textContent = "";

  const log = document.getElementById("demo-log");
  if (log) log.innerHTML = "";

  logToScreen("Demo reset.");
};