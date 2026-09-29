import { ref } from 'vue';
import type { Entity, GridPosition, DragData } from '../types';

export function useDragAndDrop() {
  const draggedEntity = ref<Entity | null>(null);
  const draggedFrom = ref<GridPosition | null>(null);
  const isDragging = ref(false);
  const dropTarget = ref<HTMLElement | null>(null);

  const startDrag = (entity: Entity, from?: GridPosition) => {
    draggedEntity.value = entity;
    draggedFrom.value = from || null;
    isDragging.value = true;
  };

  const endDrag = () => {
    draggedEntity.value = null;
    draggedFrom.value = null;
    isDragging.value = false;
    dropTarget.value = null;
  };

  const setDropTarget = (element: HTMLElement | null) => {
    dropTarget.value = element;
  };

  const createDragData = (
    entity: Entity,
    sourceCell?: GridPosition,
    sourceIndex?: number,
    isFromPool: boolean = false
  ): DragData => {
    return {
      entity,
      sourceCell,
      sourceIndex,
      isFromPool
    };
  };

  const parseDragData = (dataTransfer: DataTransfer): DragData | null => {
    try {
      const data = dataTransfer.getData('application/json');
      return JSON.parse(data) as DragData;
    } catch (error) {
      console.error('Failed to parse drag data:', error);
      return null;
    }
  };

  const handleDragStart = (
    e: DragEvent,
    entity: Entity,
    sourceCell?: GridPosition,
    sourceIndex?: number,
    isFromPool: boolean = false
  ) => {
    if (!e.dataTransfer) return;

    e.dataTransfer.effectAllowed = 'move';
    const dragData = createDragData(entity, sourceCell, sourceIndex, isFromPool);
    e.dataTransfer.setData('application/json', JSON.stringify(dragData));
    
    startDrag(entity, sourceCell);
    
    // Add visual feedback
    const target = e.target as HTMLElement;
    setTimeout(() => {
      target.classList.add('dragging');
    }, 0);
  };

  const handleDragEnd = (e: DragEvent) => {
    const target = e.target as HTMLElement;
    target.classList.remove('dragging');
    endDrag();
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = 'move';
    }
  };

  const handleDrop = (
    e: DragEvent,
    onDrop: (dragData: DragData) => void
  ) => {
    e.preventDefault();
    
    if (!e.dataTransfer) return;
    
    const dragData = parseDragData(e.dataTransfer);
    if (dragData) {
      onDrop(dragData);
    }
    
    endDrag();
  };

  // Helper to check if we can drop at a location
  const canDrop = (
    dragData: DragData | null,
    targetPosition: GridPosition,
    currentCellEntities: Entity[]
  ): boolean => {
    if (!dragData) return false;
    
    // Can always drop in empty cells
    if (currentCellEntities.length === 0) return true;
    
    // Check if dropping the same entity in the same cell
    if (dragData.sourceCell?.x === targetPosition.x && 
        dragData.sourceCell?.y === targetPosition.y) {
      // Allow reordering within the same cell
      return true;
    }
    
    // Allow dropping from pool or different cells
    return true;
  };

  // Visual feedback helpers
  const addDragOverClass = (element: HTMLElement) => {
    element.classList.add('drag-over');
  };

  const removeDragOverClass = (element: HTMLElement) => {
    element.classList.remove('drag-over');
  };

  const addDropIndicator = (element: HTMLElement, position: 'above' | 'below') => {
    element.classList.remove('drop-above', 'drop-below');
    element.classList.add(`drop-${position}`);
  };

  const removeDropIndicator = (element: HTMLElement) => {
    element.classList.remove('drop-above', 'drop-below');
  };

  return {
    // State
    draggedEntity,
    draggedFrom,
    isDragging,
    dropTarget,
    
    // Methods
    startDrag,
    endDrag,
    setDropTarget,
    createDragData,
    parseDragData,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDrop,
    canDrop,
    
    // Visual feedback helpers
    addDragOverClass,
    removeDragOverClass,
    addDropIndicator,
    removeDropIndicator
  };
}