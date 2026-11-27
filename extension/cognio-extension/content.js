(() => {
  if (window.__cognioLoaded) return;
  window.__cognioLoaded = true;

  const CSS = `
  :host{all:initial}
  *{box-sizing:border-box;margin:0;padding:0;font-family:Inter,-apple-system,"Segoe UI",sans-serif}
  .widget{display:flex;flex-direction:column;align-items:flex-end;color:#eef0f6;font-size:13px}
  button{font-family:inherit}

  /* launcher */
  .fab{width:56px;height:56px;border:0;border-radius:50%;background:linear-gradient(135deg,#ffb23e,#ff7a1a);box-shadow:0 8px 24px #ff7a1a55,0 4px 12px #0008;display:grid;place-items:center;cursor:pointer;transition:transform .2s ease,box-shadow .2s ease}
  .fab:hover{transform:scale(1.08) rotate(-5deg);box-shadow:0 10px 30px #ff7a1a88,0 4px 12px #0008}

  /* window */
  .chat{display:none;flex-direction:column;width:392px;height:min(650px,84vh);background:linear-gradient(180deg,#2b2b30,#222226);border:1px solid #3a3a41;border-radius:18px;overflow:hidden;box-shadow:0 24px 60px #000b,0 0 0 1px #ffffff0a inset;margin-bottom:12px;transform-origin:bottom right}
  .chat.open{display:flex;animation:pop .24s cubic-bezier(.2,.9,.3,1.15)}
  @keyframes pop{from{opacity:0;transform:translateY(16px) scale(.94)}to{opacity:1;transform:none}}
  @keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
  @keyframes bounce{0%,80%,100%{transform:translateY(0);opacity:.4}40%{transform:translateY(-5px);opacity:1}}
  @keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}

  .header{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;background:linear-gradient(135deg,#3b3b44,#2c2c33);border-bottom:1px solid #3a3a41;flex-shrink:0}
  .hl{display:flex;align-items:center;gap:10px}
  .hr{display:flex;align-items:center;gap:8px}
  .avatar{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#ffb23e,#ff7a1a);display:grid;place-items:center;color:#1a1a1a;font-weight:800;box-shadow:0 0 0 3px #ffa11630}
  .title{font-size:14px;font-weight:750}.sub{font-size:11px;color:#a9a9b4}
  .close{border:0;background:#ffffff0d;color:#b5b5bf;width:26px;height:26px;border-radius:8px;cursor:pointer;font-size:12px;transition:background .15s}
  .close:hover{background:#ffffff1f;color:#fff}
  .schip{display:flex;align-items:center;gap:6px;font-size:10px;font-weight:750;padding:4px 10px;border-radius:20px;background:#1e4939;color:#a4f1cf;transition:all .3s}
  .schip i{width:7px;height:7px;border-radius:50%;background:currentColor;animation:blink 2s infinite}
  .schip.MODERATE{background:#59431e;color:#ffd58a}.schip.HIGH{background:#5b2929;color:#ffb4b4}

  /* sliding tabs */
  .tabs{position:relative;display:grid;grid-template-columns:repeat(3,1fr);margin:10px 12px 8px;padding:3px;background:#19191d;border-radius:11px;flex-shrink:0}
  .tabs::before{content:"";position:absolute;top:3px;bottom:3px;left:3px;width:calc((100% - 6px)/3);border-radius:9px;background:linear-gradient(135deg,#ffb23e,#ff8a1f);transition:transform .28s cubic-bezier(.4,0,.2,1)}
  .tabs[data-idx="1"]::before{transform:translateX(100%)}
  .tabs[data-idx="2"]::before{transform:translateX(200%)}
  .tab{position:relative;z-index:1;border:0;background:transparent;color:#9b9ba7;padding:8px 6px;font-size:11.5px;font-weight:650;cursor:pointer;transition:color .2s}
  .tab.active{color:#1a1a1a}

  .out{flex:1;min-height:0;overflow-y:auto;padding:14px}
  .out[hidden]{display:none!important}
  .out::-webkit-scrollbar,.lscroll::-webkit-scrollbar{width:6px}
  .out::-webkit-scrollbar-thumb,.lscroll::-webkit-scrollbar-thumb{background:#44444c;border-radius:4px}
  .empty{text-align:center;color:#a9a9b4;font-size:12px;line-height:1.7;padding:22px 8px}

  /* bubbles */
  .msg{margin-bottom:12px;font-size:12.5px;line-height:1.7;overflow-wrap:anywhere;white-space:pre-wrap;animation:rise .3s ease both}
  .msg.user{margin-left:34px;padding:9px 13px;background:linear-gradient(135deg,#ffb23e,#ff8a1f);color:#1a1a1a;font-weight:550;border-radius:14px 14px 4px 14px}
  .msg.bot{padding:11px 13px;background:#1e1e23;border:1px solid #3a3a41;border-radius:14px 14px 14px 4px}
  .msg.bot.err{border-color:#6b2f2f;background:#2a1c1c;color:#ffc9c9}
  .msg.nudge{border-color:#ffa11655}
  .msg h4{font-size:13px;color:#ffa116;margin:8px 0 4px}
  .msg ol{padding-left:20px;margin:5px 0}
  .msg p{margin:5px 0}
  .msg .answer{color:#00c2a8;font-weight:700}
  .mtitle{font-size:11px;font-weight:750;color:#ffa116;margin-bottom:5px;letter-spacing:.3px}
  .typing{display:inline-flex;gap:5px;padding:11px 14px;background:#1e1e23;border:1px solid #3a3a41;border-radius:14px;margin-bottom:12px;animation:rise .25s ease both}
  .typing i{width:6px;height:6px;border-radius:50%;background:#ffa116;animation:bounce 1.1s infinite}
  .typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}

  .pill{display:inline-block;border-radius:20px;padding:3px 10px;font-size:10px;font-weight:750;background:#444;margin-bottom:6px;transition:all .3s}
  .pill.HIGH{background:#5b2929;color:#ffb4b4}.pill.MODERATE{background:#59431e;color:#ffd58a}.pill.LOW{background:#1e4939;color:#a4f1cf}
  .muted{color:#a9a9b4;font-size:11px;line-height:1.5;margin-top:6px}
  .actions{display:flex;gap:7px;margin-top:10px;flex-wrap:wrap}

  /* learning view */
  .out.learn{padding:0;overflow:hidden;display:flex;flex-direction:column}
  .lscroll{flex:1;min-height:0;overflow-y:auto;padding:12px 14px}
  .lhead{display:flex;align-items:center;gap:8px;margin-bottom:12px;flex-wrap:wrap}
  .lhead .pill{margin:0}
  .signals{font-size:11px;color:#a9a9b4;flex:1;min-width:0}
  .ghost{border:1px solid #3e3e46;background:transparent;color:#b9b9c4;border-radius:14px;padding:4px 10px;font-size:10.5px;cursor:pointer;transition:all .15s}
  .ghost:hover{border-color:#ffa116;color:#fff}
  .cards{display:flex;flex-direction:column;gap:9px;margin-bottom:16px}
  .acard{display:flex;align-items:center;gap:12px;text-align:left;width:100%;border:1px solid #3d3d46;background:linear-gradient(135deg,#34343c,#2a2a30);border-radius:13px;padding:12px 14px;color:#eef0f6;cursor:pointer;transition:transform .15s,border-color .15s,box-shadow .15s}
  .acard:hover{transform:translateY(-2px);border-color:#ffa116;box-shadow:0 8px 20px #ffa11620}
  .acard:active{transform:translateY(0)}
  .acard:disabled{opacity:.55;cursor:wait;transform:none;box-shadow:none}
  .acard .ci{flex:none;width:36px;height:36px;border-radius:11px;display:grid;place-items:center;background:#ffa11622;font-size:17px}
  .acard b{display:block;font-size:13px;margin-bottom:2px}
  .acard small{color:#a3a3ae;font-size:11px;line-height:1.4}
  .lcomposer{flex-shrink:0;border-top:1px solid #3a3a41;padding:10px 12px;background:#26262b}
  .chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
  .chipb{border:1px solid #3e3e46;background:#2f2f36;color:#cfcfd9;border-radius:16px;padding:5px 10px;font-size:10.5px;cursor:pointer;transition:all .15s}
  .chipb:hover:not(:disabled){border-color:#ffa116;color:#fff;transform:translateY(-1px)}
  .chipb:disabled,.send:disabled{opacity:.5;cursor:wait}
  .sendrow{display:flex;gap:8px}
  .sendrow input{flex:1;min-width:0;background:#19191d;border:1px solid #3a3a41;border-radius:11px;padding:9px 12px;color:#eef0f6;font-size:12px;outline:none;transition:border-color .15s}
  .sendrow input:focus{border-color:#ffa116}
  .send{border:0;border-radius:11px;background:linear-gradient(135deg,#ffb23e,#ff8a1f);color:#1a1a1a;font-weight:800;padding:0 15px;cursor:pointer;transition:transform .15s}
  .send:hover:not(:disabled){transform:scale(1.06)}

  /* solver / quiz composer */
  .composer{border-top:1px solid #3a3a41;padding:10px 12px;background:#26262b;flex-shrink:0}
  textarea{width:100%;resize:vertical;min-height:40px;max-height:90px;background:#19191d;color:#eef0f6;border:1px solid #3a3a41;border-radius:10px;padding:9px;font-size:12px;outline:none}
  textarea:focus{border-color:#ffa116}
  .row{display:flex;align-items:center;gap:7px;margin-top:8px}
  .btn{border:1px solid #3e3e46;background:#35353d;color:#eef0f6;border-radius:9px;padding:8px 11px;font-size:11px;cursor:pointer;white-space:nowrap;transition:all .15s}
  .btn:hover:not(:disabled){border-color:#ffa116}
  .btn.primary{background:linear-gradient(135deg,#ffb23e,#ff8a1f);color:#1a1a1a;border-color:transparent;font-weight:750;flex:1}
  .btn:disabled{opacity:.5;cursor:wait}
  .fname{flex:1;min-width:0;color:#a9a9b4;font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .preview{display:none;max-width:100%;max-height:90px;margin-top:8px;border-radius:8px}
  .status{font-size:10.5px;color:#a9a9b4;margin-top:7px;line-height:1.5}
  .qsec{margin-top:14px;animation:rise .3s ease both}.qsec:first-child{margin-top:0}
  .qsec h4{color:#ffa116;font-size:14px;margin-bottom:4px}
  .qsec h5{font-size:11px;color:#a9a9b4;margin:10px 0 4px;text-transform:uppercase;letter-spacing:.5px}
  .qcard{margin:10px 0;padding:12px;border:1px solid #3a3a41;border-radius:12px;background:#1e1e23}
  .qcard p{margin-bottom:6px;line-height:1.6}
  .qcard label{display:block;margin:6px 0;font-size:12.5px}
  .qans{margin-top:8px;color:#00c2a8}
  `;

  const BOT = '<svg viewBox="0 0 24 24" width="30" height="30" fill="none"><rect x="4" y="8" width="16" height="12" rx="4" fill="#1a1a1a"/><rect x="10.25" y="2.5" width="1.5" height="4" rx=".75" fill="#1a1a1a"/><circle cx="11" cy="2.5" r="1.4" fill="#1a1a1a"/><circle cx="9" cy="14" r="1.9" fill="#ffa116"/><circle cx="15" cy="14" r="1.9" fill="#ffa116"/><rect x="8.5" y="18" width="7" height="1.7" rx=".85" fill="#ffa116"/></svg>';

  const host = document.createElement("div");
  host.id = "cognio-extension-root";
  host.style.cssText = "all:initial;position:fixed;right:22px;bottom:22px;z-index:2147483647;";
  const root = host.attachShadow({ mode: "open" });
  root.innerHTML = `<style>${CSS}</style>
  <div class="widget">
    <div class="chat" id="chat">
      <div class="header">
        <div class="hl"><div class="avatar">C</div>
          <div><div class="title">Cognio</div><div class="sub">Learning companion</div></div></div>
        <div class="hr">
          <span class="schip LOW" id="hChip" title="Live strain estimate"><i></i><span id="hLabel">LOW</span></span>
          <button class="close" id="close" aria-label="Close">✕</button>
        </div>
      </div>

      <div class="tabs" id="tabs" data-idx="0">
        <button class="tab active" data-mode="learning">✦ Learning</button>
        <button class="tab" data-mode="solver">💬 Solver</button>
        <button class="tab" data-mode="quiz">📝 Quiz</button>
      </div>

      <div class="out learn" id="learnOut">
        <div class="lscroll" id="lscroll">
          <div class="lhead">
            <span class="pill LOW" id="lPill">LOW STRAIN</span>
            <span class="signals" id="signals">Attempts: 0 · Incorrect: 0 · Hints: 0</span>
            <button class="ghost" id="analyzeNow">↻ Analyse</button>
          </div>
          <div class="cards">
            <button class="acard" id="cardSimpler"><span class="ci">✦</span>
              <span><b>Show simpler explanation</b><small>Rewrites this page's material in plainer language.</small></span></button>
            <button class="acard" id="cardConcept"><span class="ci">🧩</span>
              <span><b>Simplify concept</b><small>The core idea in short steps, with a quick analogy.</small></span></button>
          </div>
          <div id="learnBody"></div>
        </div>
        <div class="lcomposer">
          <div class="chips" id="chips">
            <button class="chipb" data-msg="That helped, thanks!">👍 That helped</button>
            <button class="chipb" data-msg="I'm still confused. Can you explain it a different way?">😕 Still confused</button>
            <button class="chipb" data-msg="Can you give me an example?">💡 Give an example</button>
            <button class="chipb" data-msg="Please make it shorter and simpler.">✂️ Shorter</button>
          </div>
          <div class="sendrow">
            <input id="lInput" type="text" maxlength="500" placeholder="Ask a follow-up or share feedback…">
            <button class="send" id="lSend" aria-label="Send">➤</button>
          </div>
          <div class="status" id="learnStatus">Behaviour signals are processed locally in this tab.</div>
        </div>
      </div>

      <div class="out" id="solverOut" hidden><div class="empty">
        <div style="font-size:28px;margin-bottom:8px">🤖</div>
        Capture this page or upload an image of a question, then press <b>Solve</b>.</div></div>
      <div class="out" id="quizOut" hidden><div class="empty">
        <div style="font-size:28px;margin-bottom:8px">📝</div>
        Capture this page or upload study material, then press <b>Generate quiz</b>.</div></div>

      <div class="composer" id="composer" style="display:none">
        <textarea id="prompt" placeholder="Optional: what should Cognio focus on?"></textarea>
        <img class="preview" id="preview" alt="Selected image preview">
        <input type="file" id="file" accept="image/png,image/jpeg,image/webp" hidden>
        <div class="row">
          <button class="btn" id="capture">📸 Capture page</button>
          <button class="btn" id="attach">＋ Image</button>
          <button class="btn" id="clear">Clear</button>
        </div>
        <div class="row"><span class="fname" id="fname">No image selected</span></div>
        <div class="row"><button class="btn primary" id="go">Solve image ↗</button></div>
        <div class="status" id="status">Local model · No API key required</div>
      </div>
    </div>
    <button class="fab" id="fab" title="Cognio" aria-label="Open Cognio">${BOT}</button>
  </div>`;
  document.documentElement.appendChild(host);

  const $ = (id) => root.getElementById(id);
  const chat = $("chat"), solverOut = $("solverOut"), quizOut = $("quizOut"), learnOut = $("learnOut");
  const promptEl = $("prompt"), preview = $("preview"), fname = $("fname");
  const statusEl = $("status"), goBtn = $("go"), composerEl = $("composer");
  const buttons = [$("capture"), $("attach"), $("clear"), goBtn];
  const IDLE = "Local model · No API key required";
  const TYPES = ["image/jpeg", "image/png", "image/webp"];
  const TABS = ["learning", "solver", "quiz"];
  let mode = "learning";
  let image = null; // { dataUrl, name }

  const say = (t) => (statusEl.textContent = t);
  const busy = (b) => buttons.forEach((x) => (x.disabled = b));

  function h(tag, props, ...kids) {
    const el = document.createElement(tag);
    Object.assign(el, props || {});
    kids.forEach((k) => el.append(k));
    return el;
  }

  // ---- window + tabs ----
  function selectTab(name) {
    if (!TABS.includes(name)) name = "learning";
    mode = name;
    $("tabs").dataset.idx = String(TABS.indexOf(name));
    root.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.mode === name));
    learnOut.hidden = name !== "learning";
    solverOut.hidden = name !== "solver";
    quizOut.hidden = name !== "quiz";
    composerEl.style.display = name === "learning" ? "none" : "block";
    promptEl.style.display = name === "solver" ? "block" : "none";
    goBtn.textContent = name === "quiz" ? "Generate quiz ↗" : "Solve image ↗";
  }
  root.querySelectorAll(".tab").forEach((tab) =>
    tab.addEventListener("click", () => selectTab(tab.dataset.mode))
  );
  const isOpen = () => chat.classList.contains("open");
  function openChat(tab) { chat.classList.add("open"); if (tab) selectTab(tab); }
  function closeChat() { chat.classList.remove("open"); }
  $("fab").addEventListener("click", () => (isOpen() ? closeChat() : openChat()));
  $("close").addEventListener("click", closeChat);
  chrome.runtime.onMessage.addListener((m) => {
    if (m && m.type === "toggle") (isOpen() ? closeChat() : openChat());
  });

  // keep page hotkeys (LeetCode, YouTube, ...) from firing while typing in Cognio
  [$("lInput"), promptEl].forEach((el) =>
    ["keydown", "keyup", "keypress"].forEach((ev) => el.addEventListener(ev, (e) => e.stopPropagation()))
  );

  // ---- Learning tab: conversation + controls (driven by learning.js) ----
  const learnBody = $("learnBody"), lscroll = $("lscroll");
  const scrollDown = () => requestAnimationFrame(() => (lscroll.scrollTop = lscroll.scrollHeight));
  const handlers = { simpler: null, concept: null, analyze: null, send: null };

  function bubble(cls, text, title) {
    const m = h("div", { className: "msg " + cls });
    if (title) m.append(h("div", { className: "mtitle", textContent: title }));
    m.append(h("div", { textContent: text }));
    learnBody.append(m);
    scrollDown();
    return m;
  }

  const learnControls = [$("cardSimpler"), $("cardConcept"), $("lSend"), $("lInput"), ...root.querySelectorAll(".chipb")];

  $("cardSimpler").addEventListener("click", () => handlers.simpler && handlers.simpler());
  $("cardConcept").addEventListener("click", () => handlers.concept && handlers.concept());
  $("analyzeNow").addEventListener("click", () => handlers.analyze && handlers.analyze());

  function submitInput(text) {
    const v = String(text || "").trim();
    if (!v || !handlers.send) return;
    $("lInput").value = "";
    handlers.send(v);
  }
  $("lSend").addEventListener("click", () => submitInput($("lInput").value));
  $("lInput").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); submitInput($("lInput").value); } });
  root.querySelectorAll(".chipb").forEach((c) => c.addEventListener("click", () => submitInput(c.dataset.msg)));

  bubble("bot", "Hi! I'm Cognio. I watch how you work on this page, and I'll step in if things get tough. You can also use the boxes above anytime, or ask me a follow-up question below.", "COGNIO");

  window.__cognioUI = {
    analyzeBtn: $("analyzeNow"),
    learnStatus: $("learnStatus"),
    signals: $("signals"),
    open: openChat,
    close: closeChat,
    isOpen,
    addBot(text, opts = {}) { return bubble("bot" + (opts.error ? " err" : ""), text, opts.title); },
    addUser(text) { return bubble("user", text); },
    addTyping() {
      const t = h("div", { className: "typing" }, h("i"), h("i"), h("i"));
      learnBody.append(t); scrollDown(); return t;
    },
    addNudge({ level, confidence, summary, auto, onDismiss }) {
      const m = h("div", { className: "msg bot nudge" });
      m.append(h("span", { className: "pill " + level, textContent: `${level} STRAIN · ${Math.round((confidence || 0) * 100)}%` }));
      m.append(h("div", {
        textContent: auto
          ? "This looks tough, so I've opened up to help. I'm preparing a simpler explanation for you now."
          : "This concept may be challenging. Would a different explanation help? Pick one of the boxes above."
      }));
      if (summary) m.append(h("div", { className: "muted", textContent: "Observed: " + summary }));
      if (onDismiss) {
        const b = h("button", { className: "btn", textContent: "Not now" });
        b.addEventListener("click", () => { b.disabled = true; onDismiss(); });
        m.append(h("div", { className: "actions" }, b));
      }
      learnBody.append(m); scrollDown(); return m;
    },
    setStrain(level, confidence) {
      level = ["LOW", "MODERATE", "HIGH"].includes(level) ? level : "LOW";
      $("hChip").className = "schip " + level;
      $("hLabel").textContent = level;
      $("lPill").className = "pill " + level;
      $("lPill").textContent = `${level} STRAIN` + (confidence != null ? ` · ${Math.round(confidence * 100)}%` : "");
    },
    setBusy(b) { learnControls.forEach((x) => (x.disabled = !!b)); },
    onSimpler(fn) { handlers.simpler = fn; },
    onConcept(fn) { handlers.concept = fn; },
    onAnalyze(fn) { handlers.analyze = fn; },
    onSend(fn) { handlers.send = fn; }
  };

  function setImage(dataUrl, name) {
    image = { dataUrl, name };
    preview.src = dataUrl;
    preview.style.display = "block";
    fname.textContent = name;
    say("Image ready. Press the button below.");
  }
  function clearImage() {
    image = null;
    preview.removeAttribute("src");
    preview.style.display = "none";
    fname.textContent = "No image selected";
    $("file").value = "";
    say(IDLE);
  }
  $("clear").addEventListener("click", clearImage);
  $("attach").addEventListener("click", () => $("file").click());

  $("file").addEventListener("change", () => {
    const f = $("file").files[0];
    if (!f) return;
    if (!TYPES.includes(f.type)) return say("Please choose a PNG, JPG or WEBP image.");
    if (f.size > 10 * 1024 * 1024) return say("Image must be 10 MB or smaller.");
    const r = new FileReader();
    r.onload = () => setImage(r.result, f.name);
    r.readAsDataURL(f);
  });

  $("capture").addEventListener("click", async () => {
    busy(true);
    say("Capturing the visible page…");
    host.style.visibility = "hidden";               // keep Cognio out of the screenshot
    await new Promise((r) => setTimeout(r, 150));
    let res;
    try { res = await chrome.runtime.sendMessage({ type: "capture" }); }
    catch (e) { res = { ok: false, error: "Extension was reloaded. Refresh this page." }; }
    host.style.visibility = "visible";
    busy(false);
    if (res && res.ok) setImage(res.dataUrl, "page-capture.jpg");
    else say("Capture failed: " + ((res && res.error) || "unknown error"));
  });

  function clearEmpty(out) { const e = out.querySelector(".empty"); if (e) e.remove(); }

  function addMsg(type, text) {
    clearEmpty(solverOut);
    const m = h("div", { className: "msg " + type, textContent: text });
    solverOut.append(m);
    solverOut.scrollTop = solverOut.scrollHeight;
    return m;
  }

  function renderSolution(r) {
    clearEmpty(solverOut);
    const card = h("div", { className: "msg bot" });
    const add = (tag, text, cls) => card.append(h(tag, { textContent: text || "", className: cls || "" }));
    if (typeof r.answer === "string" && !r.steps && !r.final_answer) {
      add("h4", "Solution"); add("p", r.answer);
    } else {
      if (r.question) { add("h4", "Question identified"); add("p", r.question); }
      if (r.needs_clarification) {
        add("h4", "Need a clearer image");
        add("p", r.clarification_message || "Please upload a clearer image showing the complete question.");
      } else {
        if (r.explanation) { add("h4", "Explanation"); add("p", r.explanation); }
        if (Array.isArray(r.steps) && r.steps.length) {
          add("h4", "Step-by-step solution");
          const ol = h("ol");
          r.steps.forEach((s) => ol.append(h("li", { textContent: s })));
          card.append(ol);
        }
        if (r.final_answer) { add("h4", "Final answer"); add("p", r.final_answer, "answer"); }
      }
    }
    solverOut.append(card);
    solverOut.scrollTop = solverOut.scrollHeight;
  }

  function reveal(card, show, hide, text) {
    const btn = h("button", { className: "btn", textContent: show });
    const ans = h("p", { className: "qans", textContent: text, hidden: true });
    btn.addEventListener("click", () => { ans.hidden = !ans.hidden; btn.textContent = ans.hidden ? show : hide; });
    card.append(btn, ans);
  }

  function renderQuiz(data) {
    quizOut.replaceChildren();
    ["easy", "medium", "hard"].forEach((level) => {
      const q = data[level] || {};
      const mcqs = Array.isArray(q.mcqs) ? q.mcqs : [];
      const conc = Array.isArray(q.conceptual) ? q.conceptual : [];
      if (!mcqs.length && !conc.length) return;
      const sec = h("section", { className: "qsec" });
      sec.append(h("h4", { textContent: level[0].toUpperCase() + level.slice(1) + " Difficulty" }));
      if (mcqs.length) sec.append(h("h5", { textContent: "Multiple-choice" }));
      mcqs.forEach((m, i) => {
        const card = h("div", { className: "qcard" });
        card.append(h("p", { textContent: (i + 1) + ". " + m.question }));
        (Array.isArray(m.options) ? m.options : []).forEach((o) => {
          const radio = h("input", { type: "radio", name: "q-" + level + "-" + i, value: o });
          card.append(h("label", {}, radio, " " + o));
        });
        reveal(card, "Show answer", "Hide answer", "Answer: " + m.answer + (m.explanation ? " — " + m.explanation : ""));
        sec.append(card);
      });
      if (conc.length) sec.append(h("h5", { textContent: "Conceptual" }));
      conc.forEach((c, i) => {
        const card = h("div", { className: "qcard" });
        card.append(h("p", { textContent: (i + 1) + ". " + c.question }));
        reveal(card, "Show suggested answer", "Hide suggested answer", (c.answer || "") + (c.explanation ? " — " + c.explanation : ""));
        sec.append(card);
      });
      quizOut.append(sec);
    });
    if (!quizOut.children.length) say("No questions were returned. Try a clearer image.");
  }

  goBtn.addEventListener("click", async () => {
    if (!image) return say("Capture the page or upload an image first.");
    const solver = mode === "solver";
    const focus = promptEl.value.trim();
    if (solver) {
      addMsg("user", "Please solve this image." + (focus ? " Focus: " + focus : ""));
    } else {
      quizOut.replaceChildren();
    }
    const loading = solver ? addMsg("bot", "Reading the image and working through the solution…") : null;
    busy(true);
    say(solver ? "Waiting for the local model. The first request may take longer."
               : "Reading the page and generating questions… this can take a few minutes.");
    let res;
    try {
      res = await chrome.runtime.sendMessage({
        type: "api",
        path: solver ? "/api/v1/visual/solve" : "/api/v1/visual-quiz/generate",
        dataUrl: image.dataUrl,
        fileName: image.name,
        question: solver ? focus : undefined
      });
    } catch (e) {
      res = { ok: false, data: { detail: "Extension was reloaded. Refresh this page and try again." } };
    }
    busy(false);
    if (res && res.ok) {
      if (solver) { loading.remove(); renderSolution(res.data); say("Solved locally."); }
      else { renderQuiz(res.data); say("Quiz generated successfully."); }
    } else {
      const d = res && res.data && res.data.detail;
      const text = typeof d === "string" ? d : "Request failed.";
      if (solver) loading.textContent = "Error: " + text;
      else quizOut.append(h("div", { className: "msg bot", textContent: "Error: " + text }));
      say("Check the backend and Ollama if this keeps failing.");
    }
  });
})();