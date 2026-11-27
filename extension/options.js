
const mode = document.getElementById("mode");
const apiBase = document.getElementById("apiBase");
const accessToken = document.getElementById("accessToken");
const status = document.getElementById("status");

const LOCAL_URL = "http://localhost:8000";

function showStatus(message, success = true) {
  status.textContent = message;
  status.style.color = success ? "#4ade80" : "#f87171";
}

function updateMode() {
  if (mode.value === "local") {
    apiBase.value = LOCAL_URL;
    apiBase.readOnly = true;
  } else {
    apiBase.readOnly = false;

    if (apiBase.value === LOCAL_URL) {
      apiBase.value = "";
    }
  }
}

function validateConfig() {
  const url = new URL(apiBase.value.trim());
  const token = accessToken.value.trim();

  const local = url.origin === LOCAL_URL;

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
    throw new Error("Enter a valid Cognio backend URL.");
  }

  if (!token) {
    throw new Error("Enter your beta access token.");
  }

  return {
    apiBase: url.origin,
    accessToken: token
  };
}

async function loadSettings() {
  await chrome.storage.local.setAccessLevel({
    accessLevel: "TRUSTED_CONTEXTS"
  });

  const config = await chrome.storage.local.get({
    apiBase: LOCAL_URL,
    accessToken: ""
  });

  apiBase.value = config.apiBase;
  accessToken.value = config.accessToken;

  mode.value =
    config.apiBase === LOCAL_URL ? "local" : "remote";

  updateMode();
}

mode.addEventListener("change", updateMode);

document.getElementById("save")
  .addEventListener("click", async () => {
    try {
      const config = validateConfig();

      await chrome.storage.local.set(config);

      showStatus("Settings saved successfully.");
    } catch (error) {
      showStatus(error.message, false);
    }
  });

document.getElementById("test")
  .addEventListener("click", async () => {
    try {
      const config = validateConfig();

      showStatus("Testing backend connection...");

      const response = await fetch(
        config.apiBase + "/health",
        {
          redirect: "error",
          signal: AbortSignal.timeout(15000)
        }
      );

      if (!response.ok) {
        throw new Error("Backend is unavailable.");
      }

      const data = await response.json();

      if (data.status !== "ok") {
        throw new Error("Unexpected backend response.");
      }

      const authResponse = await fetch(
        config.apiBase + "/api/v1/learning/analyze",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Cognio-Token": config.accessToken
          },
          body: "{}",
          redirect: "error",
          signal: AbortSignal.timeout(15000)
        }
      );

      if (authResponse.status === 401) {
        throw new Error("Invalid beta access token.");
      }

      if (
        authResponse.status !== 422 &&
        !authResponse.ok
      ) {
        throw new Error(
          "API test returned HTTP " + authResponse.status
        );
      }

      showStatus("Backend reachable. Access token accepted.");

    } catch (error) {
      showStatus(error.message, false);
    }
  });

loadSettings().catch(error => {
  showStatus(error.message, false);
});
