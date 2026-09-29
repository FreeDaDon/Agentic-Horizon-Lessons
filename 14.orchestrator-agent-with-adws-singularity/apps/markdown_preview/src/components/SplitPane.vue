<script setup lang="ts">
import { ref, computed } from 'vue'
import { useStorage, useEventListener } from '@vueuse/core'

const props = defineProps<{
  initialRatio?: number
  minRatio?: number
  maxRatio?: number
}>()

const STORAGE_KEY = 'markdown-preview-split-ratio'

const splitRatio = useStorage(STORAGE_KEY, props.initialRatio ?? 0.5)
const isDragging = ref(false)
const containerRef = ref<HTMLElement | null>(null)
const currentPointerX = ref(0)
const currentPointerY = ref(0)

// Detect mobile layout for responsive sizing
const isMobile = ref(window.innerWidth <= 768)

// Update mobile state on resize
useEventListener(window, 'resize', () => {
  isMobile.value = window.innerWidth <= 768
})

const leftStyle = computed(() => {
  if (isMobile.value) {
    return {
      width: '100%',
      height: `calc(${splitRatio.value * 100}% - 3px)`
    }
  }
  return {
    width: `calc(${splitRatio.value * 100}% - 3px)`
  }
})

const rightStyle = computed(() => {
  if (isMobile.value) {
    return {
      width: '100%',
      height: `calc(${(1 - splitRatio.value) * 100}% - 3px)`
    }
  }
  return {
    width: `calc(${(1 - splitRatio.value) * 100}% - 3px)`
  }
})

const startDrag = (event: MouseEvent | TouchEvent) => {
  isDragging.value = true
  updatePointerPosition(event)
}

const stopDrag = () => {
  isDragging.value = false
}

const updatePointerPosition = (event: MouseEvent | TouchEvent) => {
  if ('touches' in event && event.touches.length > 0) {
    currentPointerX.value = event.touches[0].clientX
    currentPointerY.value = event.touches[0].clientY
  } else if ('clientX' in event) {
    currentPointerX.value = event.clientX
    currentPointerY.value = event.clientY
  }
}

const handleMove = (event: MouseEvent | TouchEvent) => {
  if (!isDragging.value || !containerRef.value) return

  updatePointerPosition(event)
  const rect = containerRef.value.getBoundingClientRect()

  let newRatio: number
  if (isMobile.value) {
    // Vertical split - use Y position
    newRatio = (currentPointerY.value - rect.top) / rect.height
  } else {
    // Horizontal split - use X position
    newRatio = (currentPointerX.value - rect.left) / rect.width
  }

  const min = props.minRatio ?? 0.2
  const max = props.maxRatio ?? 0.8

  splitRatio.value = Math.max(min, Math.min(max, newRatio))
}

// Mouse events
useEventListener(document, 'mouseup', stopDrag)
useEventListener(document, 'mousemove', handleMove)

// Touch events
useEventListener(document, 'touchend', stopDrag)
useEventListener(document, 'touchcancel', stopDrag)
useEventListener(document, 'touchmove', handleMove, { passive: false })
</script>

<template>
  <div
    ref="containerRef"
    class="split-pane"
    :class="{ dragging: isDragging }"
  >
    <div class="pane left-pane" :style="leftStyle">
      <slot name="left"></slot>
    </div>
    <div
      class="divider"
      @mousedown.prevent="startDrag"
      @touchstart.prevent="startDrag"
    >
      <div class="divider-handle"></div>
    </div>
    <div class="pane right-pane" :style="rightStyle">
      <slot name="right"></slot>
    </div>
  </div>
</template>

<style scoped>
.split-pane {
  display: flex;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.split-pane.dragging {
  cursor: col-resize;
  user-select: none;
}

.pane {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.divider {
  width: 6px;
  background-color: var(--border-color);
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background-color 0.2s;
}

.divider:hover,
.split-pane.dragging .divider {
  background-color: var(--accent-color);
}

.divider-handle {
  width: 2px;
  height: 40px;
  background-color: var(--text-muted);
  border-radius: 1px;
}

.divider:hover .divider-handle,
.split-pane.dragging .divider-handle {
  background-color: white;
}

@media (max-width: 768px) {
  .split-pane {
    flex-direction: column;
  }

  .split-pane.dragging {
    cursor: row-resize;
  }

  .divider {
    width: 100%;
    height: 6px;
    cursor: row-resize;
  }

  .divider-handle {
    width: 40px;
    height: 2px;
  }
}
</style>
