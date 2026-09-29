import type { GradableEntity } from '../constants/entities';

export interface Entity {
  id: string;
  name: GradableEntity;
  originalIndex: number;
}

export interface GridPosition {
  x: number; // 0-4 (common to rare)
  y: number; // 0-4 (useless to useful)
}

export interface GridCell {
  position: GridPosition;
  entities: Entity[];
}

export interface DragData {
  entity: Entity;
  sourceCell?: GridPosition;
  sourceIndex?: number;
  isFromPool: boolean;
}