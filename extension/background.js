
// Cognio Chrome Extension background service worker

const DEFAULT_API_BASE = "http://localhost:8000";

chrome.storage.local.setAccessLevel({
  accessLevel: "TRUSTED_CONTEXTS"
}).catch(console.error);

async function getConfig() {
  const config = await chrome.storage.local.get({
    apiBase: DEFAULT_API_BASE,
    accessToken: ""
  });

  const url = new URL(config.apiBase);

  const local =
    url.origin === "http://localhost:8000";

  const remote =
    url.protocol === "https:" &&
    url.hostname.endsWith(".trycloudflare.com") &&
    !url.port;

  if (
    (!local && !remote) ||
    url.username ||
    url.password ||
    url.pathname !== "/" ||
    url.search ||
    url.hash
  ) {
    throw new Error("Invalid Cognio backend URL.");
  }

  if (!config.accessToken.trim()) {
    throw new Error(
      "Open Cognio extension settings and enter your access token."
    );
  }

  return {
    apiBase: url.origin,
    accessToken: config.accessToken.trim()
  };
}

// Open/close Cognio from the Chrome toolbar.
chrome.action.onClicked.addListener(tab => {
  if (tab.id) {
    chrome.tabs.sendMessage(tab.id, {
      type: "toggle"
    }).catch(() => {});
  }
});

chrome.runtime.onMessage.addListener(
  (msg, sender, sendResponse) => {

    if (sender.id !== chrome.runtime.id) {
      return false;
    }

    if (msg.type === "capture") {
      chrome.tabs.captureVisibleTab(
        sender.tab.windowId,
        { format: "png" }
      )
        .then(dataUrl => sendResponse({
          ok: true,
          dataUrl
        }))
        .catch(err => sendResponse({
          ok: false,
          error: String(err?.message || err)
        }));

      return true;
    }

    if (msg.type === "api") {
      callImageApi(msg).then(sendResponse);
      return true;
    }

    if (msg.type === "jsonApi") {
      callJsonApi(msg).then(sendResponse);
      return true;
    }
  }
);

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

    const config = await getConfig();

    if (
      typeof dataUrl !== "string" ||
      !/^data:image\/(png|jpeg|webp);base64,/i.test(dataUrl)
    ) {
      throw new Error("Invalid image data.");
    }

    const blob = await (await fetch(dataUrl)).blob();

    if (blob.size > 10 * 1024 * 1024) {
      throw new Error("Image must be 10 MB or smaller.");
    }

    const form = new FormData();

    form.append("file", blob, fileName || "image.png");

    if (typeof question === "string") {
      form.append("question", question);
    }

    if (
      path === "/api/v1/visual/solve" &&
      typeof pageText === "string"
    ) {
      form.append("page_text", pageText.slice(0, 9000));
    }

    const response = await fetch(config.apiBase + path, {
      method: "POST",
      headers: {
        "X-Cognio-Token": config.accessToken
      },
      redirect: "error",
      body: form
    });

    let data = {};

    try {
      data = await response.json();
    } catch (_) {
      data = {
        detail: "Backend returned an invalid response."
      };
    }

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
          "Cannot reach Cognio backend."
      }
    };

  } finally {
    clearInterval(keepAlive);
  }
}

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

    const config = await getConfig();

    const response = await fetch(config.apiBase + path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Cognio-Token": config.accessToken
      },
      redirect: "error",
      body: JSON.stringify(body)
    });

    let data = {};

    try {
      data = await response.json();
    } catch (_) {
      data = {
        detail: "Backend returned an invalid response."
      };
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
