function showOverlay(message) {
    let div = document.getElementById("cognio-overlay");

    if (!div) {
        div = document.createElement("div");
        div.id = "cognio-overlay";
        div.style.position = "fixed";
        div.style.bottom = "20px";
        div.style.right = "20px";
        div.style.maxWidth = "360px";
        div.style.background = "#111827";
        div.style.color = "#ffffff";
        div.style.padding = "14px";
        div.style.borderRadius = "12px";
        div.style.boxShadow = "0 10px 25px rgba(0,0,0,0.25)";
        div.style.zIndex = "99999";
        div.style.fontFamily = "Arial, sans-serif";
        div.style.fontSize = "14px";
        div.style.lineHeight = "1.5";
        document.body.appendChild(div);
    }

    div.innerText = message;
}