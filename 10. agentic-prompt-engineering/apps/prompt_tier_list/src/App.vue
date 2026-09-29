<template>
  <div id="app">
    <header class="app-header">
      <h1 class="app-title">Agentic Prompt Tier List</h1>
    </header>
    
    <main class="app-main">
      <TierGrid 
        ref="tierGridRef"
        @entity-moved="handleEntityMoved"
      />
      
      <EntityPool 
        ref="entityPoolRef"
        @entity-dropped="handleEntityDroppedToPool"
        @reset="handleReset"
      />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import TierGrid from './components/TierGrid.vue';
import EntityPool from './components/EntityPool.vue';
import type { Entity, GridPosition } from './types';

const tierGridRef = ref<InstanceType<typeof TierGrid>>();
const entityPoolRef = ref<InstanceType<typeof EntityPool>>();

const handleEntityMoved = ({ entity, from, to }: {
  entity: Entity;
  from: GridPosition | null;
  to: GridPosition;
}) => {
  // If entity moved from pool to grid
  if (!from && entityPoolRef.value) {
    entityPoolRef.value.markEntityAsPlaced(entity.id);
  }
  
  // Log movement for debugging
  console.log(`Entity "${entity.name}" moved from`, from, 'to', to);
};

const handleEntityDroppedToPool = (entity: Entity) => {
  // Remove entity from grid
  if (tierGridRef.value) {
    tierGridRef.value.removeEntityFromGrid(entity.id);
  }
  
  // Mark entity as available in pool
  if (entityPoolRef.value) {
    entityPoolRef.value.markEntityAsAvailable(entity.id);
  }
  
  console.log(`Entity "${entity.name}" returned to pool`);
};

const handleReset = () => {
  // Reset the grid to empty state
  if (tierGridRef.value) {
    tierGridRef.value.resetGrid();
  }
  
  // Reset all entities in pool to available state
  if (entityPoolRef.value) {
    entityPoolRef.value.resetAllEntities();
  }
  
  console.log('Grid and pool reset to initial state');
};

// Setup global drag and drop handlers
onMounted(() => {
  // Sync placed entities from grid state to pool
  setTimeout(() => {
    if (tierGridRef.value && entityPoolRef.value) {
      // Get all entities from the grid
      const gridState = localStorage.getItem('tier-list-grid-state');
      if (gridState) {
        try {
          const parsedState = JSON.parse(gridState);
          const placedIds = new Set<string>();
          
          // Collect all entity IDs that are in the grid
          parsedState.forEach((cell: any) => {
            cell.entities.forEach((entity: any) => {
              placedIds.add(entity.id);
            });
          });
          
          // Mark these entities as placed in the pool
          placedIds.forEach(id => {
            entityPoolRef.value?.markEntityAsPlaced(id);
          });
        } catch (error) {
          console.error('Failed to sync placed entities:', error);
        }
      }
    }
  }, 100); // Small delay to ensure components are mounted
  
  // Prevent default browser drag and drop behavior
  document.addEventListener('dragover', (e) => {
    if (e.target === document.body) {
      e.preventDefault();
    }
  });
  
  document.addEventListener('drop', (e) => {
    if (e.target === document.body) {
      e.preventDefault();
    }
  });
});
</script>

<style>
/* Import global styles */
@import './assets/global.css';

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--color-bg-primary);
}

.app-header {
  padding: var(--spacing-md) var(--spacing-lg);
  text-align: center;
}

.app-title {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text-primary);
  text-transform: uppercase;
  letter-spacing: 2px;
  margin: 0;
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding-bottom: var(--spacing-xl);
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .app-title {
    font-size: var(--font-size-xl);
    letter-spacing: 2px;
  }
}

@media (max-width: 768px) {
  .app-header {
    padding: var(--spacing-lg) var(--spacing-md);
  }
  
  .app-title {
    font-size: var(--font-size-lg);
    letter-spacing: 1px;
  }
}
</style>
