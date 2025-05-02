import random
import pygame
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

        # Рассчитываем границы объекта в относительных координатах
        left = (obj.x - obj.radius) / self.width
        right = (obj.x + obj.radius) / self.width
        bottom = (obj.y - obj.radius) / self.height
        top = (obj.y + obj.radius) / self.height

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
                   x: Optional[float] = None, y: Optional[float] = None) -> List[WorldObject]:
        """
        Добавляет объекты в мир

        Args:
            obj_class (type): Класс создаваемого объекта
            count (int): Количество объектов для создания
            x (Optional[float]): Фиксированная X-координата (None для случайной)
            y (Optional[float]): Фиксированная Y-координата (None для случайной)

        Returns:
            List[WorldObject]: Список созданных объектов
        """
        added = []
        for _ in range(count):
            # Генерируем координаты если не заданы
            pos_x = x if x is not None else random.uniform(0, self.width)
            pos_y = y if y is not None else random.uniform(0, self.height)

            obj = obj_class(pos_x, pos_y)
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

    def get_objects_in_area(self, x: float, y: float,
                            radius: float) -> Set[WorldObject]:
        """
        Возвращает объекты в заданной области используя пространственную сетку

        Args:
            x (float): X-координата центра области
            y (float): Y-координата центра области
            radius (float): Радиус поиска

        Returns:
            Set[WorldObject]: Найденные объекты
        """
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
                if (obj.x - x) ** 2 + (obj.y - y) ** 2 <= (radius + obj.radius) ** 2}

    def update(self):
        """Основной метод обновления состояния мира"""
        # Сенсорная фаза
        for agent in self.get_objects('agent'):
            agent.sense(self)

        # Фаза мышления
        for agent in self.get_objects('agent'):
            agent.think(steps_count=1)

        # Фаза действий
        for agent in self.get_objects('agent'):
            old_cells = self._get_object_cells(agent)
            agent.act(self)
            self._update_object_in_grid(agent, old_cells)

    def draw(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0)) -> None:
        """Отрисовка всех объектов мира"""
        grid_color = (100, 100, 100)
        for i in range(1, self.grid_size[0]):
            x = i*self.width/self.grid_size[0] + offset[0]
            pygame.draw.line(surface, grid_color, (x, 0 + offset[1]), (x, self.height + offset[1]), 1)
        for i in range(1, self.grid_size[1]):
            y = i*self.height/self.grid_size[1] + offset[1]
            pygame.draw.line(surface, grid_color, (0 + offset[0], y), (self.width + offset[0], y), 1)

        for obj in self.get_objects():
            obj.draw(surface, offset)