(function () {
  function getPanel() {
    return document.getElementById("adaptive-output");
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatMultilineText(text) {
    return escapeHtml(text).replace(/\n/g, "<br><br>");
  }

  window.showOverlay = function (message, meta) {
    const panel = getPanel();
    if (!panel) return;

    const strain = String(meta?.strain_level || "LOW");
    const explanation = meta?.explanation_note || "";
    const behavior = meta?.behavior_summary || "";
    const confidence =
      meta?.confidence !== undefined && meta?.confidence !== null && meta?.confidence !== ""
        ? `${Math.round(Number(meta.confidence) * 100)}%`
        : "";

    panel.innerHTML = `
      <div class="adapt-badge adapt-${strain}">${escapeHtml(strain)} STRAIN</div>
      <h3 class="adapt-title">Cognio Learning Companion</h3>
      <div class="adapt-text">${formatMultilineText(message || "No adaptation text returned.")}</div>
      <div class="adapt-meta">
        <div><strong>Why this changed:</strong> ${escapeHtml(explanation)}</div>
        <div><strong>Observed behavior:</strong> ${escapeHtml(behavior)}</div>
        ${confidence ? `<div><strong>Model confidence:</strong> ${escapeHtml(confidence)}</div>` : ""}
      </div>
    `;
  };

  window.clearOverlay = function () {
    const panel = getPanel();
    if (!panel) return;

    panel.innerHTML = `
      <div class="companion-empty">
        <div class="companion-icon">✦</div>
        <p>Interact with the lesson and Cognio will adapt the explanation to your learning pattern in real time.</p>
      </div>
    `;
  };
})();