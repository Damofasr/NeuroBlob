import random
import pygame
from wall import Wall
from typing import Dict, Set, Tuple, List, Optional
from world_object import WorldObject


class World:
    """
    Основной класс, представляющий игровой мир.

    Отвечает за:
    - Хранение и управление всеми объектами в мире
    - Обработку пространственного разбиения для оптимизации
    - Координацию взаимодействий между объектами

    Атрибуты:
        width (int): Ширина мира в пикселях
        height (int): Высота мира в пикселях
        objects_by_category (Dict[str, Set[WorldObject]]): Объекты, сгруппированные по категориям
        grid_size (Tuple[int, int]): Размеры сетки пространственного разбиения (колонки, строки)
        grid (Dict[Tuple[int, int], Set[WorldObject]]): Пространственная сетка для оптимизации поиска
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.objects_by_category: Dict[str, Set[WorldObject]] = {}

        # Параметры пространственного разбиения
        self.grid_size = (8, 6)  # (columns, rows)
        self.grid: Dict[Tuple[int, int], Set[WorldObject]] = self._create_empty_grid()

        wall_width = 2
        self._add_wall((0, self.height/2), (wall_width, self.height))
        self._add_wall((self.width, self.height/2), (wall_width, self.height))
        self._add_wall((self.width/2, 0), (self.width, wall_width))
        self._add_wall((self.width/2, self.height), (self.width, wall_width))

    def _add_wall(self, pos, size):

        obj = Wall(pos, size=size)
        category = obj.category

        # Добавляем в категорию
        if category not in self.objects_by_category:
            self.objects_by_category[category] = set()
        self.objects_by_category[category].add(obj)

        # Добавляем в сетку
        cells = self._get_object_cells(obj)
        self._add_to_grid(obj, cells)

    def _create_empty_grid(self) -> Dict[Tuple[int, int], Set[WorldObject]]:
        """Инициализирует пустую сетку"""
        return {(x, y): set() for x in range(self.grid_size[0])
                for y in range(self.grid_size[1])}

    def _get_object_cells(self, obj: WorldObject) -> Set[Tuple[int, int]]:
        """
        Вычисляет все ячейки сетки, которые пересекает объект

        Args:
            obj (WorldObject): Объект для проверки

        Returns:
            Set[Tuple[int, int]]: Множество координат ячеек
        """
        if not hasattr(obj, 'radius'):
            return set()

        x, y = obj.position

        # Рассчитываем границы объекта в относительных координатах
        left = (x - obj.width/2) / self.width
        right = (x + obj.width/2) / self.width
        bottom = (y - obj.height/2) / self.height
        top = (y + obj.height/2) / self.height

        # Преобразуем в индексы сетки
        min_col = max(0, int(left * self.grid_size[0]))
        max_col = min(self.grid_size[0] - 1, int(right * self.grid_size[0]))
        min_row = max(0, int(bottom * self.grid_size[1]))
        max_row = min(self.grid_size[1] - 1, int(top * self.grid_size[1]))

        return {(c, r) for c in range(min_col, max_col + 1)
                for r in range(min_row, max_row + 1)}

    def _add_to_grid(self, obj: WorldObject, cells: Set[Tuple[int, int]]) -> None:
        """Добавляет объект в указанные ячейки сетки"""
        for cell in cells:
            self.grid[cell].add(obj)

    def _remove_from_grid(self, obj: WorldObject, cells: Set[Tuple[int, int]]) -> None:
        """Удаляет объект из указанных ячеек сетки"""
        for cell in cells:
            self.grid[cell].discard(obj)

    def _update_object_in_grid(self, obj: WorldObject,
                              old_cells: Optional[Set[Tuple[int, int]]] = None) -> None:
        """Обновляет положение объекта в сетке (только для перемещений)"""
        new_cells = self._get_object_cells(obj)

        if old_cells is not None:
            self._remove_from_grid(obj, old_cells - new_cells)
        self._add_to_grid(obj, new_cells - (old_cells or set()))

    def add_object(self, obj_class: type, count: int = 1,
                   pos: Optional[Tuple[float, float]] = None) -> List[WorldObject]:
        """
        Добавляет объекты в мир

        Args:
            obj_class (type): Класс создаваемого объекта
            count (int): Количество объектов для создания
            pos (Optional[Tuple[float, float]]): Фиксированные координаты (x, y) (None для случайной)

        Returns:
            List[WorldObject]: Список созданных объектов
        """
        added = []
        for _ in range(count):
            # Генерируем координаты если не заданы
            obj_pos = pos if pos is not None else (random.uniform(0, self.width), random.uniform(0, self.height))

            obj = obj_class(obj_pos)
            category = obj.category

            # Добавляем в категорию
            if category not in self.objects_by_category:
                self.objects_by_category[category] = set()
            self.objects_by_category[category].add(obj)

            # Добавляем в сетку
            cells = self._get_object_cells(obj)
            self._add_to_grid(obj, cells)
            added.append(obj)

        return added

    def remove_object(self, obj: WorldObject):
        """
        Удаляет объект из мира

        Args:
            obj (WorldObject): Объект для удаления
        """
        # Удаляем из всех ячеек сетки
        cells = self._get_object_cells(obj)
        self._remove_from_grid(obj, cells)

        if obj.category in self.objects_by_category:
            self.objects_by_category[obj.category].discard(obj)

    def get_objects(self, category: Optional[str] = None) -> Set[WorldObject]:
        """
        Возвращает объекты по категории или все объекты

        Args:
            category (Optional[str]): Категория для фильтрации

        Returns:
            Set[WorldObject]: Множество объектов
        """
        if category is None:
            return set().union(*self.objects_by_category.values())
        return self.objects_by_category.get(category, set()).copy()

    def get_objects_in_area(self, pos: Tuple[float, float],
                            radius: float) -> Set[WorldObject]:
        """
        Возвращает объекты в заданной области используя пространственную сетку

        Args:
            pos (Tuple[float, float]): Координаты центра области (x, y)
            radius (float): Радиус поиска

        Returns:
            Set[WorldObject]: Найденные объекты
        """
        x, y = pos
        # Рассчитываем границы поиска
        left = max(0.0, (x - radius) / self.width)
        right = min(1.0, (x + radius) / self.width)
        bottom = max(0.0, (y - radius) / self.height)
        top = min(1.0, (y + radius) / self.height)

        # Определяем затронутые ячейки
        min_col = int(left * self.grid_size[0])
        max_col = int(right * self.grid_size[0])
        min_row = int(bottom * self.grid_size[1])
        max_row = int(top * self.grid_size[1])

        candidates = set()
        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                candidates.update(self.grid.get((col, row), set()))

        # Точная проверка расстояния
        radius_sq = radius ** 2
        return {obj for obj in candidates
                if sum((obj.position - pos) ** 2) <= (radius + obj.radius) ** 2}

    def update(self):
        """Основной метод обновления состояния мира"""

        # Фаза действий
        for obj in self.get_objects('agent'):
            old_cells = self._get_object_cells(obj)
            nearests = self.get_objects_in_area(obj.position, obj.grid_radius)
            interacted_object = obj.update(nearests)

            if interacted_object:
                self.remove_object(interacted_object)
                self.add_object(type(interacted_object))

            closest = self.get_objects_in_area(obj.position, obj.radius)
            for close in closest:
                old_cells = self._get_object_cells(close)
                obj.collide(close)
                self._update_object_in_grid(close, old_cells)

            self._update_object_in_grid(obj, old_cells)

    def draw(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0)) -> None:
        """Отрисовка всех объектов мира"""
        grid_color = (100, 100, 100)
        for i in range(0, self.grid_size[0]+1):
            x = min(i*self.width/self.grid_size[0] + offset[0], self.width-1)
            pygame.draw.line(surface, grid_color, (x, 0 + offset[1]), (x, self.height + offset[1]), 1)
        for i in range(0, self.grid_size[1]+1):
            y = min(i*self.height/self.grid_size[1] + offset[1], self.height-1)
            pygame.draw.line(surface, grid_color, (0 + offset[0], y), (self.width + offset[0], y), 1)

        for obj in self.get_objects():
            obj.draw(surface, offset)