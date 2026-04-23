(function () {
  function ensureOverlay() {
    let div = document.getElementById("cognio-overlay");

    if (!div) {
      div = document.createElement("div");
      div.id = "cognio-overlay";
      div.style.position = "fixed";
      div.style.right = "20px";
      div.style.bottom = "20px";
      div.style.width = "320px";
      div.style.maxWidth = "calc(100vw - 40px)";
      div.style.background = "#111827";
      div.style.color = "#ffffff";
      div.style.padding = "16px";
      div.style.borderRadius = "14px";
      div.style.boxShadow = "0 12px 30px rgba(0,0,0,0.22)";
      div.style.zIndex = "9999";
      div.style.fontFamily = "Arial, sans-serif";
      div.style.display = "none";
      div.style.lineHeight = "1.5";
      document.body.appendChild(div);
    }

    return div;
  }

  window.showOverlay = function (message, meta) {
    const div = ensureOverlay();

    const strain = meta?.strain_level ? `<div style="font-size:12px;opacity:0.8;margin-bottom:6px;">Strain: ${meta.strain_level}</div>` : "";
    const note = meta?.explanation_note ? `<div style="font-size:12px;opacity:0.8;margin-top:8px;">${meta.explanation_note}</div>` : "";

    div.innerHTML = `
      <div style="font-weight:700;margin-bottom:8px;">Cognio Adaptation</div>
      ${strain}
      <div>${message}</div>
      ${note}
    `;
    div.style.display = "block";
  };

  window.hideOverlay = function () {
    const div = document.getElementById("cognio-overlay");
    if (div) div.style.display = "none";
  };
})();