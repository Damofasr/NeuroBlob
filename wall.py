from world_object import WorldObject


class Wall(WorldObject):
    category = "wall"

    def __init__(self, x: float, y: float, width: float, height: float):
        super().__init__(x, y, width = width, height = height, radius=0)
