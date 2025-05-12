from __future__ import annotations
import numpy as np
import pygame
import uuid
from typing import Tuple, Union, Set, Optional


class WorldObject:
    """
    Базовый класс для всех объектов игрового мира.

    Атрибуты:
        category (str): Категория объекта, отражающая ожидаемое поведение и способ взаимодействия (переопределяется в потомках)
        id (uuid.UUID): Уникальный идентификатор объекта
        _position (np.ndarray): Координаты центра объекта [x, y]
        size (Union[float, Tuple[float, float]]): Размер объекта для круга или прямоугольника
        color (Tuple[int, int, int]): Цвет в формате RGB
        health (float): Здоровье объекта, значение от 0 до 1
        energy (float): Энергия объекта, значение от 0 до 1
    """
    category = 'worldobject'

    def __init__(self, pos: Tuple[float, float],
                 size: Union[float, Tuple[float, float]] = 1.0,
                 color: Tuple[int, int, int] = (255, 255, 255)
                 ):
        """
        Инициализация объекта

        Args:
            pos (Tuple[float, float]): Начальные координаты (x, y)
            size: Размер объекта. Может быть кругом или прямоугольником
            color: Цвет отрисовки
        """
        self.id = uuid.uuid4()
        self._position = np.array(pos, dtype=np.float32)
        self.size = size
        self.color = color
        self.health = 1.0  # Базовое здоровье для всех объектов
        self.energy = 1.0  # Базовая энергия для всех объектов

    def __hash__(self) -> int:
        """Хеш на основе уникального ID"""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Сравнение по ID"""
        return isinstance(other, WorldObject) and self.id == other.id

    def pre_update(self, nearest: Set[WorldObject]) -> None:
        """
        Предварительная обработка объекта перед основным обновлением
        
        Args:
            nearest (Set[WorldObject]): Множество ближайших объектов
        """
        pass

    def update(self, nearest: Set[WorldObject]) -> Optional[WorldObject]:
        """
        Основной метод обновления состояния объекта
        
        Args:
            nearest (Set[WorldObject]): Множество ближайших объектов
            
        Returns:
            Optional[WorldObject]: Объект, с которым произошло взаимодействие (если было)
        """
        pass
        
    def _apply_effect(self, energy_delta: float = 0.0, health_delta: float = 0.0) -> None:
        """
        Применяет изменения энергии и здоровья с учетом их взаимосвязи
        
        Правила:
        1. Если energy_delta отрицательный и превышает текущую энергию,
           недостаток вычитается из здоровья
        2. Энергия и здоровье всегда остаются в диапазоне [0, 1]
        3. Здоровье никогда не переливается в энергию
        
        Args:
            energy_delta (float): Изменение энергии (+ добавление, - расход), по умолчанию 0
            health_delta (float): Изменение здоровья (+ восстановление, - урон), по умолчанию 0
        """
        # Обработка энергии
        if energy_delta < 0 and abs(energy_delta) > self.energy:
            # Недостаток энергии вычитается из здоровья
            health_deficit = abs(energy_delta) - self.energy
            health_delta -= health_deficit
            self.energy = 0.0
        else:
            # Нормальное изменение энергии
            self.energy = max(0.0, min(1.0, self.energy + energy_delta))
        
        # Обработка здоровья (независимо от энергии)
        self.health = max(0.0, min(1.0, self.health + health_delta))
    
    def bite(self, bite_force: float = 1.0) -> Tuple[float, float]:
        """
        Базовый метод обработки укуса объекта
        
        Args:
            bite_force: Сила укуса (множитель эффекта)
            
        Returns:
            Tuple[float, float]: Кортеж (влияние на энергию, влияние на здоровье)
        """
        # Базовая реализация не дает никакого эффекта
        return 0.0, 0.0

    @property
    def grid_radius(self) -> float:
        """Обратная совместимость: возвращает радиус для сетки"""
        return self.radius*2

    @property
    def radius(self) -> float:
        """Обратная совместимость: возвращает радиус для круга или вычисляет для прямоугольника"""
        if self.is_circle:
            return self.size
        else:
            # Для прямоугольника возвращаем половину диагонали как "условный радиус"
            return np.sqrt((self.width/2)**2 + (self.height/2)**2)

    @property
    def is_circle(self) -> bool:
        """Проверка, является ли объект кругом"""
        return isinstance(self.size, (int, float))

    @property
    def is_rectangle(self) -> bool:
        """Проверка, является ли объект прямоугольником"""
        return isinstance(self.size, tuple) and len(self.size) == 2

    @property
    def width(self) -> float:
        """Ширина прямоугольника"""
        return self.size[0] if self.is_rectangle else 2 * self.size

    @property
    def height(self) -> float:
        """Высота прямоугольника"""
        return self.size[1] if self.is_rectangle else 2 * self.size

    def collide(self, obj: WorldObject):
        """
        Обработка столкновения с другим объектом
        
        Корректирует позиции объектов в зависимости от их типов (круг/прямоугольник)
        для предотвращения наложения друг на друга.
        
        Args:
            obj (WorldObject): Объект, с которым проверяется столкновение
        """
        match (self.is_circle, obj.is_circle):
            case (True, True):
                # Столкновение двух кругов: оба подвижны
                d_pos = self.position - obj.position
                distance = np.hypot(d_pos[0], d_pos[1])
                min_distance = self.radius + obj.radius

                if distance < min_distance and distance != 0:
                    # Корректируем оба объекта
                    correction = d_pos / distance * (min_distance - distance) / 2
                    self.position += correction
                    obj.position -= correction

            case (True, False):
                # Круг и неподвижный прямоугольник: корректируем только круг
                x, y = self._position
                obj_x, obj_y = obj._position
                
                closest_x = np.clip(x,
                                   obj_x - obj.width / 2,
                                   obj_x + obj.width / 2)
                closest_y = np.clip(y,
                                   obj_y - obj.height / 2,
                                   obj_y + obj.height / 2)

                d_pos = np.array([x - closest_x, y - closest_y])
                distance = np.hypot(d_pos[0], d_pos[1])

                if distance < self.radius and distance != 0:
                    # Корректируем только круг
                    correction = d_pos / distance * (self.radius - distance)
                    self.position += correction

            case (False, True):
                # Неподвижный прямоугольник и круг: делегируем предыдущему случаю
                obj.collide(self)

            case (False, False):
                # Столкновение двух неподвижных прямоугольников: игнорируем
                pass

    @property
    def position(self) -> np.ndarray:
        """Текущая позиция в виде numpy массива [x, y]"""
        return self._position

    @position.setter
    def position(self, pos: Union[np.ndarray, Tuple[float, float]]) -> None:
        """Установка новой позиции"""
        self._position = np.array(pos, dtype=np.float32)
        
    @property
    def x(self) -> float:
        """X-координата объекта (только для чтения)"""
        return self._position[0]
        
    @property 
    def y(self) -> float:
        """Y-координата объекта (только для чтения)"""
        return self._position[1]

    def draw(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0)) -> None:
        """
        Отрисовка объекта на поверхности

        Args:
            surface: Целевая поверхность для рисования
            offset: Смещение координат (для камеры)
        """
        x, y = self._position
        if self.is_circle:
            pygame.draw.circle(
                surface,
                self.color,
                (int(x + offset[0]), int(y + offset[1])),
                int(self.radius)
            )
        if self.is_rectangle:
            rect = (
                int(x - self.width/2) + offset[0],
                int(y - self.height/2) + offset[1],
                int(self.width),
                int(self.height)
            )
            pygame.draw.rect(surface, self.color, rect)