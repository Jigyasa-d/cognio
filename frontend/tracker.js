let attempts = 0;
let wrongStreak = 0;
let hintsUsed = 0;
let startTime = Date.now();
let buffer = [];

const BASE_URL = "http://127.0.0.1:8000";

async function sendEventBatch(events) {
  try {
    const response = await fetch(`${BASE_URL}/api/v1/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        student_id: "STU_DEMO",
        content_id: "UNIT_DEMO",
        events: events
      })
    });

    const data = await response.json();
    console.log("EVENT RESPONSE:", data);

    if (data && data.adapt && data.adapt.adaptation && window.showOverlay) {
      window.showOverlay(data.adapt.adaptation);
    }
  } catch (error) {
    console.error("Error sending event batch:", error);
  }
}

function pushToBuffer(features) {
  buffer.push({
    timestamp: Date.now(),
    features: features
  });
}

setInterval(() => {
  if (buffer.length > 0) {
    sendEventBatch(buffer);
    buffer = [];
  }
}, 30000);

window.submitWrongAnswer = function () {
  const endTime = Date.now();
  const responseTime = endTime - startTime;

  attempts += 1;
  wrongStreak += 1;

  const features = {
    latency_delta: responseTime,
    error_rate: 1.0,
    attempt_burst: wrongStreak,
    attention_drop: wrongStreak >= 2 ? 0.7 : 0.2,
    hint_reliance: hintsUsed / (attempts || 1),
    cold_start_latency: 3000,
    exit_flag_ratio: 0.0,
    reread_normalized: 1.0
  };

  console.log("WRONG ANSWER FEATURES:", features);
  pushToBuffer(features);
  startTime = Date.now();
};

window.submitCorrectAnswer = function () {
  const endTime = Date.now();
  const responseTime = endTime - startTime;

  attempts += 1;
  wrongStreak = 0;

  const features = {
    latency_delta: responseTime,
    error_rate: 0.0,
    attempt_burst: 0,
    attention_drop: 0.1,
    hint_reliance: hintsUsed / (attempts || 1),
    cold_start_latency: 3000,
    exit_flag_ratio: 0.0,
    reread_normalized: 1.0
  };

  console.log("CORRECT ANSWER FEATURES:", features);
  pushToBuffer(features);
  startTime = Date.now();
};

window.useHint = function () {
  hintsUsed++;
  console.log("Hint used:", hintsUsed);
};

window.simulateStruggle = function () {
  window.submitWrongAnswer();
  window.submitWrongAnswer();
  window.submitWrongAnswer();
  console.log("Simulated 3 wrong attempts");
};