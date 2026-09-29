<template>
  <div 
    class="grid-cell"
    :class="{ 
      'drag-over': isDragOver,
      'has-entities': entities.length > 0 
    }"
    :style="cellStyle"
    @dragover="handleDragOver"
    @drop="handleDrop"
    @dragleave="handleDragLeave"
  >
    <div 
      v-for="(entity, index) in entities" 
      :key="entity.id"
      class="entity-in-cell"
      :class="{ 
        'is-h1': entity.name.startsWith('#') && !entity.name.startsWith('##'),
        'is-h2': entity.name.startsWith('##'),
        'is-prompt-format': entity.name.endsWith('.md')
      }"
      :draggable="true"
      @dragstart="(e) => handleEntityDragStart(e, entity, index)"
      @dragend="handleEntityDragEnd"
      @dragover.stop="(e) => handleEntityDragOver(e, index)"
      @drop.stop="(e) => handleEntityDrop(e, index)"
    >
      {{ entity.name }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { Entity, GridPosition } from '../types';

interface Props {
  position: GridPosition;
  entities: Entity[];
}

const props = defineProps<Props>();
const emit = defineEmits<{
  drop: [data: { position: GridPosition; dragData: any }];
  entityDragStart: [data: { entity: Entity; position: GridPosition; index: number }];
  reorder: [data: { position: GridPosition; fromIndex: number; toIndex: number }];
}>();

const isDragOver = ref(false);
const isDraggingEntity = ref(false);

// Calculate background gradient based on position
const cellStyle = computed(() => {
  const x = props.position.x;
  const y = props.position.y;

  // Check if this cell is on the diagonal (tier intersection)
  // S tier: (4,0), A tier: (3,1), B tier: (2,2), C tier: (1,3), D tier: (0,4)
  const isDiagonal = x + y === 4;

  if (isDiagonal) {
    // Determine which tier this diagonal cell belongs to
    let tierColor = '';
    let tierBorderColor = '';
    let tierOpacity = 0.1;

    switch(x) {
      case 4: // S tier
        tierColor = '255, 184, 108'; // Orange
        tierBorderColor = '#ffb86c';
        break;
      case 3: // A tier
        tierColor = '80, 250, 123'; // Green
        tierBorderColor = '#50fa7b';
        break;
      case 2: // B tier
        tierColor = '189, 147, 249'; // Purple
        tierBorderColor = '#bd93f9';
        break;
      case 1: // C tier
        tierColor = '255, 121, 198'; // Pink
        tierBorderColor = '#ff79c6';
        break;
      case 0: // D tier
        tierColor = '98, 114, 164'; // Gray
        tierBorderColor = '#6272a4';
        break;
    }

    return {
      backgroundColor: `rgba(${tierColor}, ${tierOpacity})`,
      borderColor: tierBorderColor,
      borderWidth: '1.5px',
      transition: 'all 0.3s ease'
    };
  }

  // Original gradient logic for non-diagonal cells
  const usefulnessScore = (4 - y) / 4; // 1 at top, 0 at bottom
  const expertiseScore = x / 4; // 0 at left (beginner), 1 at right (expert)

  // Combined intensity with equal weighting
  const intensity = (usefulnessScore + expertiseScore) / 2;

  // Purple accent that gets stronger towards top-right
  const purpleOpacity = intensity * 0.15; // Max 15% opacity
  const borderIntensity = intensity * 0.5; // Border gets more visible

  // Special highlight for the "best" cells (top-right quadrant)
  const isTopRight = x >= 3 && y <= 1;
  const highlightBonus = isTopRight ? 0.05 : 0;

  return {
    backgroundColor: `rgba(189, 147, 249, ${purpleOpacity + highlightBonus})`,
    borderColor: `rgba(189, 147, 249, ${0.2 + borderIntensity})`,
    borderWidth: intensity > 0.5 ? '1.5px' : '1px',
    transition: 'all 0.3s ease'
  };
});

const handleDragOver = (e: DragEvent) => {
  e.preventDefault();
  isDragOver.value = true;
};

const handleDrop = (e: DragEvent) => {
  e.preventDefault();
  isDragOver.value = false;
  
  if (!e.dataTransfer) return;
  
  const dragData = JSON.parse(e.dataTransfer.getData('application/json'));
  emit('drop', { position: props.position, dragData });
};

const handleDragLeave = () => {
  isDragOver.value = false;
};

const handleEntityDragStart = (e: DragEvent, entity: Entity, index: number) => {
  if (!e.dataTransfer) return;
  
  isDraggingEntity.value = true;
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('application/json', JSON.stringify({
    entity,
    sourceCell: props.position,
    sourceIndex: index,
    isFromPool: false
  }));
  
  emit('entityDragStart', { entity, position: props.position, index });
};

const handleEntityDragEnd = () => {
  isDraggingEntity.value = false;
};

const handleEntityDragOver = (e: DragEvent, _targetIndex: number) => {
  e.preventDefault();
  e.stopPropagation();
  
  // Removed drop indicator logic to prevent visual artifacts
};

const handleEntityDrop = (e: DragEvent, targetIndex: number) => {
  e.preventDefault();
  e.stopPropagation();
  
  if (!e.dataTransfer) return;
  
  const dragData = JSON.parse(e.dataTransfer.getData('application/json'));
  
  // If dropping within the same cell, handle reordering
  if (dragData.sourceCell?.x === props.position.x && 
      dragData.sourceCell?.y === props.position.y) {
    const fromIndex = dragData.sourceIndex;
    if (fromIndex !== targetIndex) {
      emit('reorder', { 
        position: props.position, 
        fromIndex, 
        toIndex: targetIndex 
      });
    }
  } else {
    // Otherwise, handle as a normal drop at specific index
    emit('drop', { 
      position: props.position, 
      dragData: { ...dragData, targetIndex }
    });
  }
};
</script>

<style scoped>
.grid-cell {
  background-color: var(--color-grid-bg);
  border: 1px solid var(--color-grid-border);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-sm);
  min-height: 80px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  transition: all var(--transition-fast);
  position: relative;
}

.grid-cell:hover {
  background-color: var(--color-grid-hover);
  border-color: var(--color-border-hover);
  transform: scale(1.15);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  z-index: 10;
}

.grid-cell.drag-over {
  background-color: var(--color-drop-zone);
  border-color: var(--color-accent);
  border-width: 2px;
}

.entity-in-cell {
  background-color: var(--color-entity-bg);
  border: 1px solid var(--color-entity-border);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  cursor: grab;
  font-size: var(--font-size-sm);
  font-weight: 700;
  transition: all var(--transition-fast);
  user-select: none;
  position: relative;
}

.entity-in-cell.is-h1 {
  color: var(--color-text-secondary);
  background-color: rgba(189, 147, 249, 0.15);
  border-color: var(--color-text-secondary);
  font-size: calc(var(--font-size-sm) - 4px);
}

.entity-in-cell.is-h2 {
  color: var(--color-text-secondary);
  background-color: rgba(189, 147, 249, 0.15);
  border-color: var(--color-text-secondary);
  font-size: calc(var(--font-size-sm) - 4px);
}

.entity-in-cell.is-prompt-format {
  color: #8be9fd;
  background-color: rgba(139, 233, 253, 0.15);
  border-color: #8be9fd;
  font-size: calc(var(--font-size-sm) - 4px);
}

.entity-in-cell:hover {
  background-color: var(--color-entity-hover);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.entity-in-cell:active {
  cursor: grabbing;
}

/* Drop indicators removed to prevent visual artifacts */
/* .entity-in-cell.drop-above::before {
  content: '';
  position: absolute;
  top: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background-color: var(--color-accent);
}

.entity-in-cell.drop-below::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background-color: var(--color-accent);
} */
</style>