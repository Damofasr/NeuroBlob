import math
import esper
from src.simulation.components import Position, Velocity, Health, Energy, Brain, Metabolism, Consumable, Vision, Angle, WantsToBite, BrainIO, Score, Size, Color, Category


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

# Система движения
class MovementSystem(esper.Processor):
    def process(self, dt=1.0):
        for ent, (pos, vel, health) in self.world.get_components(Position, Velocity, Health):
            pos.x += vel.dx * health.value * dt
            pos.y += vel.dy * health.value * dt

# Система восстановления здоровья (пример)
class EnergySystem(esper.Processor):
    def process(self, dt=1.0):
        for ent, (energy, metabolism, velocity) in self.world.get_components(Energy, Metabolism, Velocity):
            # Пассивный расход
            delta = metabolism.passive_cost * dt
            # Квадратичный расход на движение (сохранение старой модели)
            speed = (velocity.dx ** 2 + velocity.dy ** 2) ** 0.5
            delta += metabolism.movement_cost * (speed ** 2) * dt
            energy.value = _clamp01(energy.value - delta)

class HealthRegenSystem(esper.Processor):
    def process(self, dt=1.0):
        for ent, (health, energy, metabolism) in self.world.get_components(Health, Energy, Metabolism):
            if health.value < 1.0 and energy.value > 0.0:
                heal = min(metabolism.regen_cost * dt, 1.0 - health.value, energy.value)
                health.value += heal
                energy.value -= heal

# Система удаления мёртвых объектов
class RemoveDeadSystem(esper.Processor):
    def process(self):
        for ent, health in self.world.get_component(Health):
            if health.value <= 0.0:
                self.world.delete_entity(ent)

class VisionSystem(esper.Processor):
    """
    Формирует входы для мозга: для каждого луча — близость [0..1] и цвет цели (нормированный),
    затем добавляет (1 - energy), (1 - health).
    Упрощение: все объекты считаются круглыми с радиусом Size.value, пересечение — по близости
    с учётом обзора по углу и дальности (без точного лучевого пересечения с окружностью).
    """
    def process(self):
        # Собираем все потенциальные цели разом
        targets = []  # (pos, radius, color)
        for ent, (pos,) in self.world.get_components(Position):
            size = self.world.try_component(ent, Size)
            color = self.world.try_component(ent, Color)
            category = self.world.try_component(ent, Category)
            if size and color:
                targets.append((ent, pos, size.value, color.rgb, category.name if category else None))

        for ent, (pos, vision, brainio, angle, energy, health) in self.world.get_components(Position, Vision, BrainIO, Angle, Energy, Health):
            inputs = []
            start_angle = angle.angle - vision.angle / 2.0
            for i in range(vision.rays):
                ray_angle = start_angle + (i / (vision.rays - 1)) * vision.angle if vision.rays > 1 else angle.angle
                dir_x = math.cos(ray_angle)
                dir_y = math.sin(ray_angle)

                best_score = 0.0
                best_color = (0.0, 0.0, 0.0)

                for tgt_ent, tgt_pos, tgt_radius, tgt_color, tgt_cat in targets:
                    if tgt_ent == ent:
                        continue
                    dx = tgt_pos.x - pos.x
                    dy = tgt_pos.y - pos.y
                    distance = (dx * dx + dy * dy) ** 0.5
                    if distance > vision.distance or distance == 0:
                        continue
                    # Проверяем угол между направлением луча и вектором на цель
                    dot = (dx * dir_x + dy * dir_y) / distance
                    # Условие: цель примерно по направлению луча (допускаем узкий сектор)
                    if dot < math.cos(vision.angle / max(vision.rays, 2)):
                        continue
                    proximity = 1.0 - min(1.0, distance / vision.distance)
                    if proximity > best_score:
                        best_score = proximity
                        best_color = (tgt_color[0] / 255.0, tgt_color[1] / 255.0, tgt_color[2] / 255.0)

                inputs.extend([best_score, *best_color])

            inputs.append(1.0 - energy.value)
            inputs.append(1.0 - health.value)
            brainio.inputs = inputs


class BrainDecisionSystem(esper.Processor):
    """
    Вызывает мозг, записывает outputs, обновляет угол, скорость и флаг укуса.
    """
    def __init__(self, consume_level: float = 0.0, think_steps: int = 1):
        super().__init__()
        self.consume_level = consume_level
        self.think_steps = think_steps

    def process(self):
        for ent, (brain, brainio, angle, vel, health, energy, vision) in self.world.get_components(Brain, BrainIO, Angle, Velocity, Health, Energy, Vision):
            # Если энергии совсем мало, всё равно считаем — поведение обучаемое
            outputs = brain.brain.step(brainio.inputs, steps_count=self.think_steps)
            brainio.outputs = outputs
            d_theta, velocity_mag, eat_flag = outputs
            # Масштаб поворота как в Agent
            angle.angle = (angle.angle + d_theta * 0.1) % (2.0 * math.pi)
            vel.dx = math.cos(angle.angle) * velocity_mag * health.value
            vel.dy = math.sin(angle.angle) * velocity_mag * health.value
            wants = self.world.try_component(ent, WantsToBite)
            if wants:
                wants.value = eat_flag > self.consume_level

class EatSystem(esper.Processor):
    def process(self):
        # Агент ест ближайший объект с Consumable, если активен WantsToBite
        agents = list(self.world.get_components(Position, Size, Energy, Health, Metabolism, WantsToBite))
        foods = list(self.world.get_components(Position, Size, Consumable))

        for ent, (apos, asize, aenergy, ahealth, meta, bite_flag) in agents:
            if not bite_flag.value:
                continue
            # Стоимость попытки укуса
            aenergy.value = _clamp01(aenergy.value - meta.biting_cost)

            # Поиск ближайшей пищи в досягаемости
            best = None
            best_dist = None
            for fent, (fpos, fsize, cons) in foods:
                dx = fpos.x - apos.x
                dy = fpos.y - apos.y
                dist = (dx * dx + dy * dy) ** 0.5
                reach = asize.value + fsize.value
                if dist <= reach * 1.5:
                    if best is None or dist < best_dist:
                        best = (fent, cons)
                        best_dist = dist

            if best is None:
                continue

            fent, cons = best
            # Применяем эффекты
            aenergy.value = _clamp01(aenergy.value + cons.energy_effect)
            ahealth.value = _clamp01(ahealth.value + cons.health_effect)

            # Обновляем счёт
            score = self.world.try_component(ent, Score)
            if score:
                if cons.energy_effect > 0:
                    score.value += 1
                elif cons.health_effect < 0:
                    score.value -= 1

            # Удаляем съеденное
            self.world.delete_entity(fent)