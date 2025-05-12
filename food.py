from world_object import WorldObject
from typing import Tuple


class Food(WorldObject):
    """
    Базовый класс объекта, который можно съесть.

    Атрибуты:
        ENERGY_EFFECT (float): Влияние на энергию при потреблении
        HEALTH_EFFECT (float): Влияние на здоровье при потреблении
    """
    category = 'food'
    ENERGY_EFFECT = 0.2
    HEALTH_EFFECT = 0.0

    def __init__(self, pos: Tuple[float, float],
                 color: Tuple[int, int, int] = (0, 255, 0)):
        """
        Инициализация еды

        Args:
            pos (Tuple[float, float]): Координаты (x, y)
            color: Цвет отрисовки
        """
        super().__init__(pos, size=3, color=color)
        
    def bite(self, bite_force: float = 1.0) -> Tuple[float, float]:
        """
        Обработка укуса пищи
        
        Args:
            bite_force: Сила укуса (множитель эффекта)
            
        Returns:
            Tuple[float, float]: Кортеж (влияние на энергию, влияние на здоровье)
        """
        # Пища теряет здоровье при укусе
        self.health = 0.0
        
        # Возвращаем влияние, модифицированное силой укуса
        return self.ENERGY_EFFECT * bite_force, self.HEALTH_EFFECT * bite_force


class Poison(Food):
    """
    Класс ядовитого объекта (наследуется от Food)

    Атрибуты:
        ENERGY_EFFECT (float): Влияние на энергию при потреблении
        HEALTH_EFFECT (float): Влияние на здоровье при потреблении (предполагается отрицательным)
    """
    ENERGY_EFFECT = 0.0
    HEALTH_EFFECT = -0.1

    def __init__(self, pos: Tuple[float, float],
                 color: Tuple[int, int, int] = (128, 0, 128)):
        """
        Инициализация яда

        Args:
            pos (Tuple[float, float]): Координаты (x, y)
            color: Цвет отрисовки
        """
        super().__init__(pos, color=color)