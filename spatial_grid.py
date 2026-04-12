from dataclasses import dataclass, field
from typing import Dict, Set, Tuple

@dataclass
class SpatialGrid:
    width: int
    height: int
    cell_size: int
    cells: Dict[Tuple[int, int], Set[int]] = field(default_factory=dict)

    def __post_init__(self):
        cols = self.width // self.cell_size + 1
        rows = self.height // self.cell_size + 1
        self.cells = {(x, y): set() for x in range(cols) for y in range(rows)}
        self.cols = cols
        self.rows = rows

    def _cell_coords(self, x, y):
        return (int(x // self.cell_size), int(y // self.cell_size))

    def add(self, entity_id, x, y):
        cell = self._cell_coords(x, y)
        self.cells.setdefault(cell, set()).add(entity_id)

    def remove(self, entity_id, x, y):
        cell = self._cell_coords(x, y)
        if cell in self.cells:
            self.cells[cell].discard(entity_id)

    def move(self, entity_id, old_x, old_y, new_x, new_y):
        self.remove(entity_id, old_x, old_y)
        self.add(entity_id, new_x, new_y)

    def query(self, x, y, radius):
        # Вернуть все entity_id в радиусе (реализация по необходимости)
        result = set()
        min_cx = max(0, int((x - radius) // self.cell_size))
        max_cx = min(self.cols - 1, int((x + radius) // self.cell_size))
        min_cy = max(0, int((y - radius) // self.cell_size))
        max_cy = min(self.rows - 1, int((y + radius) // self.cell_size))
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                result.update(self.cells.get((cx, cy), set()))
        return result

import esper
from components import Position

class GridUpdateSystem(esper.Processor):
    def __init__(self, grid: SpatialGrid):
        super().__init__()
        self.grid = grid
        self.last_positions = {}

    def process(self):
        for ent, pos in self.world.get_component(Position):
            old_pos = self.last_positions.get(ent)
            if old_pos is None:
                self.grid.add(ent, pos.x, pos.y)
            elif (old_pos[0], old_pos[1]) != (pos.x, pos.y):
                self.grid.move(ent, old_pos[0], old_pos[1], pos.x, pos.y)
            self.last_positions[ent] = (pos.x, pos.y)