import math
import random
import pygame
import pygame.gfxdraw
from typing import Optional, Tuple, List, Set
from world import World
from world_object import WorldObject
from neuroblob import NeuroBlob


class Agent(WorldObject):
    """
    Класс, представляющий агента в симуляции.

    Отвечает за:
    - Восприятие окружающей среды через зрительные лучи
    - Принятие решений с помощью нейросети
    - Движение и взаимодействие с объектами мира
    - Управление энергией и здоровьем

    Атрибуты:
        category (str): Категория объекта ('agent')
        VISION_RAYS (int): Количество зрительных лучей
        VISION_DISTANCE (float): Дальность зрения
        VISION_ANGLE (float): Угол обзора в радианах
        LEARNING (bool): Флаг включения обучения
    """

    category = 'agent'
    LEARNING = False

    VISION_RAYS = 11
    VISION_DISTANCE = 100.0
    VISION_ANGLE = 120 * (math.pi / 180)
    CONSUME_LEVEL = 0.0

    # Динамика энергии и здоровья
    PASSIVE_COST = 0.0001
    MOVEMENT_COST_FACTOR = 0.001
    BITING_COST = 0.005
    REGEN_COST = PASSIVE_COST

    def __init__(self, pos: Tuple[float, float]):
        """
        Инициализация агента

        Args:
            pos (Tuple[float, float]): Начальные координаты (x, y)
        """
        super().__init__(pos, size=6, color=(0, 100, 255))
        self.angle: float = random.uniform(0, 2 * math.pi)
        self.energy: float = 1.0
        self.health: float = 1.0
        self.age: int = 0
        self.score: int = 0
        self.interacted_object = None

        self.inputs: List[float] = []
        self.outputs: List[float] = [0.0, 0.0, 0.0]  # d_theta, velocity, eat_flag

        n_input = self.VISION_RAYS * 4 + 2
        n_output = 3
        n_hidden = (n_input + n_output) * 2
        self.brain = NeuroBlob(n_input=n_input, n_hidden=n_hidden,
                               n_output=n_output, allow_self_connections=True)

    def update(self, nearests: Set[WorldObject], think_steps=1) -> Optional[WorldObject]:
        self.interacted_object = None
        self._sense(nearests)
        self._think(think_steps)
        self._act(nearests)

        return self.interacted_object

    def _sense(self, nearests: Set[WorldObject]) -> None:
        """
        Сбор информации об окружающей среде через зрительные лучи

        Args:
            nearests (Set[WorldObject]): Ссылка на ближайшие объекты
        """
        inputs = []
        for i in range(self.VISION_RAYS):
            start_angle = self.angle - self.VISION_ANGLE / 2
            ray_angle = start_angle + (i / (self.VISION_RAYS - 1)) * self.VISION_ANGLE
            ray_dir = (math.cos(ray_angle), math.sin(ray_angle))

            best_score = 0.0
            best_color = [0.0, 0.0, 0.0]

            # Проверка объектов в сетке
            dist = None
            for obj in nearests:
                if obj is self:
                    continue

                if obj.is_circle:
                    dist = self._intersect_ray_circle(ray_dir, obj)
                if obj.is_rectangle:
                    dist = self._intersect_ray_rectangle(ray_dir, obj)

                if dist is None or dist > self.VISION_DISTANCE:
                    continue

                proximity = 1.0 - (dist / self.VISION_DISTANCE)
                if proximity > best_score:
                    best_score = proximity
                    best_color = [c / 255.0 for c in obj.color]

            inputs.extend([best_score] + best_color)

        inputs.append(1 - self.energy)
        inputs.append(1 - self.health)
        self.inputs = inputs

    def _think(self, think_steps: int = 1) -> None:
        """
        Обработка собранных данных нейросетью

        Args:
            think_steps (int): Количество шагов обработки нейросети
        """
        self.outputs = self.brain.step(self.inputs, steps_count=think_steps)

    def _act(self, nearests: Set[WorldObject]) -> None:
        """
        Выполнение действий на основе решений нейросети

        Args:
            nearests (Set[WorldObject]): Ссылка на ближайшие объекты
        """
        d_theta, velocity, eat_flag = self.outputs
        d_theta *= 0.1
        self.age += 1

        # Движение
        self._rotate(d_theta)
        self._move(velocity)

        # Расчёт изменений состояния
        prev_e = self.energy
        prev_h = self.health

        if eat_flag > self.CONSUME_LEVEL:
            self._consume_if_possible(nearests)

        total_cost = self.PASSIVE_COST + self.MOVEMENT_COST_FACTOR * velocity ** 2
        self._apply_energy_cost(total_cost)
        self._restore_health()

        # Механизм обучения
        if self.LEARNING and self.brain:
            self._update_learning(prev_e, prev_h)

            # Легкое затухание весов для предотвращения застревания
            if self.age % 100 == 0:  # Периодическое затухание
                self.brain.W *= 0.999

    @property
    def grid_radius(self) -> float:
        """
        Возвращает радиус области, в которой агент может обнаруживать объекты
        
        Returns:
            float: Дальность видимости агента (VISION_DISTANCE)
        """
        return self.VISION_DISTANCE

    def _rotate(self, d_theta: float) -> None:
        """Обновление угла поворота агента"""
        self.angle = (self.angle + d_theta) % (2 * math.pi)

    def _move(self, velocity: float) -> None:
        """Перемещение агента с учётом границ мира"""
        dx = math.cos(self.angle) * velocity
        dy = math.sin(self.angle) * velocity


        self.x = self.x + dx
        self.y = self.y + dy

    def _apply_energy_cost(self, cost: float) -> None:
        """Расход энергии с учётом возможного дефицита"""
        if self.energy > cost:
            self.energy -= cost
        else:
            deficit = cost - self.energy
            self.energy = 0.0
            self.health = max(0.0, self.health - deficit)

    def _restore_health(self) -> None:
        """Восстановление здоровья за счёт энергии"""
        if self.health < 1.0:
            heal = min(self.REGEN_COST, 1.0 - self.health, self.energy)
            self.health += heal
            self.energy -= heal

    def _consume_if_possible(self, nearests: Set[WorldObject]) -> None:
        """Попытка потребления ближайшего объекта"""
        self._apply_energy_cost(self.BITING_COST)

        for obj in nearests:
            dx = obj.x - self.x
            dy = obj.y - self.y
            distance = math.hypot(dx, dy)
            angle = (math.atan2(dy, dx) + math.pi - self.angle) % math.tau - math.pi

            if distance > (self.radius + obj.radius)*1.2 or abs(angle) > self.VISION_ANGLE / 2:
                continue

            match obj.category:
                case 'food':
                    self._process_consumption(obj)
                    self.interacted_object = obj
                case _:
                    pass

            return

    def _process_consumption(self, food: WorldObject) -> None:
        """Обработка успешного потребления объекта"""
        self.energy = min(1.0, self.energy + food.ENERGY_COST)
        self.health = max(0.0, self.health + food.HEALTH_COST)

        self.score += 1 if food.ENERGY_COST else -1
        if self.LEARNING:
            self.brain.learn(scale=0.0001)

    def _intersect_ray_circle(self, ray_dir: Tuple[float, float],
                              obj: WorldObject) -> Optional[float]:
        """Расчёт пересечения луча с круглым объектом"""
        dx, dy = ray_dir

        Lx, Ly = obj.position - self.position

        t_m = Lx * Lx + Ly * Ly
        if t_m > (self.VISION_DISTANCE + obj.radius) ** 2:
            return None

        t_ca = Lx * dx + Ly * dy
        if t_ca < 0:
            return None

        d2 = t_m - t_ca * t_ca
        if d2 > obj.radius * obj.radius:
            return None

        t_hc = math.sqrt(obj.radius * obj.radius - d2)
        t0 = t_ca - t_hc
        t1 = t_ca + t_hc
        return t0 if t0 >= 0 else (t1 if t1 >= 0 else None)

    def _intersect_ray_wall(self, ray_dir: Tuple[float, float],
                            world: World) -> Optional[float]:
        """Расчёт пересечения луча с границами мира"""
        if (self.VISION_DISTANCE < self.x < world.width - self.VISION_DISTANCE and
                self.VISION_DISTANCE < self.y < world.height - self.VISION_DISTANCE):
            return None

        max_x = self.VISION_DISTANCE * ray_dir[0] + self.x
        max_y = self.VISION_DISTANCE * ray_dir[1] + self.y

        if 0.0 < max_x < world.width and 0.0 < max_y < world.height:
            return None

        dist = self.VISION_DISTANCE

        if max_x > world.width:
            dist = min(dist, (world.width - self.x) / ray_dir[0])
        elif max_x < 0.0:
            dist = min(dist, -self.x / ray_dir[0])

        if max_y > world.height:
            dist = min(dist, (world.height - self.y) / ray_dir[1])
        elif max_y < 0.0:
            dist = min(dist, -self.y / ray_dir[1])

        return dist

    def _intersect_ray_rectangle(self, ray_dir: Tuple[float, float],
                            obj: WorldObject) -> Optional[float]:
        """Расчёт пересечения луча с прямоугольным объектом"""

        dx, dy = obj.position - self.position

        max_x = dx + obj.width/2
        min_x = dx - obj.width/2
        max_y = dy + obj.height/2
        min_y = dy - obj.height/2

        dist = self.VISION_DISTANCE

        for x_edge in (max_x, min_x):
            if x_edge*ray_dir[0]>0:
                inter_y = x_edge/ray_dir[0]*ray_dir[1]
                if (max_y - inter_y)*(min_y - inter_y) <= 0:
                    dist = min(x_edge/ray_dir[0], dist)

        for y_edge in (max_y, min_y):
            if y_edge*ray_dir[1]>0:
                inter_x = y_edge/ray_dir[1]*ray_dir[0]
                if (max_x - inter_x)*(min_x - inter_x) <= 0:
                    dist = min(y_edge/ray_dir[1], dist)

        return dist

    def draw(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0)) -> None:
        """Отрисовка агента и его визуальных индикаторов"""
        x, y = (self.x + offset[0], self.y + offset[1])

        # Отрисовка лучей зрения
        for i in range(self.VISION_RAYS):
            dist = (1.0 - self.inputs[4 * i]) * self.VISION_DISTANCE
            color = [int(c * 255.0) for c in self.inputs[4 * i + 1:4 * i + 4]]

            ray_angle = (self.angle - self.VISION_ANGLE / 2 +
                         (i / (self.VISION_RAYS - 1)) * self.VISION_ANGLE)
            tip_x = x + math.cos(ray_angle) * dist
            tip_y = y + math.sin(ray_angle) * dist
            pygame.draw.line(surface, color, (x, y), (tip_x, tip_y), 2)

        # Индикаторы состояния
        self._draw_attribute(surface, 3, self.energy, (250, 200, 0), offset)
        self._draw_attribute(surface, 2, self.health, (250, 10, 10), offset)

        # Основной круг агента
        super().draw(surface, offset=offset)

        # Индикатор питания
        if self.outputs[2] > self.CONSUME_LEVEL:
            pygame.draw.circle(surface, (255, 255, 0),
                               (int(x), int(y)), self.radius)

        # Направление взгляда
        tip_x = x + math.cos(self.angle) * self.radius
        tip_y = y + math.sin(self.angle) * self.radius
        pygame.draw.line(surface, (255, 255, 255), (x, y), (tip_x, tip_y), 2)

    def _draw_attribute(self, surface: pygame.Surface, factor: float,
                        attribute: float, color: Tuple[int, int, int],
                        offset: Tuple[int, int]) -> None:
        """Отрисовка кругового индикатора атрибута"""
        pygame.gfxdraw.arc(
            surface,
            int(self.x + offset[0]),
            int(self.y + offset[1]),
            int(self.radius * factor),
            -90 - int(359 * attribute),
            -90,
            color
        )

    def _update_learning(self, prev_e: float, prev_h: float) -> None:
        """Обновление параметров обучения"""
        delta_h = self.health - prev_h
        delta_e = self.energy - prev_e
        
        # Базовый масштаб для всех обучающих сигналов
        BASE_SCALE = 0.00001
        
        # Здоровье (важнее энергии)
        self.brain.learn(scale=3 * BASE_SCALE * delta_h, forgotten_rate=0.00001)
        
        # Энергия
        self.brain.learn(scale=BASE_SCALE * delta_e, forgotten_rate=0.00001)  # Для всех случаев, без условия
        
        # Критические состояния
        if self.health == 0.0:
            self.brain.learn(scale=-10 * BASE_SCALE, forgotten_rate=0.0001)  # В 10 раз сильнее базового
