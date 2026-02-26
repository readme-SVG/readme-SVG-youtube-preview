let currentVideoId = null;
let currentTab = 'markdown';
let badgeUrl = '';

function syncColor(pickerId, textId) {
  const picker = document.getElementById(pickerId);
  const text = document.getElementById(textId);
  picker.addEventListener('input', () => { text.value = picker.value; });
  text.addEventListener('input', () => {
    if (/^#[0-9a-fA-F]{6}$/.test(text.value)) picker.value = text.value;
  });
}

syncColor('bg-color-picker', 'bg-color-text');
syncColor('title-color-picker', 'title-color-text');
syncColor('plate-color-picker', 'plate-color-text');
syncColor('border-color-picker', 'border-color-text');

document.getElementById('url-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') generate();
});

function showError(msg) {
  const el = document.getElementById('error-msg');
  el.textContent = msg;
  el.classList.add('visible');
}

function hideError() {
  document.getElementById('error-msg').classList.remove('visible');
}

async function generate() {
  const url = document.getElementById('url-input').value.trim();
  if (!url) { showError('Please enter a YouTube URL or video ID'); return; }

  hideError();
  document.getElementById('result-card').classList.remove('visible');
  document.getElementById('loading').classList.add('visible');
  document.getElementById('gen-btn').disabled = true;

  try {
    const infoResp = await fetch(`/info?url=${encodeURIComponent(url)}`);
    if (!infoResp.ok) { throw new Error('Could not find video. Check the URL and try again.'); }
    const info = await infoResp.json();
    currentVideoId = info.id;

    const width = document.getElementById('width-input').value || 320;
    const radius = document.getElementById('radius-input').value || 8;
    const bg = document.getElementById('bg-color-text').value.replace('#', '');
    const titleColor = document.getElementById('title-color-text').value.replace('#', '');
    const plateColor = document.getElementById('plate-color-text').value.replace('#', '');
    const titleOpacity = document.getElementById('title-opacity-input').value || 1;
    const plateOpacity = document.getElementById('plate-opacity-input').value || 0.78;
    const titlePosition = document.getElementById('title-position-input').value || 'overlay_bottom';
    const borderWidth = document.getElementById('border-width-input').value || 1;
    const borderColor = document.getElementById('border-color-text').value.replace('#', '');

    badgeUrl = `/badge?id=${currentVideoId}&width=${width}&radius=${radius}&bg=${bg}&title_color=${titleColor}&title_opacity=${titleOpacity}&plate_color=${plateColor}&plate_opacity=${plateOpacity}&title_position=${titlePosition}&border_width=${borderWidth}&border_color=${borderColor}`;

    const ytUrl = `https://www.youtube.com/watch?v=${currentVideoId}`;
    document.getElementById('preview-link').href = ytUrl;
    document.getElementById('preview-img').src = badgeUrl;

    updateCode(ytUrl);

    document.getElementById('loading').classList.remove('visible');
    document.getElementById('result-card').classList.add('visible');
  } catch (err) {
    document.getElementById('loading').classList.remove('visible');
    showError(err.message || 'Something went wrong');
  } finally {
    document.getElementById('gen-btn').disabled = false;
  }
}

function updateCode(ytUrl) {
  const absUrl = window.location.origin + badgeUrl;
  let code = '';
  if (currentTab === 'markdown') {
    code = `[![YouTube video](${absUrl})](${ytUrl})`;
  } else if (currentTab === 'html') {
    code = `<a href="${ytUrl}" target="_blank">\n  <img src="${absUrl}" alt="YouTube video" />\n</a>`;
  } else {
    code = absUrl;
  }
  document.getElementById('code-output').textContent = code;
}

function setTab(tab, btn) {
  currentTab = tab;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  if (currentVideoId) {
    const ytUrl = `https://www.youtube.com/watch?v=${currentVideoId}`;
    updateCode(ytUrl);
  }
}

function copyCode() {
  const code = document.getElementById('code-output').textContent;
  navigator.clipboard.writeText(code).then(() => {
    const btn = document.getElementById('copy-btn');
    btn.textContent = '✓ Copied';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = 'Copy';
      btn.classList.remove('copied');
    }, 2000);
  });
}
