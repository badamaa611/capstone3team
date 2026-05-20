// ── Тестийн логик ──────────────────────────────────────────────
let questions   = [];
let currentIdx  = 0;
let answers     = {};  // { question_id: hariult }
let timerSec    = 80 * 60;
let timerHandle = null;

// Тест ачааллах (URL-ээс параметр авна)
async function loadTest() {
  const params   = new URLSearchParams(window.location.search);
  const angi     = params.get("angi")    || "12";
  const hicheel  = params.get("hicheel") || "Биологи";

  const res  = await fetch(`/api/test/generate?angi=${angi}&hicheel=${encodeURIComponent(hicheel)}&too=30`);
  const data = await res.json();
  questions  = data.asuultuud || [];

  document.getElementById("total-q").textContent = questions.length;
  showQuestion(0);
  startTimer();
}

function showQuestion(idx) {
  if (!questions.length) return;
  currentIdx = idx;
  const q = questions[idx];

  document.getElementById("q-num").textContent  = idx + 1;
  document.getElementById("current-q").textContent = idx + 1;
  document.getElementById("q-text").textContent = q.asuult;

  const imgBox = document.getElementById("q-image-box");
  const img = document.getElementById("q-image");
  if (q.image_url && q.image_url.trim() !== '') {
    img.src = q.image_url;
    imgBox.style.display = "block";
  } else {
    imgBox.style.display = "none";
  }

  const optBox  = document.getElementById("options");
  const labels  = ["A","B","V","G","D"];
  const hariult = [q.a_hariu, q.b_hariu, q.v_hariu, q.g_hariu, q.d_hariu];

  optBox.innerHTML = "";
  labels.forEach((lbl, i) => {
    if (!hariult[i]) return;
    const btn = document.createElement("button");
    btn.className = "option-btn";
    if (answers[q.id] === lbl) btn.classList.add("selected");
    btn.textContent = `${lbl}. ${hariult[i]}`;
    btn.onclick = () => selectAnswer(q.id, lbl);
    optBox.appendChild(btn);
  });

  document.getElementById("prev-btn").disabled   = idx === 0;
  document.getElementById("next-btn").style.display   = idx < questions.length - 1 ? "" : "none";
  document.getElementById("finish-btn").style.display = idx === questions.length - 1 ? "" : "none";
}

function selectAnswer(qId, hariult) {
  answers[qId] = hariult;
  document.querySelectorAll(".option-btn").forEach((btn) => {
    btn.classList.toggle("selected", btn.textContent.startsWith(hariult + "."));
  });
}

function nextQuestion() { if (currentIdx < questions.length - 1) showQuestion(currentIdx + 1); }
function prevQuestion() { if (currentIdx > 0) showQuestion(currentIdx - 1); }

async function finishTest() {
  if (!confirm("Тестийг дуусгах уу?")) return;
  clearInterval(timerHandle);
  const res = await fetch("/api/test/submit", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ answers })
  });
  const data = await res.json();
  const params = new URLSearchParams(window.location.search);
  const angi = params.get("angi") || "12";
  const hicheel = params.get("hicheel") || "Биологи";
  const resultData = { ...data, angi, hicheel };
  sessionStorage.setItem('lastTestResult', JSON.stringify(resultData));
  location.href = `/result?onoo=${data.onoo}&niit=${data.niit}`;
}

function startTimer() {
  timerHandle = setInterval(() => {
    timerSec--;
    const m = Math.floor(timerSec / 60).toString().padStart(2,"0");
    const s = (timerSec % 60).toString().padStart(2,"0");
    const el = document.getElementById("timer");
    if (el) {
      el.textContent = `${m}:${s}`;
      if (timerSec < 300) el.style.color = "#ef4444";
    }
    if (timerSec <= 0) finishTest();
  }, 1000);
}

async function loadResult() {
  const params = new URLSearchParams(window.location.search);
  const onoo = params.get("onoo") || "0";
  const niit = params.get("niit") || "0";

  const scoreEl = document.getElementById("onoo");
  if (scoreEl) scoreEl.textContent = onoo;
  const totalEl = document.querySelector(".score-circle small");
  if (totalEl) totalEl.textContent = `/${niit}`;

  const stored = sessionStorage.getItem('lastTestResult');
  if (!stored) return;
  const result = JSON.parse(stored);
  if (!result) return;

  const list = document.getElementById("weak-list");
  if (list) {
    if (result.sul_sedewnuud && result.sul_sedewnuud.length) {
      list.innerHTML = result.sul_sedewnuud.map(item =>
        `<div class="weak-item"><strong>${item.hicheel}</strong>: ${item.sedew} (${item.aldaa} алдаа)</div>`
      ).join('');
    } else {
      list.innerHTML = '<p>Алдаа олдсонгүй эсвэл сул сэдэв бүртгэгдээгүй байна.</p>';
    }
  }
}

async function loadAIQuestions() {
  const stored = sessionStorage.getItem('lastTestResult');
  if (!stored) {
    alert('Тестийн үр дүн олдсонгүй. Тестийг эхлээд өгөөд, дараа AI асуулт үүсгэнэ үү.');
    return;
  }

  const result = JSON.parse(stored);
  const weak = result.sul_sedewnuud && result.sul_sedewnuud.length ? result.sul_sedewnuud[0] : null;
  if (!weak) {
    alert('Сул сэдэв байхгүй тул AI асуулт үүсгэж чадахгүй байна.');
    return;
  }

  const aiSection = document.getElementById("ai-section");
  const aiList = document.getElementById("ai-questions-list");
  if (!aiSection || !aiList) return;

  aiSection.style.display = "block";
  aiList.innerHTML = '<p>AI асуулт үүсгэж байна...</p>';

  const res = await fetch('/api/generate-questions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      angi: result.angi || '12',
      hicheel: weak.hicheel || '',
      sedew: weak.sedew || '',
      too: 3
    })
  });

  const data = await res.json();
  if (!data.asuultuud || !data.asuultuud.length) {
    aiList.innerHTML = '<p>AI-аар асуулт үүсгэж чадсангүй.</p>';
    return;
  }

  aiList.innerHTML = data.asuultuud.map((q, idx) =>
    `<div class="ai-question"><strong>${idx + 1}. ${q.asuult}</strong><p>A. ${q.a_hariu}</p><p>B. ${q.b_hariu}</p><p>В. ${q.v_hariu}</p><p>Г. ${q.g_hariu}</p></div>`
  ).join('');
}

// Тест хуудсан дээр байвал ачааллана
if (document.getElementById("question-box")) loadTest();
if (document.getElementById("onoo")) loadResult();
