import numpy as np
import pygame
import uuid
from typing import Tuple, Optional


class WorldObject:
    """
    Базовый класс для всех объектов игрового мира.

    Атрибуты:
        category (str): Категория объекта, отражающая ожидаемое поведение и способ взаимодействия (переопределяется в потомках)
        id (uuid.UUID): Уникальный идентификатор объекта
        x (float): X-координата центра
        y (float): Y-координата центра
        radius (float): Радиус объекта для коллизий
        color (Tuple[int, int, int]): Цвет в формате RGB
    """
    category = 'worldobject'

    def __init__(self, x: float, y: float,
                 radius: float = 1,
                 color: Tuple[int, int, int] = (255, 255, 255)):
        """
        Инициализация объекта

        Args:
            x: Начальная X-координата
            y: Начальная Y-координата
            radius: Радиус объекта
            color: Цвет отрисовки
        """
        self.id = uuid.uuid4()
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color

    def __hash__(self) -> int:
        """Хеш на основе уникального ID"""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Сравнение по ID"""
        return isinstance(other, WorldObject) and self.id == other.id

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
        pygame.draw.circle(
            surface,
            self.color,
            (int(self.x + offset[0]), int(self.y + offset[1])),
            int(self.radius)
        )