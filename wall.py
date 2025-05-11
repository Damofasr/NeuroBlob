from world_object import WorldObject
from typing import Tuple


class Wall(WorldObject):
    category = "wall"

    def __init__(self, pos: Tuple[float, float], size: Tuple[float, float]):
        """
        Инициализация стены
        
        Args:
            pos (Tuple[float, float]): Координаты центра стены (x, y)
            size (Tuple[float, float]): Размеры стены (ширина, высота)
        """
        super().__init__(pos, size=size, color=(127, 127, 127))
