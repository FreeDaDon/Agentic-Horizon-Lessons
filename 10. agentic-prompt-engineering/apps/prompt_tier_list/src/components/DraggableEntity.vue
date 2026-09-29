<template>
  <div
    class="draggable-entity"
    :class="{ 
      'is-dragging': isDragging,
      'is-h1': entity.name.startsWith('#') && !entity.name.startsWith('##'),
      'is-h2': entity.name.startsWith('##'),
      'is-prompt-format': entity.name.endsWith('.md')
    }"
    :draggable="!isPlaced"
    @dragstart="handleDragStart"
    @dragend="handleDragEnd"
  >
    {{ entity.name }}
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { Entity } from '../types';

interface Props {
  entity: Entity;
  isPlaced?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isPlaced: false
});

const emit = defineEmits<{
  dragStart: [entity: Entity];
  dragEnd: [];
}>();

const isDragging = ref(false);

const handleDragStart = (e: DragEvent) => {
  if (props.isPlaced) return;
  
  isDragging.value = true;
  
  if (!e.dataTransfer) return;
  
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('application/json', JSON.stringify({
    entity: props.entity,
    sourceCell: null,
    sourceIndex: null,
    isFromPool: true
  }));
  
  // Add visual feedback
  const target = e.target as HTMLElement;
  target.classList.add('dragging');
  
  emit('dragStart', props.entity);
};

const handleDragEnd = (e: DragEvent) => {
  isDragging.value = false;
  
  // Remove visual feedback
  const target = e.target as HTMLElement;
  target.classList.remove('dragging');
  
  emit('dragEnd');
};
</script>

<style scoped>
.draggable-entity {
  background-color: var(--color-entity-bg);
  border: 1px solid var(--color-entity-border);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-xs) var(--spacing-sm);
  cursor: grab;
  transition: all var(--transition-fast);
  user-select: none;
  font-size: var(--font-size-sm);
  font-weight: 700;
  display: inline-block;
  position: relative;
}

.draggable-entity.is-h1 {
  color: var(--color-text-secondary);
  background-color: rgba(189, 147, 249, 0.15);
  border-color: var(--color-text-secondary);
  font-size: calc(var(--font-size-sm) - 4px);
}

.draggable-entity.is-h2 {
  color: var(--color-text-secondary);
  background-color: rgba(189, 147, 249, 0.15);
  border-color: var(--color-text-secondary);
  font-size: calc(var(--font-size-sm) - 4px);
}

.draggable-entity.is-prompt-format {
  color: #8be9fd;
  background-color: rgba(139, 233, 253, 0.15);
  border-color: #8be9fd;
  font-size: calc(var(--font-size-sm) - 4px);
}

.draggable-entity:not([draggable="false"]):hover {
  background-color: var(--color-entity-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.draggable-entity:active:not([draggable="false"]) {
  cursor: grabbing;
}

.draggable-entity.is-dragging {
  opacity: 0.5;
}

.draggable-entity[draggable="false"] {
  cursor: default;
  opacity: 0.5;
}

.draggable-entity.dragging {
  opacity: 0.4;
}
</style>