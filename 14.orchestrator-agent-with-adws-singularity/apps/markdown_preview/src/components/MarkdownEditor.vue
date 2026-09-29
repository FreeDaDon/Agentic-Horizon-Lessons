<script setup lang="ts">
import { ref, onMounted } from 'vue'

defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)

const handleInput = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
}

const handleKeydown = (event: KeyboardEvent) => {
  // Handle Tab key for indentation
  if (event.key === 'Tab') {
    event.preventDefault()
    const textarea = textareaRef.value
    if (!textarea) return

    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const value = textarea.value

    if (event.shiftKey) {
      // Shift+Tab: remove indentation
      const lineStart = value.lastIndexOf('\n', start - 1) + 1
      if (value.substring(lineStart, lineStart + 2) === '  ') {
        const newValue = value.substring(0, lineStart) + value.substring(lineStart + 2)
        emit('update:modelValue', newValue)
        setTimeout(() => {
          textarea.selectionStart = Math.max(start - 2, lineStart)
          textarea.selectionEnd = Math.max(end - 2, lineStart)
        }, 0)
      }
    } else {
      // Tab: add indentation
      const newValue = value.substring(0, start) + '  ' + value.substring(end)
      emit('update:modelValue', newValue)
      setTimeout(() => {
        textarea.selectionStart = start + 2
        textarea.selectionEnd = start + 2
      }, 0)
    }
  }
}

onMounted(() => {
  if (textareaRef.value) {
    textareaRef.value.focus()
  }
})
</script>

<template>
  <div class="editor-container">
    <div class="editor-header">
      <span class="editor-title">Markdown</span>
    </div>
    <textarea
      ref="textareaRef"
      class="editor-textarea"
      :value="modelValue"
      @input="handleInput"
      @keydown="handleKeydown"
      placeholder="Write your markdown here..."
      spellcheck="false"
    ></textarea>
  </div>
</template>

<style scoped>
.editor-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--bg-secondary);
}

.editor-header {
  padding: 0.75rem 1rem;
  background-color: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.editor-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.editor-textarea {
  flex: 1;
  width: 100%;
  padding: 1rem;
  border: none;
  resize: none;
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  font-size: 0.9rem;
  line-height: 1.6;
  tab-size: 2;
  outline: none;
}

.editor-textarea::placeholder {
  color: var(--text-muted);
}

.editor-textarea:focus {
  outline: none;
}
</style>
