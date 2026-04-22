// frontend/tracker.js

let attempts = 0;
let hintsUsed = 0;
let startTime = Date.now();
let buffer = [];

const BASE_URL = "http://127.0.0.1:8001";

// -------- SEND TO BACKEND (EVENTS ENDPOINT) -------- //
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
        events: events   // batch of events
      })
    });

    const data = await response.json();

    console.log("EVENT RESPONSE:", data);

    // If adapt response is forwarded, show overlay
    if (data && data.adaptation && window.showOverlay) {
      window.showOverlay(data.adaptation);
    }

  } catch (error) {
    console.error("Error sending event batch:", error);
  }
}

// -------- BUFFER LOGIC -------- //
function pushToBuffer(features) {
  buffer.push({
    timestamp: Date.now(),
    features: features
  });
}

// -------- SEND EVERY 30 SECONDS -------- //
setInterval(() => {
  if (buffer.length > 0) {
    sendEventBatch(buffer);
    buffer = [];
  }
}, 30000); // ✅ 30 seconds (PRD requirement)


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