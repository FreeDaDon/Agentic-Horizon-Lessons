<script setup lang="ts">
import { ref } from 'vue'
import { useClipboard } from '@vueuse/core'

const props = defineProps<{
  text: string
}>()

const { copy, isSupported } = useClipboard()
const copied = ref(false)
const error = ref(false)

const handleCopy = async () => {
  if (!isSupported.value) {
    error.value = true
    setTimeout(() => {
      error.value = false
    }, 2000)
    return
  }

  try {
    await copy(props.text)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    error.value = true
    setTimeout(() => {
      error.value = false
    }, 2000)
  }
}
</script>

<template>
  <button
    class="copy-button"
    :class="{ copied, error }"
    @click="handleCopy"
    :disabled="!text"
    :title="copied ? 'Copied!' : error ? 'Failed to copy' : 'Copy HTML to clipboard'"
  >
    <svg
      v-if="copied"
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
    <svg
      v-else-if="error"
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <line x1="18" y1="6" x2="6" y2="18"></line>
      <line x1="6" y1="6" x2="18" y2="18"></line>
    </svg>
    <svg
      v-else
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
    </svg>
    <span class="button-text">{{ copied ? 'Copied!' : error ? 'Error' : 'Copy HTML' }}</span>
  </button>
</template>

<style scoped>
.copy-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.copy-button:hover:not(:disabled) {
  background-color: var(--bg-tertiary);
  border-color: var(--accent-color);
}

.copy-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.copy-button.copied {
  background-color: var(--success-color);
  border-color: var(--success-color);
  color: white;
}

.copy-button.error {
  background-color: var(--error-color);
  border-color: var(--error-color);
  color: white;
}

.button-text {
  white-space: nowrap;
}

@media (max-width: 480px) {
  .button-text {
    display: none;
  }

  .copy-button {
    padding: 0.5rem;
  }
}
</style>
