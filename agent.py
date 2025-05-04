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

    def __init__(self, x: float, y: float):
        """
        Инициализация агента

        Args:
            x (float): Начальная X-координата
            y (float): Начальная Y-координата
        """
        super().__init__(x, y, size=6, color=(0, 100, 255))
        self.angle: float = random.uniform(0, 2 * math.pi)
        self.energy: float = 1.0
        self.health: float = 1.0
        self.age: int = 0
        self.score: int = 0

        self.inputs: List[float] = []
        self.outputs: List[float] = [0.0, 0.0, 0.0]  # d_theta, velocity, eat_flag

        n_input = self.VISION_RAYS * 4 + 2
        n_output = 3
        n_hidden = (n_input + n_output) * 2
        self.brain = NeuroBlob(n_input=n_input, n_hidden=n_hidden,
                               n_output=n_output, allow_self_connections=True)

    def sense(self, world: World) -> None:
        """
        Сбор информации об окружающей среде через зрительные лучи

        Args:
            world (World): Ссылка на игровой мир
        """
        inputs = []
        for i in range(self.VISION_RAYS):
            start_angle = self.angle - self.VISION_ANGLE / 2
            ray_angle = start_angle + (i / (self.VISION_RAYS - 1)) * self.VISION_ANGLE
            ray_dir = (math.cos(ray_angle), math.sin(ray_angle))

            best_score = 0.0
            best_color = [0.0, 0.0, 0.0]

            # Проверка пересечения со стенами
            dist = self._intersect_ray_rectangle(ray_dir, world)
            if dist is not None and dist <= self.VISION_DISTANCE:
                proximity = 1.0 - (dist / self.VISION_DISTANCE)
                best_score = proximity
                best_color = [0.5, 0.5, 0.5]

            # Проверка объектов в сетке
            for obj in world.get_objects_in_area(self.x, self.y, self.VISION_DISTANCE):
                if obj is self:
                    continue

                match obj.category:
                    case 'wall':
                        dist = self._intersect_ray_rectangle(ray_dir, world)
                    case _:
                        dist = self._intersect_ray_circle(ray_dir, obj)

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

    def think(self, steps_count: int = 1) -> None:
        """
        Обработка собранных данных нейросетью

        Args:
            steps_count (int): Количество шагов обработки нейросети
        """
        self.outputs = self.brain.step(self.inputs, steps_count=steps_count)

    def act(self, world: World) -> None:
        """
        Выполнение действий на основе решений нейросети

        Args:
            world (World): Ссылка на игровой мир
        """
        d_theta, velocity, eat_flag = self.outputs
        d_theta *= 0.1
        self.age += 1

        # Движение
        self._rotate(d_theta)
        self._move(world, velocity)

        # Расчёт изменений состояния
        prev_e = self.energy
        prev_h = self.health

        if eat_flag > self.CONSUME_LEVEL:
            self._consume_if_possible(world)

        total_cost = self.PASSIVE_COST + self.MOVEMENT_COST_FACTOR * velocity ** 2
        self._apply_energy_cost(total_cost)
        self._restore_health()

        # Механизм обучения
        if self.LEARNING and self.brain:
            self._update_learning(prev_e, prev_h)

    def _rotate(self, d_theta: float) -> None:
        """Обновление угла поворота агента"""
        self.angle = (self.angle + d_theta) % (2 * math.pi)

    def _move(self, world: World, velocity: float) -> None:
        """Перемещение агента с учётом границ мира"""
        dx = math.cos(self.angle) * velocity
        dy = math.sin(self.angle) * velocity


        self.x = max(self.radius, min(self.x + dx, world.width - self.radius))
        self.y = max(self.radius, min(self.y + dy, world.height - self.radius))

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

    def _consume_if_possible(self, world: World) -> None:
        """Попытка потребления ближайшего объекта"""
        self._apply_energy_cost(self.BITING_COST)

        for food in world.get_objects('food'):
            dx = food.x - self.x
            dy = food.y - self.y
            distance = math.hypot(dx, dy)
            angle = (math.atan2(dy, dx) + math.pi - self.angle) % math.tau - math.pi

            if distance > self.radius + food.radius or abs(angle) > self.VISION_ANGLE / 2:
                continue

            self._process_consumption(world, food)
            return

    def _process_consumption(self, world: World, food: WorldObject) -> None:
        """Обработка успешного потребления объекта"""
        world.remove_object(food)
        self.energy = min(1.0, self.energy + food.ENERGY_COST)
        self.health = max(0.0, self.health + food.HEALTH_COST)
        world.add_object(type(food))

        self.score += 1 if food.ENERGY_COST else -1
        if self.LEARNING:
            self.brain.learn(reward=1.0, lr=0.0001)

    def _intersect_ray_circle(self, ray_dir: Tuple[float, float],
                              obj: WorldObject) -> Optional[float]:
        """Расчёт пересечения луча с круглым объектом"""
        dx, dy = ray_dir
        Lx = obj.x - self.x
        Ly = obj.y - self.y

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

    def _intersect_ray_rectangle(self, ray_dir: Tuple[float, float],
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

    def draw(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0)) -> None:
        """Отрисовка агента и его визуальных индикаторов"""
        x, y = (self.x + offset[0], self.y + offset[1])

        # Отрисовка лучей зрения
        for i in range(self.VISION_RAYS):
            dist = (1.0 - self.inputs[4 * i]) * self.VISION_DISTANCE
            color = [c * 255.0 for c in self.inputs[4 * i + 1:4 * i + 4]]

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

        self.brain.learn(reward=0.1 * delta_h, lr=0.01)

        if delta_e < 0:
            self.brain.learn(reward=0.1 * delta_e, lr=0.01)

        if self.energy > 0.9:
            self.brain.learn(reward=0.01, lr=0.001)
        elif self.energy < 0.1:
            self.brain.learn(reward=-0.01, lr=0.001)

        if self.health == 0.0:
            self.brain.learn(reward=-1.0, lr=0.005)
