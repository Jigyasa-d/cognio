function showOverlay(message) {
    let div = document.getElementById("cognio-overlay");

    if (!div) {
        div = document.createElement("div");
        div.id = "cognio-overlay";
        div.style.position = "fixed";
        div.style.bottom = "20px";
        div.style.right = "20px";
        div.style.background = "#000";
        div.style.color = "#fff";
        div.style.padding = "10px";
        div.style.borderRadius = "8px";
        document.body.appendChild(div);
    }

    div.innerText = message;
}