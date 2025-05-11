from world_object import WorldObject
from typing import Tuple


class Wall(WorldObject):
    category = "wall"

    def __init__(self, x: float, y: float, size: Tuple[float, float]):
        super().__init__(x, y, size = size, color = (127, 127, 127))
