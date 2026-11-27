// Cognio Chrome Extension background service worker

const API_BASE = "http://localhost:8000";

// Open/close Cognio from the Chrome toolbar.
chrome.action.onClicked.addListener(tab => {
  if (tab.id) {
    chrome.tabs.sendMessage(tab.id, { type: "toggle" }).catch(() => {});
  }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

  // Capture visible webpage.
  if (msg.type === "capture") {
    chrome.tabs.captureVisibleTab(
      sender.tab.windowId,
      { format: "png" }
    )
      .then(dataUrl => sendResponse({ ok: true, dataUrl }))
      .catch(err => sendResponse({
        ok: false,
        error: String(err?.message || err)
      }));

    return true;
  }

  // Existing Solver and Quiz image APIs.
  if (msg.type === "api") {
    callImageApi(msg).then(sendResponse);
    return true;
  }

  // New Cognio learning JSON APIs.
  if (msg.type === "jsonApi") {
    callJsonApi(msg).then(sendResponse);
    return true;
  }
});


// Keep the worker alive during long local vision requests.
async function callImageApi({
  path,
  dataUrl,
  fileName,
  question,
  pageText
}) {
  const keepAlive = setInterval(() => {
    chrome.runtime.getPlatformInfo(() => {});
  }, 20000);

  try {
    const allowedPaths = [
      "/api/v1/visual/solve",
      "/api/v1/visual-quiz/generate"
    ];

    if (!allowedPaths.includes(path)) {
      throw new Error("Unsupported image API endpoint.");
    }

    const blob = await (await fetch(dataUrl)).blob();

    const form = new FormData();

    form.append("file", blob, fileName || "image.jpg");

    if (typeof question === "string") {
      form.append("question", question);
    }
    if (path === "/api/v1/visual/solve" && typeof pageText === "string") {
      form.append("page_text", pageText.slice(0, 9000));
    }

    const response = await fetch(API_BASE + path, {
      method: "POST",
      body: form
    });

    let data = {};

    try {
      data = await response.json();
    } catch (_) {}

    return {
      ok: response.ok,
      status: response.status,
      data
    };

  } catch (error) {
    console.error("Cognio image API error:", error);

    return {
      ok: false,
      status: 0,
      data: {
        detail: error.message ||
          "Cannot reach Cognio backend. Is Docker running?"
      }
    };

  } finally {
    clearInterval(keepAlive);
  }
}


// JSON communication for behavioural analysis and adaptation.
async function callJsonApi({ path, body }) {
  const keepAlive = setInterval(() => {
    chrome.runtime.getPlatformInfo(() => {});
  }, 20000);

  try {
    const allowedPaths = [
      "/api/v1/learning/analyze",
      "/api/v1/learning/adapt",
      "/api/v1/learning/feedback",
      "/api/v1/learning/chat"
    ];

    if (!allowedPaths.includes(path)) {
      throw new Error("Unsupported Cognio learning endpoint.");
    }

    if (!body || typeof body !== "object") {
      throw new Error("Invalid JSON request body.");
    }

    const response = await fetch(API_BASE + path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body)
    });

    let data = {};

    try {
      data = await response.json();
    } catch (_) {}

    if (!response.ok) {
      console.error("Cognio learning API error:", response.status, data);
    }

    return {
      ok: response.ok,
      status: response.status,
      data
    };

  } catch (error) {
    console.error("Cognio JSON API error:", error);

    return {
      ok: false,
      status: 0,
      error: error.message,
      data: {
        detail: error.message ||
          "Cannot connect to Cognio learning backend."
      }
    };

  } finally {
    clearInterval(keepAlive);
  }
}