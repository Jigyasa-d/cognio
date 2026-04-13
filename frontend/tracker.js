// frontend/tracker.js

let attempts = 0;
let hintsUsed = 0;
let startTime = Date.now();

function sendEvent(features) {
  console.log("TRACKED FEATURES:", features);
}

// simulate answer submission
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

  sendEvent(features);

  startTime = Date.now(); // reset timer
};

// simulate hint usage
window.useHint = function () {
  hintsUsed++;
  console.log("Hint used:", hintsUsed);
};