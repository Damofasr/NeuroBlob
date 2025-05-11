from __future__ import annotations
import numpy as np
import pygame
import uuid
from typing import Tuple, Union, Set


class WorldObject:
    """
    Базовый класс для всех объектов игрового мира.

    Атрибуты:
        category (str): Категория объекта, отражающая ожидаемое поведение и способ взаимодействия (переопределяется в потомках)
        id (uuid.UUID): Уникальный идентификатор объекта
        x (float): X-координата центра
        y (float): Y-координата центра
        size (Union[float, Tuple[float, float]]): Размер объекта для круга или прямоугольника
        color (Tuple[int, int, int]): Цвет в формате RGB
    """
    category = 'worldobject'

    def __init__(self, x: float, y: float,
                 size: Union[float, Tuple[float, float]] = 1.0,
                 color: Tuple[int, int, int] = (255, 255, 255)
                 ):
        """
        Инициализация объекта

        Args:
            x: Начальная X-координата
            y: Начальная Y-координата
            size: Размер объекта. Может быть кругом или прямоугольником
            color: Цвет отрисовки
        """
        self.id = uuid.uuid4()
        self.x = x
        self.y = y
        self.size = size
        self.color = color

    def __hash__(self) -> int:
        """Хеш на основе уникального ID"""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Сравнение по ID"""
        return isinstance(other, WorldObject) and self.id == other.id

    def pre_update(self, nearest: Set[WorldObject]) -> None:
        pass

    def update(self, nearest: Set[WorldObject]) -> WorldObject:
        pass

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
                closest_x = np.clip(self.x,
                                    obj.x - obj.width / 2,
                                    obj.x + obj.width / 2)
                closest_y = np.clip(self.y,
                                    obj.y - obj.height / 2,
                                    obj.y + obj.height / 2)

                d_pos = np.array([self.x - closest_x, self.y - closest_y])
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
        return np.array([self.x, self.y])

    @position.setter
    def position(self, pos: np.ndarray) -> None:
        """Установка новой позиции"""
        self.x, self.y = pos

    def draw(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0)) -> None:
        """
        Отрисовка объекта на поверхности

        Args:
            surface: Целевая поверхность для рисования
            offset: Смещение координат (для камеры)
        """
        if self.is_circle:
            pygame.draw.circle(
                surface,
                self.color,
                (int(self.x + offset[0]), int(self.y + offset[1])),
                int(self.radius)
            )
        if self.is_rectangle:
            pygame.draw.rect(surface,
                             self.color,
                             (self.x-self.width/2, self.y-self.height/2, self.width, self.height)
                             )