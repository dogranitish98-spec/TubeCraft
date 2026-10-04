<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>
}

const deferred = ref<BeforeInstallPromptEvent | null>(null)
const visible = ref(false)
const iosInstall = ref(false)
const standalone = ref(false)
const online = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)
const updateAvailable = ref(false)
let registration: ServiceWorkerRegistration | null = null

function isStandaloneMode() {
  return window.matchMedia('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
}

function onBeforeInstallPrompt(event: Event) {
  event.preventDefault()
  deferred.value = event as BeforeInstallPromptEvent
  visible.value = !standalone.value
}

function onAppInstalled() {
  deferred.value = null
  visible.value = false
  standalone.value = true
}

function onOnline() { online.value = true }
function onOffline() { online.value = false }

async function install() {
  if (!deferred.value) return
  await deferred.value.prompt()
  await deferred.value.userChoice
  deferred.value = null
  visible.value = false
}

function reloadForUpdate() {
  registration?.waiting?.postMessage({ type: 'SKIP_WAITING' })
}

function onControllerChange() {
  window.location.reload()
}

onMounted(async () => {
  standalone.value = isStandaloneMode()
  iosInstall.value = /iphone|ipad|ipod/i.test(navigator.userAgent) && !standalone.value
  window.addEventListener('beforeinstallprompt', onBeforeInstallPrompt)
  window.addEventListener('appinstalled', onAppInstalled)
  window.addEventListener('online', onOnline)
  window.addEventListener('offline', onOffline)

  if ('serviceWorker' in navigator) {
    try {
      registration = await navigator.serviceWorker.ready
      if (registration.waiting) updateAvailable.value = true
      registration.addEventListener('updatefound', () => {
        const worker = registration?.installing
        if (!worker) return
        worker.addEventListener('statechange', () => {
          if (worker.state === 'installed' && navigator.serviceWorker.controller) {
            updateAvailable.value = true
          }
        })
      })
      navigator.serviceWorker.addEventListener('controllerchange', onControllerChange)
    } catch {
      // PWA remains usable when service workers are unavailable.
    }
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeinstallprompt', onBeforeInstallPrompt)
  window.removeEventListener('appinstalled', onAppInstalled)
  window.removeEventListener('online', onOnline)
  window.removeEventListener('offline', onOffline)
  navigator.serviceWorker?.removeEventListener('controllerchange', onControllerChange)
})
</script>

<template>
  <div class="mb-5 space-y-2" aria-live="polite">
    <div v-if="!online" class="rounded-xl border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-xs text-amber-200">
      Offline: your TubeCraft shell and saved drafts remain available. Generation resumes when the Agnes engine reconnects.
    </div>

    <div v-if="iosInstall" class="rounded-xl border border-accent/25 bg-accent/10 px-3 py-3 text-xs text-ink-2">
      <strong class="text-accent">Install TubeCraft:</strong> tap Share in Safari, then choose <strong>Add to Home Screen</strong>.
    </div>

    <button
      v-if="visible && !iosInstall && !standalone"
      type="button"
      class="w-full min-h-11 rounded-xl border border-accent/30 bg-accent/10 px-4 py-3 text-sm font-semibold text-accent hover:bg-accent/15"
      @click="install"
    >
      Install TubeCraft on this device
    </button>

    <button
      v-if="updateAvailable"
      type="button"
      class="w-full min-h-11 rounded-xl border border-rule bg-paper-2 px-4 py-3 text-sm font-semibold text-ink-2 hover:border-accent/40"
      @click="reloadForUpdate"
    >
      Update TubeCraft to the latest version
    </button>
  </div>
</template>
