<template>
  <div class="entity-pool">
    <div class="pool-header">
      <h3 class="pool-title">Sections & Formats</h3>
      <button
        class="reset-button"
        @click="$emit('reset')"
        title="Reset all entities"
      >
        ×
      </button>
    </div>
    <div
      class="entities-container"
      :class="{ 'drag-over': isDragOver }"
      @dragover="handleDragOver"
      @drop="handleDrop"
      @dragleave="handleDragLeave"
    >
      <DraggableEntity
        v-for="entity in availableEntities"
        :key="entity.id"
        :entity="entity"
        :is-placed="isEntityPlaced(entity.id)"
        @drag-start="handleDragStart"
        @drag-end="handleDragEnd"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import DraggableEntity from "./DraggableEntity.vue";
import { GRADABLE_ENTITIES } from "../constants/entities";
import type { Entity } from "../types";

// Create entities from constants
const allEntities = ref<Entity[]>(
  GRADABLE_ENTITIES.map((name, index) => ({
    id: `entity-${index}`,
    name,
    originalIndex: index,
  }))
);

const placedEntityIds = ref<Set<string>>(new Set());
const isDragOver = ref(false);

const availableEntities = computed(() => allEntities.value);

const isEntityPlaced = (entityId: string) => {
  return placedEntityIds.value.has(entityId);
};

const emit = defineEmits<{
  entityDropped: [entity: Entity];
  reset: [];
}>();

const handleDragStart = (_entity: Entity) => {
  // Could add visual feedback to the pool
};

const handleDragEnd = () => {
  // Clean up any visual feedback
};

const handleDragOver = (e: DragEvent) => {
  e.preventDefault();
  isDragOver.value = true;
};

const handleDrop = (e: DragEvent) => {
  e.preventDefault();
  isDragOver.value = false;

  if (!e.dataTransfer) return;

  try {
    const dragData = JSON.parse(e.dataTransfer.getData("application/json"));

    // Only accept entities that are coming from the grid (not from pool itself)
    if (!dragData.isFromPool && dragData.entity) {
      emit("entityDropped", dragData.entity);
      markEntityAsAvailable(dragData.entity.id);
    }
  } catch (error) {
    console.error("Failed to parse drag data:", error);
  }
};

const handleDragLeave = () => {
  isDragOver.value = false;
};

// Method to mark entity as placed (called from parent)
const markEntityAsPlaced = (entityId: string) => {
  placedEntityIds.value.add(entityId);
};

// Method to mark entity as available (called from parent)
const markEntityAsAvailable = (entityId: string) => {
  placedEntityIds.value.delete(entityId);
};

// Method to reset all placed entities
const resetAllEntities = () => {
  placedEntityIds.value.clear();
};

defineExpose({
  markEntityAsPlaced,
  markEntityAsAvailable,
  resetAllEntities,
  allEntities: availableEntities,
});
</script>

<style scoped>
.entity-pool {
  padding: var(--spacing-md);
  background-color: var(--color-bg-secondary);
  border-radius: var(--border-radius-md);
  margin: var(--spacing-md) auto;
  max-width: 1270px;
  width: calc(100% - var(--spacing-md) * 2);
}

.pool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.pool-title {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.reset-button {
  background-color: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xl);
  font-weight: 300;
  width: 32px;
  height: 32px;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  padding: 0;
}

.reset-button:hover {
  background-color: var(--color-accent);
  color: var(--color-text-primary);
  border-color: var(--color-accent);
  transform: scale(1.1);
}

.entities-container {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-sm);
  min-height: 60px;
  align-items: center;
}

/* Visual feedback for drag over */
.entities-container.drag-over {
  background-color: var(--color-drop-zone);
  border: 2px dashed var(--color-accent);
}
</style>
