<template>
  <div class="tier-grid-container">
    <div class="grid-layout">
      <!-- Top Y-axis label -->
      <div class="y-label-top">Useful</div>

      <!-- Left X-axis label -->
      <div class="x-label-left">Beginner</div>

      <!-- Left tier indicators (vertical) -->
      <div class="tier-bar-left">
        <div class="tier-indicator">S</div>
        <div class="tier-indicator">A</div>
        <div class="tier-indicator">B</div>
        <div class="tier-indicator">C</div>
        <div class="tier-indicator">D</div>
      </div>

      <!-- The actual grid -->
      <div class="tier-grid">
        <GridCell
          v-for="cell in gridCells"
          :key="`${cell.position.x}-${cell.position.y}`"
          :position="cell.position"
          :entities="cell.entities"
          @drop="handleCellDrop"
          @entity-drag-start="handleEntityDragStart"
          @reorder="handleReorder"
        />
      </div>

      <!-- Right X-axis label -->
      <div class="x-label-right">Expert</div>

      <!-- Bottom tier indicators (horizontal) -->
      <div class="tier-bar-bottom">
        <div class="tier-indicator">D</div>
        <div class="tier-indicator">C</div>
        <div class="tier-indicator">B</div>
        <div class="tier-indicator">A</div>
        <div class="tier-indicator">S</div>
      </div>

      <!-- Bottom Y-axis label -->
      <div class="y-label-bottom">Useless</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import GridCell from "./GridCell.vue";
import type { Entity, GridCell as GridCellType, GridPosition } from "../types";

const GRID_SIZE = 5;
const STORAGE_KEY = "tier-list-grid-state";

// Initialize grid with empty cells
const gridState = ref<GridCellType[]>([]);

const initializeEmptyGrid = () => {
  const newGrid: GridCellType[] = [];
  for (let y = 0; y < GRID_SIZE; y++) {
    for (let x = 0; x < GRID_SIZE; x++) {
      newGrid.push({
        position: { x, y },
        entities: [],
      });
    }
  }
  return newGrid;
};

// Load from localStorage on mount
onMounted(() => {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      const parsedState = JSON.parse(saved);
      gridState.value = parsedState;
    } catch (error) {
      console.error("Failed to parse saved state:", error);
      gridState.value = initializeEmptyGrid();
    }
  } else {
    gridState.value = initializeEmptyGrid();
  }
});

// Save to localStorage whenever grid state changes
watch(
  gridState,
  (newState) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newState));
  },
  { deep: true }
);

const gridCells = computed(() => gridState.value);

const emit = defineEmits<{
  entityMoved: [
    data: { entity: Entity; from: GridPosition | null; to: GridPosition }
  ];
}>();

const handleCellDrop = ({
  position,
  dragData,
}: {
  position: GridPosition;
  dragData: any;
}) => {
  const targetCell = gridState.value.find(
    (cell) => cell.position.x === position.x && cell.position.y === position.y
  );

  if (!targetCell) return;

  // If entity is from another cell
  if (dragData.sourceCell && !dragData.isFromPool) {
    const sourceCell = gridState.value.find(
      (cell) =>
        cell.position.x === dragData.sourceCell.x &&
        cell.position.y === dragData.sourceCell.y
    );

    if (sourceCell) {
      // Remove from source cell
      const entityIndex = sourceCell.entities.findIndex(
        (e) => e.id === dragData.entity.id
      );
      if (entityIndex > -1) {
        sourceCell.entities.splice(entityIndex, 1);
      }
    }
  }

  // Add to target cell
  if (dragData.targetIndex !== undefined) {
    targetCell.entities.splice(dragData.targetIndex, 0, dragData.entity);
  } else {
    targetCell.entities.push(dragData.entity);
  }

  emit("entityMoved", {
    entity: dragData.entity,
    from: dragData.sourceCell || null,
    to: position,
  });
};

const handleEntityDragStart = (_: {
  entity: Entity;
  position: GridPosition;
  index: number;
}) => {
  // Add visual feedback if needed
};

const handleReorder = ({
  position,
  fromIndex,
  toIndex,
}: {
  position: GridPosition;
  fromIndex: number;
  toIndex: number;
}) => {
  const cell = gridState.value.find(
    (c) => c.position.x === position.x && c.position.y === position.y
  );

  if (!cell) return;

  const [movedEntity] = cell.entities.splice(fromIndex, 1);
  cell.entities.splice(toIndex, 0, movedEntity);
};

// Expose method to add entity from pool
defineExpose({
  addEntityToGrid: (entity: Entity, position?: GridPosition) => {
    const targetPosition = position || { x: 2, y: 2 }; // Default to center
    const targetCell = gridState.value.find(
      (cell) =>
        cell.position.x === targetPosition.x &&
        cell.position.y === targetPosition.y
    );

    if (targetCell) {
      targetCell.entities.push(entity);
    }
  },

  removeEntityFromGrid: (entityId: string) => {
    for (const cell of gridState.value) {
      const index = cell.entities.findIndex((e) => e.id === entityId);
      if (index > -1) {
        cell.entities.splice(index, 1);
        break;
      }
    }
  },

  resetGrid: () => {
    gridState.value = initializeEmptyGrid();
    localStorage.removeItem(STORAGE_KEY);
  },
});
</script>

<style scoped>
.tier-grid-container {
  padding: var(--spacing-md);
  display: flex;
  justify-content: center;
  align-items: center;
}

.grid-layout {
  display: grid;
  grid-template-columns: auto 33px minmax(auto, 1048px) auto;
  grid-template-rows: auto 600px 30px auto;
  gap: 0;
  column-gap: 2px;
  align-items: stretch;
  justify-items: stretch;
  width: fit-content;
  margin: 0 auto;
  position: relative;
}

/* Y-axis labels */
.y-label-top {
  grid-column: 3;
  grid-row: 1;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: #50fa7b; /* Bright green - positive */
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 4px;
  text-align: center;
  align-self: end;
  justify-self: center;
}

.y-label-bottom {
  grid-column: 3;
  grid-row: 4;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: #6272a4; /* Gray - negative */
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 4px;
  opacity: 0.7;
  text-align: center;
  align-self: start;
  justify-self: center;
}

/* X-axis labels */
.x-label-left {
  grid-column: 1;
  grid-row: 2;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: #6272a4; /* Gray - basic */
  text-transform: uppercase;
  letter-spacing: 1px;
  writing-mode: horizontal-tb;
  margin-right: 8px;
  opacity: 0.7;
  align-self: center;
  justify-self: end;
}

.x-label-right {
  grid-column: 4;
  grid-row: 2;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: #f1fa8c; /* Bright yellow - advanced */
  text-transform: uppercase;
  letter-spacing: 1px;
  writing-mode: horizontal-tb;
  margin-left: 8px;
  align-self: center;
  justify-self: start;
}

/* Tier bars */
.tier-bar-left {
  grid-column: 2;
  grid-row: 2;
  display: grid;
  grid-template-rows: repeat(5, 1fr);
  gap: 2px;
  height: 600px;
  width: 33px;
  padding: 0;
  margin: 0;
}

.tier-bar-bottom {
  grid-column: 3;
  grid-row: 3;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 2px;
  width: 1048px;
  height: 30px;
}

.tier-bar-left .tier-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(139, 148, 170, 0.1);
  border: 1px solid rgba(139, 148, 170, 0.3);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-sm);
  font-weight: 700;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
}

.tier-bar-bottom .tier-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(139, 148, 170, 0.1);
  border: 1px solid rgba(139, 148, 170, 0.3);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-sm);
  font-weight: 700;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  width: 100%;
  height: 100%;
}

/* Color code the tier indicators */
.tier-bar-left .tier-indicator:nth-child(1),
.tier-bar-bottom .tier-indicator:nth-child(5) {
  color: #ffb86c; /* S tier - Orange */
  border-color: #ffb86c;
  background-color: rgba(255, 184, 108, 0.1);
}

.tier-bar-left .tier-indicator:nth-child(2),
.tier-bar-bottom .tier-indicator:nth-child(4) {
  color: #50fa7b; /* A tier - Green */
  border-color: #50fa7b;
  background-color: rgba(80, 250, 123, 0.1);
}

.tier-bar-left .tier-indicator:nth-child(3),
.tier-bar-bottom .tier-indicator:nth-child(3) {
  color: #bd93f9; /* B tier - Purple */
  border-color: #bd93f9;
  background-color: rgba(189, 147, 249, 0.1);
}

.tier-bar-left .tier-indicator:nth-child(4),
.tier-bar-bottom .tier-indicator:nth-child(2) {
  color: #ff79c6; /* C tier - Pink */
  border-color: #ff79c6;
  background-color: rgba(255, 121, 198, 0.1);
}

.tier-bar-left .tier-indicator:nth-child(5),
.tier-bar-bottom .tier-indicator:nth-child(1) {
  color: #6272a4; /* D tier - Gray */
  border-color: #6272a4;
  background-color: rgba(98, 114, 164, 0.1);
}

.tier-grid {
  grid-column: 3;
  grid-row: 2;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  grid-template-rows: repeat(5, 1fr);
  gap: 2px;
  width: 1048px;
  height: 600px;
  margin: 0;
  padding: 0;
}

/* Visual indicators for axes - removed as they're misaligned */
</style>
