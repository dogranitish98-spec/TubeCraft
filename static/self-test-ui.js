(function () {
  'use strict';
  const state = { polling: null };

  function button(text, className, handler) {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = text;
    b.className = className || '';
    b.addEventListener('click', handler);
    return b;
  }

  async function request(url, options) {
    const response = await fetch(url, Object.assign({ cache: 'no-store' }, options || {}));
    const data = await response.json().catch(() => ({}));
    if (!response.ok && response.status !== 412) {
      throw new Error(data.message || data.detail || data.error || ('HTTP ' + response.status));
    }
    return { response, data };
  }

  function ensurePanel() {
    let panel = document.getElementById('tc-selftest');
    if (panel) return panel;
    panel = document.createElement('section');
    panel.id = 'tc-selftest';
    panel.setAttribute('aria-live', 'polite');
    panel.innerHTML = [
      '<div class="tc-selftest-head"><div><div class="tc-selftest-kicker">VERIFICATION</div><h2>Self-test & readiness</h2><p>Verify the local media pipeline, provider configuration, and real AI generation without guessing.</p></div><button class="tc-selftest-close" aria-label="Close">×</button></div>',
      '<div class="tc-selftest-actions"></div>',
      '<div class="tc-selftest-result"><div class="tc-selftest-empty">No test has run yet.</div></div>'
    ].join('');
    document.body.appendChild(panel);
    panel.querySelector('.tc-selftest-close').addEventListener('click', () => panel.remove());
    const actions = panel.querySelector('.tc-selftest-actions');
    actions.appendChild(button('Run system test', 'tc-selftest-primary', runSystemTest));
    actions.appendChild(button('Generate real test video', 'tc-selftest-secondary', runLiveTest));
    return panel;
  }

  function render(result, kind) {
    const panel = ensurePanel();
    const box = panel.querySelector('.tc-selftest-result');
    const passed = result && result.ok;
    const status = passed ? 'PASS' : (result && result.error_code === 'AGNES_API_KEY_MISSING' ? 'NOT READY' : 'FAIL');
    const rows = [];
    if (result.checks) {
      Object.keys(result.checks).forEach((key) => {
        const value = result.checks[key];
        const ok = typeof value === 'object' ? !!value.ok : !!value;
        rows.push('<div class="tc-selftest-row"><span>' + key.replace(/_/g, ' ') + '</span><strong class="' + (ok ? 'ok' : 'bad') + '">' + (ok ? 'PASS' : 'CHECK') + '</strong></div>');
      });
    }
    if (result.media_probe) {
      rows.push('<div class="tc-selftest-row"><span>generated MP4</span><strong class="' + (result.media_probe.ok ? 'ok' : 'bad') + '">' + (result.media_probe.ok ? 'VALID' : 'INVALID') + '</strong></div>');
      rows.push('<div class="tc-selftest-meta">' + (result.media_probe.duration_seconds || 0) + 's · ' + (result.media_probe.width || '?') + '×' + (result.media_probe.height || '?') + ' · ' + (result.media_probe.codec || 'unknown codec') + '</div>');
    }
    if (result.current_message) rows.push('<div class="tc-selftest-message">' + escapeHtml(result.current_message) + '</div>');
    if (result.message) rows.push('<div class="tc-selftest-message">' + escapeHtml(result.message) + '</div>');
    if (result.error) rows.push('<div class="tc-selftest-error">' + escapeHtml(result.error) + '</div>');
    box.innerHTML = '<div class="tc-selftest-status ' + (passed ? 'ok' : 'warn') + '"><span>' + status + '</span><small>' + escapeHtml(kind || '') + '</small></div>' + rows.join('');
  }

  function escapeHtml(text) {
    return String(text || '').replace(/[&<>'"]/g, (ch) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[ch]));
  }

  async function runSystemTest() {
    render({ ok: true, checks: { running: true } }, 'System test running…');
    try {
      const { data } = await request('/api/self-test');
      render(data, 'Local deterministic test');
    } catch (e) {
      render({ ok: false, error: e.message }, 'System test failed');
    }
  }

  async function runLiveTest() {
    render({ ok: true, checks: { queued: true } }, 'Submitting real Agnes generation…');
    try {
      const { response, data } = await request('/api/self-test/live', { method: 'POST' });
      if (response.status === 412 || !data.ok) {
        render(data, 'Provider not ready');
        return;
      }
      const taskId = data.task_id;
      render({ ok: true, current_message: 'Real generation task queued: ' + taskId }, 'Live generation in progress');
      pollLive(taskId);
    } catch (e) {
      render({ ok: false, error: e.message }, 'Live generation failed to start');
    }
  }

  function pollLive(taskId) {
    if (state.polling) clearInterval(state.polling);
    const started = Date.now();
    state.polling = setInterval(async function () {
      try {
        const { data } = await request('/api/self-test/live/' + encodeURIComponent(taskId));
        render(data, 'Live generation · ' + String(data.status || 'unknown'));
        if (data.final_video_exists && data.media_probe) {
          clearInterval(state.polling);
          state.polling = null;
          return;
        }
        if (String(data.status).toLowerCase() === 'failed' || Date.now() - started > 15 * 60 * 1000) {
          clearInterval(state.polling);
          state.polling = null;
        }
      } catch (e) {
        if (Date.now() - started > 15 * 60 * 1000) {
          clearInterval(state.polling);
          state.polling = null;
        }
      }
    }, 3000);
  }

  function installTrigger() {
    const existing = document.querySelectorAll('.diagnostic-btn');
    existing.forEach((b) => {
      if (b.dataset.tcSelftestBound === '1') return;
      b.dataset.tcSelftestBound = '1';
      b.textContent = 'Self-test & diagnostics';
      b.addEventListener('click', function (e) {
        e.stopImmediatePropagation();
        ensurePanel();
        runSystemTest();
      }, true);
    });

    if (!document.getElementById('tc-selftest-floating')) {
      const fab = button('Self-test', 'tc-selftest-floating', () => { ensurePanel(); runSystemTest(); });
      fab.id = 'tc-selftest-floating';
      document.body.appendChild(fab);
    }
  }

  const css = document.createElement('style');
  css.textContent = `
    #tc-selftest{position:fixed;z-index:99999;right:22px;bottom:22px;width:min(560px,calc(100vw - 28px));max-height:calc(100vh - 44px);overflow:auto;background:#0b1118;color:#edf2f7;border:1px solid rgba(148,163,184,.18);border-radius:16px;box-shadow:0 26px 90px rgba(0,0,0,.55);padding:18px;font-family:Inter,system-ui,sans-serif}
    .tc-selftest-head{display:flex;justify-content:space-between;gap:16px}.tc-selftest-kicker{font-size:9px;letter-spacing:.16em;color:#7fb0ff;font-weight:800}.tc-selftest-head h2{font-size:20px;margin:5px 0}.tc-selftest-head p{font-size:11px;line-height:1.5;color:#8491a2;margin:0;max-width:440px}.tc-selftest-close{width:32px;height:32px;border-radius:8px;border:1px solid rgba(255,255,255,.12);background:#101720;color:#9aa7b7;font-size:20px}.tc-selftest-actions{display:flex;gap:8px;margin:16px 0}.tc-selftest-actions button{min-height:38px;padding:0 12px;border-radius:8px;border:1px solid rgba(148,163,184,.16);font-weight:750;font-size:10px;cursor:pointer}.tc-selftest-primary{background:#8fb9e8;color:#071018}.tc-selftest-secondary{background:#111923;color:#d5deea}.tc-selftest-result{border:1px solid rgba(148,163,184,.14);border-radius:11px;overflow:hidden}.tc-selftest-empty,.tc-selftest-message,.tc-selftest-error,.tc-selftest-meta{padding:10px 12px;color:#8795a7;font-size:10px}.tc-selftest-status{display:flex;align-items:center;justify-content:space-between;padding:11px 12px;background:#0e151d;border-bottom:1px solid rgba(148,163,184,.12);font-size:10px;font-weight:800}.tc-selftest-status.ok{color:#43c994}.tc-selftest-status.warn{color:#e5b75a}.tc-selftest-status small{font-weight:600;color:#6e7d90}.tc-selftest-row{display:flex;justify-content:space-between;padding:9px 12px;border-bottom:1px solid rgba(148,163,184,.08);font-size:10px;text-transform:capitalize}.tc-selftest-row strong.ok{color:#43c994}.tc-selftest-row strong.bad{color:#ef7777}.tc-selftest-error{color:#ef9999;background:rgba(239,119,119,.06)}
    #tc-selftest-floating{position:fixed;z-index:9998;right:16px;bottom:16px;min-height:36px;padding:0 12px;border:1px solid rgba(127,176,255,.25);border-radius:999px;background:#0d151e;color:#dceaff;box-shadow:0 10px 30px rgba(0,0,0,.25);font-size:10px;font-weight:800}
    @media(max-width:700px){#tc-selftest{right:10px;bottom:74px;width:calc(100vw - 20px);padding:14px}.tc-selftest-actions{flex-direction:column}.tc-selftest-actions button{width:100%}#tc-selftest-floating{right:12px;bottom:74px}}
  `;
  document.head.appendChild(css);

  const boot = () => { installTrigger(); setInterval(installTrigger, 1000); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true }); else boot();
})();
