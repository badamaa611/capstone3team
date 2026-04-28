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

  const res  = await fetch(`/api/test/generate?angi=${angi}&hicheel=${hicheel}&too=30`);
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

  const optBox  = document.getElementById("options");
  const labels  = ["A","B","V","G","D"];
  const hariult = [q.a_hariu, q.b_hariu, q.v_hariu, q.g_hariu, q.d_hariu];

  optBox.innerHTML = "";
  labels.forEach((lbl, i) => {
    if (!hariult[i]) return;
    const btn = document.createElement("button");
    btn.className = "option-btn";
    if (answers[q.id] === lbl) btn.classList.add("selected");
    btn.textContent = `${lbl}. ${hariuht[i]}`;
    btn.onclick = () => selectAnswer(q.id, lbl);
    optBox.appendChild(btn);
  });

  document.getElementById("prev-btn").disabled   = idx === 0;
  document.getElementById("next-btn").style.display   = idx < questions.length - 1 ? "" : "none";
  document.getElementById("finish-btn").style.display = idx === questions.length - 1 ? "" : "none";
}

function selectAnswer(qId, hariult) {
  answers[qId] = hariult;
  document.querySelectorAll(".option-btn").forEach((btn, i) => {
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
  // Үр дүнгийн хуудас руу шилжих
  location.href = `/result?onoo=${data.onoo}`;
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

async function loadAIQuestions() {
  document.getElementById("ai-section").style.display = "block";
  // TODO: сул сэдвүүдийн жагсаалтаас анхны сэдвийг авч AI-руу илгээх
}

// Тест хуудсан дээр байвал ачааллана
if (document.getElementById("question-box")) loadTest();
