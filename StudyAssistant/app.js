/* ═══════════════════════════════════════════
   STUDYAI — App Logic
   ═══════════════════════════════════════════ */

'use strict';

// ── DOM References ──────────────────────────
const $ = id => document.getElementById(id);

const statusDot      = $('statusDot');
const statusText     = $('statusText');
const statusPulse    = $('statusPulse');
const startBtn       = $('startBtn');
const btnIcon        = $('btnIcon');
const btnLabel       = $('btnLabel');
const answerOverlay  = $('answerOverlay');
const scanIndicator  = $('scanIndicator');
const scanOverlay    = $('scanOverlay');
const questionBlock  = $('questionBlock');
const aoLetter       = $('aoLetter');
const aoAnswerText   = $('aoAnswerText');
const aoExplanation  = $('aoExplanation');
const aoConf         = $('aoConf');
const aoTimerFill    = $('aoTimerFill');
const aoTimerLabel   = $('aoTimerLabel');
const scanCount      = $('scanCount');
const ansCount       = $('ansCount');
const accVal         = $('accVal');
const demoBtn        = $('demoBtn');
const nextQBtn       = $('nextQBtn');

// ── State ───────────────────────────────────
let appState       = 'idle';   // idle | scanning | ready
let isRunning      = false;
let autoHideTimer  = null;
let timerInterval  = null;
let statsScanned   = 0;
let statsAnswered  = 0;
let currentQIndex  = 0;
const AUTO_HIDE_MS = 8000;

// ── Question Bank ───────────────────────────
const questions = [
  {
    text: 'Which data structure uses LIFO (Last In, First Out) ordering?',
    opts: ['A. Queue', 'B. Stack', 'C. Linked List', 'D. Hash Map'],
    answer: 'B',
    label: 'Stack',
    explanation: 'Stack follows LIFO — the last element pushed is the first to be popped.',
    confidence: '98%',
  },
  {
    text: 'What is the time complexity of binary search on a sorted array?',
    opts: ['A. O(n)', 'B. O(n²)', 'C. O(log n)', 'D. O(1)'],
    answer: 'C',
    label: 'O(log n)',
    explanation: 'Binary search halves the search space each step, yielding logarithmic time.',
    confidence: '99%',
  },
  {
    text: 'Which HTTP status code indicates "Not Found"?',
    opts: ['A. 200', 'B. 301', 'C. 500', 'D. 404'],
    answer: 'D',
    label: '404',
    explanation: '404 Not Found is returned when the server cannot locate the requested resource.',
    confidence: '100%',
  },
  {
    text: 'Which layer of the OSI model handles routing between networks?',
    opts: ['A. Transport', 'B. Network', 'C. Data Link', 'D. Physical'],
    answer: 'B',
    label: 'Network',
    explanation: 'The Network layer (Layer 3) manages routing, forwarding, and IP addressing.',
    confidence: '97%',
  },
  {
    text: 'In Python, which keyword is used to define a generator function?',
    opts: ['A. return', 'B. async', 'C. yield', 'D. lambda'],
    answer: 'C',
    label: 'yield',
    explanation: 'The yield keyword pauses execution and returns a value, making a generator.',
    confidence: '99%',
  },
  {
    text: 'Which sorting algorithm has O(n log n) average-case complexity?',
    opts: ['A. Bubble Sort', 'B. Insertion Sort', 'C. Merge Sort', 'D. Selection Sort'],
    answer: 'C',
    label: 'Merge Sort',
    explanation: 'Merge Sort consistently divides and merges, achieving O(n log n) on average.',
    confidence: '98%',
  },
];

// ── Canvas Background (particle grid) ───────
(function initCanvas() {
  const canvas = $('bgCanvas');
  const ctx    = canvas.getContext('2d');
  let W, H, particles = [], mouseX = 0, mouseY = 0;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function Particle() {
    this.x  = Math.random() * W;
    this.y  = Math.random() * H;
    this.vx = (Math.random() - 0.5) * 0.3;
    this.vy = (Math.random() - 0.5) * 0.3;
    this.r  = Math.random() * 1.5 + 0.5;
    this.a  = Math.random() * 0.4 + 0.1;
  }

  Particle.prototype.update = function() {
    this.x += this.vx;
    this.y += this.vy;
    if (this.x < 0) this.x = W;
    if (this.x > W) this.x = 0;
    if (this.y < 0) this.y = H;
    if (this.y > H) this.y = 0;
  };

  function spawnParticles() {
    const count = Math.floor((W * H) / 12000);
    particles = Array.from({ length: count }, () => new Particle());
  }

  function drawLines() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const d  = Math.sqrt(dx * dx + dy * dy);
        if (d < 130) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(56,189,248,${(1 - d / 130) * 0.07})`;
          ctx.lineWidth = 0.7;
          ctx.stroke();
        }
      }
      // mouse proximity glow
      const mdx = particles[i].x - mouseX;
      const mdy = particles[i].y - mouseY;
      const md  = Math.sqrt(mdx * mdx + mdy * mdy);
      if (md < 160) {
        ctx.beginPath();
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(mouseX, mouseY);
        ctx.strokeStyle = `rgba(56,189,248,${(1 - md / 160) * 0.15})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }
    }
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);

    // Subtle background gradient
    const grad = ctx.createRadialGradient(W * 0.3, H * 0.3, 0, W * 0.3, H * 0.3, W * 0.7);
    grad.addColorStop(0, 'rgba(14,28,54,0.5)');
    grad.addColorStop(1, 'rgba(8,12,20,0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    particles.forEach(p => {
      p.update();
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(56,189,248,${p.a})`;
      ctx.fill();
    });

    drawLines();
    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', () => { resize(); spawnParticles(); });
  window.addEventListener('mousemove', e => { mouseX = e.clientX; mouseY = e.clientY; });
  resize();
  spawnParticles();
  draw();
})();

// ── State Machine ────────────────────────────
function setState(state) {
  appState = state;
  statusDot.className   = 'status-dot ' + state;
  statusText.className  = 'status-text ' + state;

  const labels = { idle: 'Idle', scanning: 'Scanning', ready: 'Answer Ready' };
  statusText.textContent = labels[state] || state;

  statusPulse.className = 'status-pulse' + (state === 'scanning' ? ' active' : '');
}

// ── Load Question onto Screen ─────────────────
function loadQuestion(index) {
  const q = questions[index];
  const qText = questionBlock.querySelector('.q-text');
  const optList = questionBlock.querySelector('.options-list');

  // fade out, swap, fade in
  questionBlock.style.opacity = '0';
  questionBlock.style.transform = 'translateY(6px)';

  setTimeout(() => {
    qText.textContent = q.text;
    optList.innerHTML = q.opts.map(o =>
      `<li class="opt" data-val="${o[0]}">${o}</li>`
    ).join('');

    // re-attach hover listeners
    optList.querySelectorAll('.opt').forEach(el => {
      el.addEventListener('click', () => {
        if (isRunning) runScan();
      });
    });

    questionBlock.style.opacity = '1';
    questionBlock.style.transform = 'translateY(0)';
    questionBlock.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
  }, 200);
}

// ── Show Answer Overlay ─────────────────────
function showAnswer(q) {
  // Populate
  aoLetter.textContent      = q.answer;
  aoAnswerText.textContent  = q.label;
  aoExplanation.textContent = q.explanation;
  aoConf.textContent        = q.confidence + ' confident';

  // Reset letter animation
  aoLetter.style.animation = 'none';
  aoAnswerText.style.animation = 'none';
  aoExplanation.style.animation = 'none';
  requestAnimationFrame(() => {
    aoLetter.style.animation      = 'letterPop 0.5s cubic-bezier(0.34,1.56,0.64,1) both';
    aoAnswerText.style.animation  = 'slideRight 0.4s ease both 0.1s';
    aoExplanation.style.animation = 'fadeUp 0.4s ease both 0.2s';
  });

  // Highlight correct option
  const opts = document.querySelectorAll('.opt');
  opts.forEach(el => el.classList.remove('correct'));
  opts.forEach(el => {
    if (el.dataset.val === q.answer) el.classList.add('correct');
  });

  answerOverlay.classList.remove('fading');
  answerOverlay.classList.add('visible');
  startAutoHide();

  // Update stats
  statsAnswered++;
  ansCount.textContent = statsAnswered;
  accVal.textContent   = '100%';
}

// ── Auto-hide Timer ─────────────────────────
function startAutoHide() {
  clearTimers();
  let elapsed = 0;
  const tick  = 100;

  aoTimerFill.style.transform = 'scaleX(1)';
  aoTimerLabel.textContent    = `Auto-hide in ${AUTO_HIDE_MS / 1000}s`;

  timerInterval = setInterval(() => {
    elapsed += tick;
    const progress = 1 - (elapsed / AUTO_HIDE_MS);
    aoTimerFill.style.transform = `scaleX(${Math.max(0, progress)})`;
    const remaining = Math.ceil((AUTO_HIDE_MS - elapsed) / 1000);
    aoTimerLabel.textContent = remaining > 0 ? `Auto-hide in ${remaining}s` : 'Hiding…';
  }, tick);

  autoHideTimer = setTimeout(() => {
    hideAnswer();
  }, AUTO_HIDE_MS);
}

function clearTimers() {
  clearTimeout(autoHideTimer);
  clearInterval(timerInterval);
}

function hideAnswer() {
  clearTimers();
  answerOverlay.classList.add('fading');
  setTimeout(() => {
    answerOverlay.classList.remove('visible', 'fading');
    // Remove correct highlight
    document.querySelectorAll('.opt').forEach(el => el.classList.remove('correct'));
  }, 500);
}

// ── Scan Sequence ───────────────────────────
function runScan() {
  if (appState === 'scanning') return;

  // Hide previous answer if any
  if (answerOverlay.classList.contains('visible')) {
    hideAnswer();
  }

  // Count scan
  statsScanned++;
  scanCount.textContent = statsScanned;

  // Start scanning
  setState('scanning');
  questionBlock.classList.add('scanning');
  scanIndicator.classList.add('visible');
  scanOverlay.classList.add('active');

  const delay = 900 + Math.random() * 600;   // realistic "AI thinking" feel

  setTimeout(() => {
    scanIndicator.classList.remove('visible');
    scanOverlay.classList.remove('active');
    questionBlock.classList.remove('scanning');

    setState('ready');
    showAnswer(questions[currentQIndex]);

    // After overlay hides, go back to idle (if still running)
    setTimeout(() => {
      if (isRunning) setState('scanning');
      else setState('idle');
    }, AUTO_HIDE_MS + 600);

  }, delay);
}

// ── Start / Stop Toggle ─────────────────────
startBtn.addEventListener('click', () => {
  isRunning = !isRunning;

  if (isRunning) {
    startBtn.classList.remove('stop');
    startBtn.classList.add('stop');
    btnIcon.textContent  = '■';
    btnLabel.textContent = 'Stop';
    setState('scanning');
    // Auto-trigger first scan
    setTimeout(runScan, 400);
  } else {
    startBtn.classList.remove('stop');
    btnIcon.textContent  = '▶';
    btnLabel.textContent = 'Start Scanning';
    hideAnswer();
    setState('idle');
  }
});

// ── Demo Button ─────────────────────────────
demoBtn.addEventListener('click', () => {
  if (appState === 'scanning') return;
  runScan();
});

// ── Next Question ───────────────────────────
nextQBtn.addEventListener('click', () => {
  hideAnswer();
  setState('idle');
  currentQIndex = (currentQIndex + 1) % questions.length;
  loadQuestion(currentQIndex);
});

// ── Keyboard Hotkey (Ctrl + Shift + A) ──────
document.addEventListener('keydown', e => {
  if (e.ctrlKey && e.shiftKey && e.key === 'A') {
    e.preventDefault();
    if (!isRunning) runScan();
  }
});

// ── Click on options triggers scan ──────────
document.querySelectorAll('.opt').forEach(el => {
  el.addEventListener('click', () => {
    if (isRunning) runScan();
  });
});

// ── Click on overlay to dismiss ─────────────
answerOverlay.addEventListener('click', () => hideAnswer());

// ── Initial State ────────────────────────────
loadQuestion(0);
setState('idle');
