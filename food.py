from world_object import WorldObject
from typing import Tuple


class Food(WorldObject):
    """
    Базовый класс объекта, который можно съесть.

    Атрибуты:
        ENERGY_COST (float): Влияние на энергию при потреблении
        HEALTH_COST (float): Влияние на здоровье при потреблении
    """
    category = 'food'
    ENERGY_COST = 0.2
    HEALTH_COST = 0.0

    def __init__(self, x: float, y: float,
                 color: Tuple[int, int, int] = (0, 255, 0)):
        """
        Инициализация еды

        Args:
            x: X-координата
            y: Y-координата
            color: Цвет отрисовки
        """
        super().__init__(x, y, radius=3, color=color)


class Poison(Food):
    """
    Класс ядовитого объекта (наследуется от Food)

    Атрибуты:
        ENERGY_COST (float): Влияние на энергию при потреблении
        HEALTH_COST (float): Влияние на здоровье при потреблении (предполагается отрицательным)
    """
    ENERGY_COST = 0.0
    HEALTH_COST = -0.1

    def __init__(self, x: float, y: float,
                 color: Tuple[int, int, int] = (128, 0, 128)):
        """
        Инициализация яда

        Args:
            x: X-координата
            y: Y-координата
            color: Цвет отрисовки
        """
        super().__init__(x, y, color=color)