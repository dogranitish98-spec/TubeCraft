<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { t } from '@/i18n'
import { useTheme } from '@/composables/useTheme'
import { useToast } from '@/composables/useToast'
import { useConfig } from '@/composables/useConfig'
import { useVoice } from '@/composables/useVoice'
import { useTasks } from '@/composables/useTasks'
import { useNavigation } from '@/composables/useNavigation'
import { useGallery } from '@/composables/useGallery'
import { appState } from '@/store'
import ConfigPanel from '@/components/ConfigPanel.vue'
import CreatePanel from '@/components/CreatePanel.vue'
import SimplePanel from '@/components/SimplePanel.vue'
import TaskListPanel from '@/components/TaskListPanel.vue'
import GalleryPanel from '@/components/GalleryPanel.vue'
import ProgressPage from '@/components/ProgressPage.vue'
import VoicePickerModal from '@/components/VoicePickerModal.vue'
import Toast from '@/components/Toast.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import LangSwitcher from '@/components/shared/LangSwitcher.vue'

const { themeIcon, themeLabel, cycleTheme } = useTheme()
const { visible: toastVisible, message: toastMessage, type: toastType } = useToast()
const { loadModels, renderWorkspaces } = useConfig()
const { initVoiceSelector } = useVoice()
const { loadTaskList, startTaskListTimer, stopTaskListTimer } = useTasks()
const { parseHash } = useNavigation()
const { loadGallery, startGalleryTimer, stopGalleryTimer } = useGallery()

const isConfigLoaded = ref(false)
const health = ref<'online' | 'checking' | 'degraded' | 'offline'>('checking')
const healthDetail = ref('Checking backend and provider…')
const lastHealthCheck = ref('')
let healthTimer: number | undefined

function switchMainTab(tab: 'create' | 'list' | 'simple' | 'gallery') {
  appState.view = tab
  location.hash = tab === 'list' ? '#/list' : tab === 'simple' ? '#/simple' : tab === 'gallery' ? '#/gallery' : '#/create'
  if (tab === 'list') { loadTaskList(); startTaskListTimer() }
  else if (tab === 'gallery') { loadGallery(); startGalleryTimer() }
  else { stopTaskListTimer(); stopGalleryTimer() }
}


async function runSelfTest() {
  try {
    const response = await fetch('/api/self-test', { cache: 'no-store' })
    const data = await response.json()
    healthDetail.value = data.ok ? 'Local self-test passed' : (data.error || 'Self-test failed')
    await checkHealth(true)
  } catch (e) {
    health.value = 'offline'
    healthDetail.value = e instanceof Error ? e.message : 'Self-test unavailable'
  }
}

async function checkHealth(silent = false) {
  if (!silent) health.value = 'checking'
  try {
    const r = await fetch('/api/health', { cache: 'no-store' })
    const data = await r.json().catch(() => ({}))
    const ok = r.ok && (data.status === undefined || data.status === 'ok' || data.status === 'healthy')
    health.value = ok ? 'online' : 'degraded'
    healthDetail.value = ok ? 'Backend ready' : (data.message || 'Backend responded with a warning')
  } catch {
    health.value = 'offline'
    healthDetail.value = 'Backend unavailable'
  }
  lastHealthCheck.value = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  const parsed = parseHash()
  if (parsed.view === 'progress' && parsed.taskId) {
    appState.view = 'progress'
    appState.progressTaskId = parsed.taskId
    appState.currentTaskId = parsed.taskId
  } else {
    appState.view = parsed.view
    if (parsed.view === 'gallery') { loadGallery(); startGalleryTimer() }
  }

  await checkHealth()
  healthTimer = window.setInterval(() => checkHealth(true), 30000)

  try {
    const cfg = await fetch('/api/config', { cache: 'no-store' }).then((r) => r.json())
    if (cfg.api_key) appState.apiKeySource = cfg.source
    if (cfg.app_version) appState.appVersion = cfg.app_version
    await renderWorkspaces()
    if (cfg.watermark !== undefined) appState.watermarkEnabled = !!cfg.watermark.enabled
    if (cfg.agnes_domain) appState.agnesDomain = cfg.agnes_domain
    await loadModels()
    isConfigLoaded.value = true
  } catch (e) { console.error('init config load error:', e) }

  try { await initVoiceSelector() } catch (e) { console.error('init voice selector error:', e) }
  if (appState.view !== 'progress') autoReconnectRunningTask()
})

onBeforeUnmount(() => { if (healthTimer) window.clearInterval(healthTimer) })

async function autoReconnectRunningTask() {
  try {
    const d = await fetch('/api/tasks', { cache: 'no-store' }).then((r) => r.json())
    const running = (d.tasks || []).find((task: any) => task.status === 'running' || task.status === 'queued')
    if (running) {
      appState.currentTaskType = running.task_type || 'creative'
      appState.currentDirName = running.dir_name || running.task_id
      appState.progressTaskId = running.task_id
      appState.progressOrigin = 'create'
      appState.view = 'progress'
      location.hash = '#/progress/' + encodeURIComponent(running.task_id)
    }
  } catch { /* offline is handled by health state */ }
}
</script>

<template>
  <ProgressPage v-if="appState.view === 'progress'" />

  <div v-else class="studio-shell">
    <header class="studio-topbar">
      <div class="brand-lockup">
        <div class="brand-mark" aria-hidden="true">▶</div>
        <div>
          <div class="brand-name">TubeCraft<span>Studio</span></div>
          <div class="brand-sub">AI VIDEO WORKSPACE</div>
        </div>
      </div>

      <div class="global-search" role="search">
        <span class="search-icon" aria-hidden="true">⌕</span>
        <input aria-label="Search projects, scripts, or tools" placeholder="Search projects, scripts, or tools…" />
        <kbd>Ctrl K</kbd>
      </div>

      <div class="top-actions">
        <span class="health-pill" :class="`health-${health}`"><i></i>{{ health === 'online' ? 'Ready' : health === 'checking' ? 'Checking' : health === 'degraded' ? 'Degraded' : 'Offline' }}</span>
        <button class="icon-btn" :title="themeLabel" :aria-label="themeLabel" @click="cycleTheme"><span v-html="themeIcon"></span></button>
        <LangSwitcher />
      </div>
    </header>

    <aside class="studio-sidebar">
      <nav class="side-nav" aria-label="Primary navigation">
        <button class="side-item" :class="{ active: appState.view === 'create' }" @click="switchMainTab('create')"><span>✦</span> Studio</button>
        <button class="side-item" :class="{ active: appState.view === 'list' }" @click="switchMainTab('list')"><span>▤</span> Jobs</button>
        <button class="side-item" :class="{ active: appState.view === 'gallery' }" @click="switchMainTab('gallery')"><span>▦</span> Library</button>
        <button class="side-item" :class="{ active: appState.view === 'simple' }" @click="switchMainTab('simple')"><span>⚡</span> Quick Create</button>
        <div class="side-divider"></div>
        <a class="side-item" href="https://video.lichuanyang.top/guides/prompt-tips" target="_blank" rel="noopener"><span>?</span> Guides</a>
        <a class="side-item" href="https://github.com/lcy362/agnes-video-generator" target="_blank" rel="noopener"><span>↗</span> Engine</a>
      </nav>
      <div class="sidebar-footer">
        <div class="provider-card">
          <div class="provider-head"><span class="provider-dot"></span><strong>Agnes Engine</strong></div>
          <div class="provider-copy">Generation service</div>
          <div class="provider-status">{{ healthDetail }}</div>
          <button class="diagnostic-btn" @click="runSelfTest">Self-test & diagnostics</button>
        </div>
        <div class="version-row">{{ appState.appVersion || 'TubeCraft Studio' }} <span>•</span> PWA</div>
      </div>
    </aside>

    <main class="studio-main">
      <section class="hero-panel">
        <div class="hero-copy">
          <div class="eyebrow">LONG-FORM VIDEO WORKSPACE</div>
          <h1>From script to finished video.</h1>
          <p>Plan scenes, generate with Agnes, monitor every job, and keep your creative workflow in one professional workspace.</p>
          <div class="hero-actions">
            <button class="primary-cta" @click="switchMainTab('create')">Create new video <span>→</span></button>
            <button class="secondary-cta" @click="switchMainTab('list')">View jobs</button>
          </div>
        </div>
        <div class="hero-metrics">
          <div><strong>5–10 min</strong><span>Long-form ready</span></div>
          <div><strong>16:9 / 9:16</strong><span>Output formats</span></div>
          <div><strong>Checkpointed</strong><span>Resume-safe jobs</span></div>
        </div>
      </section>

      <section class="workspace-bar">
        <div class="workspace-title"><span class="status-dot" :class="`dot-${health}`"></span><div><strong>Production workspace</strong><small>{{ lastHealthCheck ? `Last checked ${lastHealthCheck}` : 'Initializing services' }}</small></div></div>
        <div class="workspace-tools"><span class="mode-chip">PWA</span><span class="mode-chip">Agnes</span><span class="mode-chip">FFmpeg</span></div>
      </section>

      <section v-if="!isConfigLoaded" class="loading-strip">Preparing models, voices and workspaces…</section>

      <div class="config-wrap"><ConfigPanel /></div>

      <section class="panel-tabs" aria-label="Workspace views">
        <button :class="{ active: appState.view === 'create' }" @click="switchMainTab('create')"><span>✦</span> Create</button>
        <button :class="{ active: appState.view === 'list' }" @click="switchMainTab('list')"><span>▤</span> Jobs</button>
        <button :class="{ active: appState.view === 'gallery' }" @click="switchMainTab('gallery')"><span>▦</span> Library</button>
        <button :class="{ active: appState.view === 'simple' }" @click="switchMainTab('simple')"><span>⚡</span> Quick</button>
      </section>

      <div class="workspace-content">
        <div v-show="appState.view === 'create'"><CreatePanel /></div>
        <div v-show="appState.view === 'simple'"><SimplePanel @go-list="switchMainTab('list')" /></div>
        <div v-show="appState.view === 'list'"><TaskListPanel /></div>
        <div v-show="appState.view === 'gallery'"><GalleryPanel /></div>
      </div>

      <section class="system-strip">
        <div><span class="status-dot dot-online"></span><strong>Backend</strong><small>{{ health === 'online' ? 'Operational' : healthDetail }}</small></div>
        <div><span class="status-dot dot-online"></span><strong>FFmpeg</strong><small>Video processing pipeline</small></div>
        <div><span class="status-dot" :class="`dot-${health}`"></span><strong>Agnes</strong><small>{{ healthDetail }}</small></div>
      </section>

      <footer class="studio-footer">TubeCraft Studio · Professional PWA workspace · <span>{{ appState.appVersion || 'Build' }}</span></footer>
    </main>

    <nav class="mobile-nav" aria-label="Mobile navigation">
      <button :class="{ active: appState.view === 'create' }" @click="switchMainTab('create')"><span>✦</span>Create</button>
      <button :class="{ active: appState.view === 'list' }" @click="switchMainTab('list')"><span>▤</span>Jobs</button>
      <button :class="{ active: appState.view === 'gallery' }" @click="switchMainTab('gallery')"><span>▦</span>Library</button>
      <button :class="{ active: appState.view === 'simple' }" @click="switchMainTab('simple')"><span>⚡</span>Quick</button>
    </nav>
  </div>

  <VoicePickerModal />
  <Toast v-if="toastVisible" :message="toastMessage" :type="toastType" />
  <ConfirmModal />
</template>
