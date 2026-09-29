<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import SplitPane from './components/SplitPane.vue'
import MarkdownEditor from './components/MarkdownEditor.vue'
import MarkdownPreview from './components/MarkdownPreview.vue'
import CopyButton from './components/CopyButton.vue'
import { useMarkdown } from './composables/useMarkdown'

const { markdown, renderedHtml } = useMarkdown()

// Toast notification state for keyboard shortcut feedback
const toastMessage = ref('')
const toastType = ref<'success' | 'error'>('success')
const showToast = ref(false)

const displayToast = (message: string, type: 'success' | 'error') => {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 2000)
}

// Keyboard shortcut: Cmd/Ctrl+S to copy HTML
const handleKeydown = async (event: KeyboardEvent) => {
  if ((event.metaKey || event.ctrlKey) && event.key === 's') {
    event.preventDefault()
    try {
      await navigator.clipboard.writeText(renderedHtml.value)
      displayToast('HTML copied to clipboard!', 'success')
    } catch {
      displayToast('Failed to copy HTML to clipboard', 'error')
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="app">
    <header class="app-header">
      <h1 class="app-title">Markdown Preview</h1>
      <div class="app-actions">
        <CopyButton :text="renderedHtml" />
      </div>
    </header>
    <main class="app-main">
      <SplitPane :initial-ratio="0.5" :min-ratio="0.2" :max-ratio="0.8">
        <template #left>
          <MarkdownEditor v-model="markdown" />
        </template>
        <template #right>
          <MarkdownPreview :html="renderedHtml" />
        </template>
      </SplitPane>
    </main>
    <Transition name="toast">
      <div
        v-if="showToast"
        class="toast"
        :class="toastType"
      >
        {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  background-color: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.app-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.app-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.app-main {
  flex: 1;
  overflow: hidden;
}

@media (max-width: 768px) {
  .app-header {
    padding: 0.5rem 1rem;
  }

  .app-title {
    font-size: 1rem;
  }
}

.toast {
  position: fixed;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.toast.success {
  background-color: var(--success-color);
}

.toast.error {
  background-color: var(--error-color);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(1rem);
}
</style>
