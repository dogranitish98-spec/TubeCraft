(function(){
  'use strict';
  function boot(){
    var app=document.getElementById('app');
    if(!app || app.dataset.tcShell==='1') return !!app;
    var legacy=app.querySelector('.max-w-4xl');
    if(!legacy) return false;
    app.dataset.tcShell='1';

    var shell=document.createElement('div'); shell.className='tc-shell';
    var top=document.createElement('header'); top.className='tc-top';
    top.innerHTML='<div class="tc-brand"><div class="tc-mark">▶</div><div><b>TubeCraft<em>Studio</em></b><small>AI VIDEO WORKSPACE</small></div></div><div class="tc-search"><span>⌕</span><input aria-label="Search projects, scripts, or tools" placeholder="Search projects, scripts, or tools…"><kbd>Ctrl K</kbd></div><div class="tc-health"><i></i><span>Studio ready</span></div>';

    var side=document.createElement('aside'); side.className='tc-side';
    side.innerHTML='<nav class="tc-nav" aria-label="Primary navigation"><button data-tab="create" class="tc-active"><span class="ico">✦</span>Studio</button><button data-tab="list"><span class="ico">▤</span>Jobs</button><button data-tab="gallery"><span class="ico">▦</span>Library</button><button data-tab="simple"><span class="ico">⚡</span>Quick Create</button><div class="tc-sep"></div><a class="tc-nav" style="color:#7d8ba0;text-decoration:none;padding:9px 12px;font-size:11px" href="https://video.lichuanyang.top/guides/prompt-tips" target="_blank" rel="noopener">? Guides</a></nav><div class="tc-provider"><div><span class="tc-dot"></span><strong>Agnes Engine</strong></div><p>Generation provider · API tasks · FFmpeg pipeline</p></div>';

    var main=document.createElement('main'); main.className='tc-main';
    var hero=document.createElement('section'); hero.className='tc-hero';
    hero.innerHTML='<div><div class="eyebrow">LONG-FORM VIDEO WORKSPACE</div><h1>From script to finished video.</h1><p>Plan scenes, generate with Agnes, monitor every job, and keep the production workflow in one focused workspace.</p><div class="actions"><button class="tc-primary" data-hero-tab="create">Create new video →</button><button class="tc-secondary" data-hero-tab="list">View jobs</button></div></div><div class="tc-stats"><div><b>5–10 min</b><span>Long-form ready</span></div><div><b>16:9 / 9:16</b><span>Output formats</span></div><div><b>Resume-safe</b><span>Checkpointed jobs</span></div></div>';
    var content=document.createElement('div'); content.className='tc-content';
    legacy.parentNode.insertBefore(shell,legacy);
    shell.appendChild(top); shell.appendChild(side); shell.appendChild(main); main.appendChild(hero);
    var bar=document.createElement('div'); bar.className='tc-viewbar'; bar.innerHTML='<button class="tc-active" data-tab="create">✦ Create</button><button data-tab="list">▤ Jobs</button><button data-tab="gallery">▦ Library</button><button data-tab="simple">⚡ Quick</button>';
    main.appendChild(bar); main.appendChild(content); content.appendChild(legacy);

    var mobile=document.createElement('nav'); mobile.className='tc-mobile'; mobile.innerHTML='<button class="tc-active" data-tab="create"><span>✦</span>Create</button><button data-tab="list"><span>▤</span>Jobs</button><button data-tab="gallery"><span>▦</span>Library</button><button data-tab="simple"><span>⚡</span>Quick</button>'; shell.appendChild(mobile);

    function clickTab(tab){
      var target=legacy.querySelector('button');
      var buttons=[].slice.call(legacy.querySelectorAll('button'));
      var text={create:['Create','创作'],list:['Task','任务'],gallery:['Gallery','图库'],simple:['Simple','简单']};
      var hints=text[tab]||text.create;
      var found=buttons.find(function(b){ return hints.some(function(h){return (b.textContent||'').toLowerCase().indexOf(h.toLowerCase())>=0;}); });
      if(found) found.click();
      document.querySelectorAll('[data-tab]').forEach(function(b){ b.classList.toggle('tc-active',b.getAttribute('data-tab')===tab); });
    }
    shell.querySelectorAll('[data-tab]').forEach(function(b){ b.addEventListener('click',function(){clickTab(b.getAttribute('data-tab'));}); });
    shell.querySelectorAll('[data-hero-tab]').forEach(function(b){ b.addEventListener('click',function(){clickTab(b.getAttribute('data-hero-tab'));}); });
    return true;
  }
  var tries=0; var timer=setInterval(function(){ if(boot() || ++tries>80) clearInterval(timer); },125);
  if(document.readyState!=='loading') boot(); else document.addEventListener('DOMContentLoaded',boot,{once:true});
})();
