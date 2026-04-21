// frontend/tracker.js

let attempts = 0;
let hintsUsed = 0;
let startTime = Date.now();
let buffer = [];

// -------- SEND TO BACKEND -------- //
async function sendEventBatch(features) {
  try {
    const response = await fetch("http://127.0.0.1:8001/api/v1/adapt", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        student_id: "STU_DEMO",
        content_id: "UNIT_DEMO",
        features: features
      })
    });

    const data = await response.json();

    console.log("ADAPT RESPONSE:", data);

    // show overlay if available
    if (window.showOverlay) {
      window.showOverlay(data.adaptation);
    }

  } catch (error) {
    console.error("Error sending event:", error);
  }
}

// -------- BUFFER LOGIC -------- //
function pushToBuffer(features) {
  buffer.push(features);
}

// send latest event every 5 sec
setInterval(() => {
  if (buffer.length > 0) {
    const latest = buffer[buffer.length - 1];
    sendEventBatch(latest);
    buffer = [];
  }
}, 5000);

// -------- SIMULATE ANSWER -------- //
window.submitAnswer = function () {
  const endTime = Date.now();
  const responseTime = endTime - startTime;

  attempts++;

  const features = {
    latency_delta: responseTime,
    error_rate: attempts > 0 ? 1 / attempts : 0,
    attempt_burst: attempts > 2 ? 1 : 0,
    attention_drop: 0,
    hint_reliance: hintsUsed / (attempts || 1),
    cold_start_latency: 3000,
    exit_flag_ratio: 0,
    reread_normalized: 1
  };

  console.log("TRACKED FEATURES:", features);

  pushToBuffer(features);

  startTime = Date.now();
};

// -------- SIMULATE HINT -------- //
window.useHint = function () {
  hintsUsed++;
  console.log("Hint used:", hintsUsed);
};