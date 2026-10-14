'use strict';

const VIDEO_ID_RE = /^[a-zA-Z0-9_-]{11}$/;
const HEX_COLOR_RE = /^#?[0-9a-fA-F]{6}$/;

let currentVideoId = null;
let currentTab = 'markdown';
let badgeUrl = '';
let isGenerating = false;
let copyResetTimer = null;

const $ = (id) => document.getElementById(id);

/** Keep a color picker and its text field in sync. */
function syncColor(pickerId, textId) {
  const picker = $(pickerId);
  const text = $(textId);
  picker.addEventListener('input', () => { text.value = picker.value; });
  text.addEventListener('input', () => {
    if (HEX_COLOR_RE.test(text.value)) picker.value = text.value.startsWith('#') ? text.value : `#${text.value}`;
  });
}

/** Strip a leading '#' so colors can be passed as bare hex in the query string. */
function bareHex(value) {
  return String(value).replace(/^#/, '');
}

function watchUrl(videoId) {
  return `https://www.youtube.com/watch?v=${videoId}`;
}

function showError(msg) {
  const el = $('error-msg');
  el.textContent = msg;
  el.classList.add('visible');
}

function hideError() {
  $('error-msg').classList.remove('visible');
}

function setLoading(isLoading) {
  $('loading').classList.toggle('visible', isLoading);
  $('gen-btn').disabled = isLoading;
}

/** Build the /badge query string from the form. Every value is URL-encoded. */
function buildBadgeUrl(videoId) {
  const params = new URLSearchParams({
    id: videoId,
    width: $('width-input').value || '320',
    radius: $('radius-input').value || '8',
    bg: bareHex($('bg-color-text').value),
    title_color: bareHex($('title-color-text').value),
    title_opacity: $('title-opacity-input').value || '1',
    plate_color: bareHex($('plate-color-text').value),
    plate_opacity: $('plate-opacity-input').value || '0.78',
    title_position: $('title-position-input').value || 'overlay_bottom',
    border_width: $('border-width-input').value || '1',
    border_color: bareHex($('border-color-text').value),
  });
  return `/badge?${params.toString()}`;
}

async function generate() {
  // Ignore repeated submissions (button click + Enter key) while a request is running.
  if (isGenerating) return;

  const url = $('url-input').value.trim();
  if (!url) {
    showError('Please enter a YouTube URL or video ID');
    return;
  }

  isGenerating = true;
  hideError();
  $('result-card').classList.remove('visible');
  setLoading(true);

  try {
    const infoResp = await fetch(`/info?${new URLSearchParams({ url })}`);
    if (!infoResp.ok) {
      throw new Error('Could not find video. Check the URL and try again.');
    }
    const info = await infoResp.json();
    if (!VIDEO_ID_RE.test(info.id || '')) {
      throw new Error('Could not find video. Check the URL and try again.');
    }
    currentVideoId = info.id;
    badgeUrl = buildBadgeUrl(currentVideoId);

    const previewImg = $('preview-img');
    previewImg.onerror = () => {
      $('result-card').classList.remove('visible');
      showError('Could not render the badge. Try different settings.');
    };
    previewImg.src = badgeUrl;
    $('preview-link').href = watchUrl(currentVideoId);

    updateCode();

    $('result-card').classList.add('visible');
  } catch (err) {
    showError(err.message || 'Something went wrong');
  } finally {
    setLoading(false);
    isGenerating = false;
  }
}

function updateCode() {
  if (!currentVideoId) return;
  const ytUrl = watchUrl(currentVideoId);
  const absUrl = window.location.origin + badgeUrl;
  let code;
  if (currentTab === 'markdown') {
    code = `[![YouTube video](${absUrl})](${ytUrl})`;
  } else if (currentTab === 'html') {
    code = `<a href="${ytUrl}" target="_blank">\n  <img src="${absUrl}" alt="YouTube video" />\n</a>`;
  } else {
    code = absUrl;
  }
  $('code-output').textContent = code;
}

function setTab(tab, btn) {
  currentTab = tab;
  document.querySelectorAll('.tab').forEach((t) => t.classList.remove('active'));
  btn.classList.add('active');
  updateCode();
}

async function copyCode() {
  const btn = $('copy-btn');
  try {
    await navigator.clipboard.writeText($('code-output').textContent);
    btn.textContent = '✓ Copied';
    btn.classList.add('copied');
  } catch (err) {
    // Clipboard API is unavailable (e.g. non-secure context) or permission was denied.
    btn.textContent = 'Copy failed';
  }
  clearTimeout(copyResetTimer);
  copyResetTimer = setTimeout(() => {
    btn.textContent = 'Copy';
    btn.classList.remove('copied');
  }, 2000);
}

function init() {
  syncColor('bg-color-picker', 'bg-color-text');
  syncColor('title-color-picker', 'title-color-text');
  syncColor('plate-color-picker', 'plate-color-text');
  syncColor('border-color-picker', 'border-color-text');

  $('url-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') generate();
  });
  $('gen-btn').addEventListener('click', generate);
  $('copy-btn').addEventListener('click', copyCode);

  document.querySelectorAll('.tab').forEach((btn) => {
    btn.addEventListener('click', () => setTab(btn.dataset.tab, btn));
  });
}

init();
