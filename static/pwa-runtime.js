(() => {
  'use strict';

  const ACCESS_TOKEN_KEY = 'tubecraft_access_token';
  const isStandalone = () =>
    window.matchMedia?.('(display-mode: standalone)').matches ||
    navigator.standalone === true;
  const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  const sameOriginApi = input => {
    try {
      const url = input instanceof Request ? new URL(input.url) : new URL(String(input), location.href);
      return url.origin === location.origin && url.pathname.startsWith('/api/');
    } catch { return false; }
  };

  function installAuthFetchPatch() {
    if (!window.fetch || window.__tubecraftAuthFetchPatched) return;
    const original = window.fetch.bind(window);
    window.__tubecraftOriginalFetch = original;
    window.fetch = (input, init) => {
      try {
        if (!sameOriginApi(input)) return original(input, init);
        const token = localStorage.getItem(ACCESS_TOKEN_KEY) || '';
        if (!token) return original(input, init);
        const headers = new Headers(input instanceof Request ? input.headers : (init?.headers || undefined));
        if (!headers.has('X-TubeCraft-Access-Token')) headers.set('X-TubeCraft-Access-Token', token);
        if (input instanceof Request) return original(new Request(input, { headers }), init);
        return original(input, { ...(init || {}), headers });
      } catch {
        return original(input, init);
      }
    };
    window.__tubecraftAuthFetchPatched = true;
  }

  function createBanner(id, message, actionText, action) {
    if (document.getElementById(id)) return;
    const el = document.createElement('div');
    el.id = id;
    el.setAttribute('role', 'status');
    el.style.cssText = [
      'position:fixed','left:max(12px,env(safe-area-inset-left))','right:max(12px,env(safe-area-inset-right))',
      'bottom:max(12px,env(safe-area-inset-bottom))','z-index:99999','display:flex','align-items:center','gap:12px',
      'padding:12px 14px','border:1px solid rgba(255,255,255,.14)','border-radius:14px',
      'background:#121722','color:#f4f7fb','box-shadow:0 12px 36px rgba(0,0,0,.35)',
      'font:500 14px/1.35 system-ui,sans-serif'
    ].join(';');
    const text = document.createElement('div');
    text.textContent = message;
    text.style.flex = '1';
    const btn = document.createElement('button');
    btn.textContent = actionText;
    btn.style.cssText = 'min-height:44px;border:1px solid rgba(255,255,255,.18);border-radius:10px;padding:8px 12px;background:#8fb9e8;color:#071018;font-weight:700;cursor:pointer';
    btn.onclick = () => action(el);
    el.append(text, btn);
    document.body.appendChild(el);
  }

  function showConnectionState() {
    const update = () => {
      const id = 'tubecraft-connection-banner';
      const existing = document.getElementById(id);
      if (!navigator.onLine) {
        if (!existing) {
          createBanner(id, 'Offline mode: TubeCraft is available, but new generation requests need the engine connection.', 'Dismiss', el => el.remove());
        }
      } else {
        existing?.remove();
      }
    };
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    update();
  }

  async function ensureAccessToken() {
    const rawFetch = window.__tubecraftOriginalFetch || window.fetch.bind(window);
    try {
      const statusResp = await rawFetch('/api/auth/status', { cache: 'no-store' });
      if (!statusResp.ok) return;
      const status = await statusResp.json();
      if (!status.required) return;
      const existing = localStorage.getItem(ACCESS_TOKEN_KEY) || '';
      const check = await rawFetch('/api/auth/check', {
        headers: existing ? { 'X-TubeCraft-Access-Token': existing } : {},
        cache: 'no-store'
      });
      if (check.ok) return;

      const gate = document.createElement('div');
      gate.id = 'tubecraft-access-gate';
      gate.style.cssText = 'position:fixed;inset:0;z-index:100000;display:grid;place-items:center;background:#07090c;color:#f4f7fb;padding:20px;font-family:system-ui,sans-serif';
      const card = document.createElement('form');
      card.style.cssText = 'width:min(440px,100%);padding:24px;border:1px solid rgba(255,255,255,.12);border-radius:18px;background:#0d1117;box-shadow:0 20px 60px rgba(0,0,0,.4)';
      card.innerHTML = '<h1 style="font-size:24px;font-weight:800;margin:0 0 8px">TubeCraft Studio</h1><p style="opacity:.75;font-size:14px;line-height:1.5;margin:0 0 18px">This PWA is protected. Enter the local access token configured on the TubeCraft engine.</p><label style="display:block;font-size:13px;font-weight:700;margin-bottom:8px" for="tubecraft-token">Access token</label><input id="tubecraft-token" type="password" autocomplete="current-password" style="width:100%;box-sizing:border-box;min-height:46px;padding:10px 12px;border-radius:10px;border:1px solid rgba(255,255,255,.14);background:#141a22;color:#fff;margin-bottom:12px"/><button type="submit" style="width:100%;min-height:46px;border:0;border-radius:10px;background:#8fb9e8;color:#071018;font-weight:800">Connect</button><div id="tubecraft-token-error" style="margin-top:10px;color:#ef7777;font-size:13px;min-height:18px"></div>';
      gate.appendChild(card);
      document.body.appendChild(gate);
      card.addEventListener('submit', async event => {
        event.preventDefault();
        const token = card.querySelector('#tubecraft-token').value.trim();
        const error = card.querySelector('#tubecraft-token-error');
        if (!token) { error.textContent = 'Enter the access token.'; return; }
        const verify = await rawFetch('/api/auth/check', { headers: { 'X-TubeCraft-Access-Token': token }, cache: 'no-store' }).catch(() => null);
        if (!verify?.ok) { error.textContent = 'Token rejected. Check the engine configuration.'; return; }
        localStorage.setItem(ACCESS_TOKEN_KEY, token);
        gate.remove();
        location.reload();
      });
    } catch {
      // Local engine may be offline; leave the normal offline/PWA UI visible.
    }
  }

  function registerPwa() {
    if (!('serviceWorker' in navigator)) return;
    navigator.serviceWorker.register('/sw.js', { scope: '/' }).then(reg => {
      const showUpdate = () => {
        if (!reg.waiting) return;
        createBanner('tubecraft-update-banner', 'A new TubeCraft version is ready.', 'Update', el => {
          reg.waiting?.postMessage({ type: 'SKIP_WAITING' });
          el.remove();
        });
      };
      showUpdate();
      reg.addEventListener('updatefound', () => {
        const worker = reg.installing;
        if (!worker) return;
        worker.addEventListener('statechange', () => {
          if (worker.state === 'installed' && navigator.serviceWorker.controller) showUpdate();
        });
      });
      navigator.serviceWorker.addEventListener('controllerchange', () => window.location.reload());
    }).catch(() => {});
  }

  function setupInstallPrompt() {
    if (isStandalone()) return;
    let deferred = null;
    window.addEventListener('beforeinstallprompt', event => {
      event.preventDefault();
      deferred = event;
      createBanner('tubecraft-install-banner', 'Install TubeCraft for an app-like experience.', 'Install', async el => {
        if (!deferred) return;
        await deferred.prompt();
        await deferred.userChoice;
        deferred = null;
        el.remove();
      });
    });
    window.addEventListener('appinstalled', () => {
      document.getElementById('tubecraft-install-banner')?.remove();
      deferred = null;
    });
    if (isIOS) {
      createBanner('tubecraft-ios-install-banner', 'Install TubeCraft in Safari: Share → Add to Home Screen.', 'Got it', el => el.remove());
    }
  }

  const start = () => {
    installAuthFetchPatch();
    registerPwa();
    setupInstallPrompt();
    showConnectionState();
    void ensureAccessToken();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
