// The Model Verse — Interactive Studio Client

let currentVideos = [];
let currentTemplates = [];
let activeJobEventSource = null;

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  loadSystemStatus();
  loadDigest();
  loadTemplates();
  loadVideos();
  setupSliders();
  setupEventListeners();
});

function initTabs() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const parentTabs = btn.closest(".panel-tabs");
      parentTabs.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const targetTab = btn.getAttribute("data-tab");
      const container = btn.closest(".panel").querySelector(".panel-body");
      container.querySelectorAll(".tab-content").forEach(content => {
        content.style.display = content.id === targetTab ? "block" : "none";
      });
    });
  });
}

function setupSliders() {
  const duckSlider = document.getElementById("duckGainSlider");
  const duckVal = document.getElementById("duckGainVal");
  if (duckSlider && duckVal) {
    duckSlider.addEventListener("input", (e) => {
      duckVal.textContent = `${Math.round(e.target.value * 100)}%`;
    });
  }

  const swellSlider = document.getElementById("swellGainSlider");
  const swellVal = document.getElementById("swellGainVal");
  if (swellSlider && swellVal) {
    swellSlider.addEventListener("input", (e) => {
      swellVal.textContent = `${Math.round(e.target.value * 100)}%`;
    });
  }

  const speedSlider = document.getElementById("speedSlider");
  const speedVal = document.getElementById("speedVal");
  if (speedSlider && speedVal) {
    speedSlider.addEventListener("input", (e) => {
      speedVal.textContent = `${parseFloat(e.target.value).toFixed(2)}x`;
    });
  }
}

function setupEventListeners() {
  document.getElementById("btnSynthTest").addEventListener("click", testSynthPreview);
  document.getElementById("btnProduce").addEventListener("click", triggerProduction);
  document.getElementById("videoSelect").addEventListener("change", (e) => {
    const selected = currentVideos.find(v => v.filename === e.target.value);
    if (selected) renderVideoView(selected);
  });

  // Modal close
  document.getElementById("imageModal").addEventListener("click", () => {
    document.getElementById("imageModal").style.display = "none";
  });
}

// -------------------------------------------------------------
// Data Loaders
// -------------------------------------------------------------

async function loadSystemStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    document.getElementById("statusKokoro").textContent = data.kokoro_ready ? "ONLINE" : "OFFLINE";
    document.getElementById("statusFFmpeg").textContent = data.ffmpeg_ready ? "READY" : "MISSING";
    document.getElementById("videoCountBadge").textContent = `${data.video_count} Produced`;
  } catch (err) {
    console.error("Status load failed", err);
  }
}

async function loadDigest() {
  const container = document.getElementById("tabDigest");
  container.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-dim);">Scraping arXiv & HuggingFace trending papers...</div>`;
  try {
    const res = await fetch("/api/digest?limit=10");
    const papers = await res.json();
    if (!Array.isArray(papers) || papers.length === 0) {
      container.innerHTML = `<div style="color:var(--text-dim); text-align:center;">No trending papers retrieved.</div>`;
      return;
    }

    container.innerHTML = papers.map(p => `
      <div class="digest-card" onclick="selectTrendingPaper('${escapeHtml(p.id)}', '${escapeHtml(p.title)}', '${p.recommended_category}')">
        <div class="digest-header">
          <span class="digest-score">⚡ ${p.impact_score || 0} pts</span>
          <span class="digest-cat">${(p.recommended_category || 'deepdive').replace('_', ' ')}</span>
        </div>
        <div class="digest-title">${escapeHtml(p.title)}</div>
        <div class="digest-abstract">${escapeHtml(p.abstract || '')}</div>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<div style="color:var(--danger); padding:10px;">Failed to load digest.</div>`;
  }
}

async function loadTemplates() {
  const container = document.getElementById("tabTemplates");
  try {
    const res = await fetch("/api/templates");
    currentTemplates = await res.json();
    container.innerHTML = currentTemplates.map(t => `
      <div class="template-item" onclick="selectTemplate('${t.filename}')">
        <div class="template-info">
          <h4>${escapeHtml(t.title)}</h4>
          <div class="template-meta">${t.category} • ${t.beat_count} Beats • ~${t.estimated_duration}s</div>
        </div>
        <span style="font-size:12px; color:var(--mint);">Inspect ➔</span>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<div style="color:var(--danger);">Error loading templates.</div>`;
  }
}

async function selectTemplate(filename) {
  try {
    const res = await fetch(`/api/templates/${filename}`);
    const spec = await res.json();
    
    // Auto-fill produce form
    document.getElementById("prodTopic").value = spec.title || spec.id;
    document.getElementById("prodCategory").value = spec.category || "mechanism_deepdive";
    document.getElementById("prodSkipScript").checked = true;

    // Render beats in inspection box
    const beatsContainer = document.getElementById("templateBeatList");
    beatsContainer.innerHTML = (spec.beats || []).map(b => `
      <div class="beat-item">
        <div class="beat-time">Beat ${b.beat_id} [${b.start ? b.start.toFixed(1) : 0}s ➔ ${b.end ? b.end.toFixed(1) : (b.duration || 5)}s]</div>
        <div class="beat-text">"${escapeHtml(b.text)}"</div>
        ${b.formula ? `<div style="font-family:var(--font-mono); font-size:10px; color:var(--cyan); margin-top:2px;">TeX: ${escapeHtml(b.formula)}</div>` : ''}
      </div>
    `).join("");

    // Switch to beat viewer tab
    document.querySelector('[data-tab="tabBeatViewer"]').click();
  } catch (err) {
    console.error("Error selecting template", err);
  }
}

function selectTrendingPaper(arxivId, title, category) {
  document.getElementById("prodTopic").value = title;
  document.getElementById("prodArxiv").value = arxivId;
  document.getElementById("prodCategory").value = category;
  document.getElementById("prodSkipScript").checked = false;
  
  // Highlight produce card
  const cta = document.getElementById("btnProduce");
  cta.scrollIntoView({ behavior: "smooth" });
}

async function loadVideos() {
  try {
    const res = await fetch("/api/videos");
    currentVideos = await res.json();
    const select = document.getElementById("videoSelect");
    
    if (currentVideos.length === 0) {
      select.innerHTML = `<option value="">No videos rendered yet</option>`;
      return;
    }

    select.innerHTML = currentVideos.map(v => `
      <option value="${v.filename}">${v.title} (${v.size_mb} MB)</option>
    `).join("");

    // Default to first video
    renderVideoView(currentVideos[0]);
  } catch (err) {
    console.error("Error loading videos", err);
  }
}

function renderVideoView(video) {
  const player = document.getElementById("mainVideoPlayer");
  player.src = video.url;
  player.load();

  document.getElementById("videoTitleLabel").textContent = video.title;
  document.getElementById("videoMetaLabel").textContent = `${video.size_mb} MB • ${video.created_at}`;

  // Keyframe filmstrip
  const strip = document.getElementById("keyframeStrip");
  if (video.keyframes && video.keyframes.length > 0) {
    strip.innerHTML = video.keyframes.map((kf, idx) => {
      const fname = kf.split("/").pop();
      return `
        <div class="keyframe-card" onclick="openKeyframeModal('${kf}')">
          <img src="${kf}" alt="Keyframe ${idx + 1}" loading="lazy"/>
          <div class="keyframe-label">Beat ${idx + 1}</div>
        </div>
      `;
    }).join("");
  } else {
    strip.innerHTML = `<div style="color:var(--text-dim); font-size:12px; padding:10px;">No keyframes extracted for this video.</div>`;
  }

  // Audio decks
  if (video.audio) {
    if (video.audio.narration) document.getElementById("audioNarration").src = video.audio.narration;
    if (video.audio.soundtrack) document.getElementById("audioSoundtrack").src = video.audio.soundtrack;
    if (video.audio.master) document.getElementById("audioMaster").src = video.audio.master;
  }
}

function openKeyframeModal(src) {
  const modal = document.getElementById("imageModal");
  const modalImg = document.getElementById("modalImg");
  modalImg.src = src;
  modal.style.display = "flex";
}

// -------------------------------------------------------------
// Audio Synth Preview & Ducking Simulator
// -------------------------------------------------------------

async function testSynthPreview() {
  const btn = document.getElementById("btnSynthTest");
  const duckGain = parseFloat(document.getElementById("duckGainSlider").value);
  const normalGain = parseFloat(document.getElementById("swellGainSlider").value);

  btn.textContent = "⏳ Generating...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/audio/preview-synth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        duration: 6.0,
        duck_gain: duckGain,
        normal_gain: normalGain,
        simulate_ducking: true
      })
    });
    const data = await res.json();
    if (data.audio_url) {
      const audioTrack = document.getElementById("audioSoundtrack");
      audioTrack.src = data.audio_url;
      audioTrack.play();
      appendLogLine(`🎵 Generated 6.0s procedural synth preview with dynamic ducking: ${data.audio_url}`);
    }
  } catch (err) {
    console.error("Preview failed", err);
    appendLogLine(`❌ Failed to generate synth preview: ${err}`);
  } finally {
    btn.textContent = "🎹 Test Synth Ducking";
    btn.disabled = false;
  }
}

// -------------------------------------------------------------
// Autonomous Video Production Trigger & SSE Log Stream
// -------------------------------------------------------------

async function triggerProduction() {
  const topic = document.getElementById("prodTopic").value.trim();
  const arxiv = document.getElementById("prodArxiv").value.trim();
  const category = document.getElementById("prodCategory").value;
  const voice = document.getElementById("prodVoice").value;
  const speed = parseFloat(document.getElementById("speedSlider").value);
  const quality = document.getElementById("prodQuality").value;
  const skipScript = document.getElementById("prodSkipScript").checked;
  const enableMusic = document.getElementById("prodEnableMusic").checked;
  const dryRunPublish = document.getElementById("prodDryRunPublish").checked;

  if (!topic && !arxiv) {
    alert("Please enter a topic or an arXiv paper ID.");
    return;
  }

  const btn = document.getElementById("btnProduce");
  btn.textContent = "⚙️ Producing Short...";
  btn.disabled = true;

  clearLogs();
  appendLogLine(`🚀 Dispatching autonomous production job: [${category}] ${topic || arxiv}...`);

  try {
    const res = await fetch("/api/produce", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic: topic || null,
        arxiv: arxiv || null,
        category: category,
        voice: voice,
        speed: speed,
        quality: quality,
        skip_script: skipScript,
        enable_music: enableMusic,
        dry_run_publish: dryRunPublish,
        publish: false
      })
    });
    const data = await res.json();
    const jobId = data.job_id;
    appendLogLine(`📡 Job registered: ${jobId}. Connecting to live log stream...`);

    // Connect SSE
    if (activeJobEventSource) activeJobEventSource.close();
    activeJobEventSource = new EventSource(`/api/jobs/${jobId}/stream`);

    activeJobEventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.line) appendLogLine(payload.line);
      } catch (e) {
        appendLogLine(event.data);
      }
    };

    activeJobEventSource.addEventListener("end", (event) => {
      activeJobEventSource.close();
      activeJobEventSource = null;
      btn.textContent = "⚡ Produce Broadcast Short";
      btn.disabled = false;
      appendLogLine("🎉 Production workflow complete! Refreshing video library...");
      loadVideos();
    });

    activeJobEventSource.onerror = (err) => {
      console.warn("SSE connection closed or error", err);
      if (activeJobEventSource) activeJobEventSource.close();
      btn.textContent = "⚡ Produce Broadcast Short";
      btn.disabled = false;
    };

  } catch (err) {
    appendLogLine(`❌ Failed to start job: ${err}`);
    btn.textContent = "⚡ Produce Broadcast Short";
    btn.disabled = false;
  }
}

// -------------------------------------------------------------
// Terminal Helpers
// -------------------------------------------------------------

function appendLogLine(text) {
  const container = document.getElementById("terminalLogs");
  const div = document.createElement("div");
  div.className = "log-line";
  div.textContent = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function clearLogs() {
  document.getElementById("terminalLogs").innerHTML = "";
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
