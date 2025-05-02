import numpy as np
import random
import pygame
from world_object import WorldObject
from neuroblob import NeuroBlob

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

class Agent(WorldObject):
    category = 'agent'

    VISION_RAYS = 11
    VISION_DISTANCE = 100.0
    VISION_ANGLE = 120 * (np.pi / 180)

    # Energy & health dynamics
    PASSIVE_COST = 0.0001
    MOVEMENT_COST_FACTOR = 0.001
    REGEN_COST = PASSIVE_COST  # cost per tick available for health regen
    FOOD_COST = 0.2

    def __init__(self, x, y):
        super().__init__(x, y, radius=6, color=(0, 100, 255))
        self.angle = random.uniform(0, 2 * np.pi)
        self.energy = 1.0
        self.health = 1.0
        self.age = 0
        self.score = 0

        # Precompute ray directions with numpy
        self.angles = np.linspace(-0.5, 0.5, self.VISION_RAYS, dtype=np.float32) * self.VISION_ANGLE
        self.ray_dirs = np.zeros((self.VISION_RAYS, 2), dtype=np.float32)
        self._update_ray_dirs()

        # Input / output buffers
        self.inputs = np.zeros(self.VISION_RAYS * 4 + 2, dtype=np.float32)
        self.outputs = np.zeros(3, dtype=np.float32)

        # NeuroBlob brain
        n_input = self.inputs.size
        n_output = self.outputs.size
        n_hidden = (n_input + n_output) * 2
        self.brain = NeuroBlob(n_input=n_input,
                               n_hidden=n_hidden,
                               n_output=n_output,
                               allow_self_connections=True)

    def _update_ray_dirs(self):
        """Recompute ray_dirs based on current angle."""
        angles = self.angle + self.angles
        self.ray_dirs[:, 0] = np.cos(angles)
        self.ray_dirs[:, 1] = np.sin(angles)

    def sense(self, world):
        """Populate self.inputs with vision + fatigue + damage."""
        # Update ray directions
        self._update_ray_dirs()

        idx = 0
        # For each ray, compute best intersection
        for ray_dir in self.ray_dirs:
            best_score = 0.0
            best_color = np.zeros(3, dtype=np.float32)

            # Check walls
            t_wall = self._intersect_ray_rectangle(ray_dir, world)
            if t_wall is not None and t_wall <= self.VISION_DISTANCE:
                proximity = 1.0 - (t_wall / self.VISION_DISTANCE)
                best_score = proximity
                best_color[:] = 0.5  # gray for walls

            # Check circle objects
            for obj in world.get_objects():
                if obj is self:
                    continue
                dist = self._intersect_ray_circle(ray_dir, obj)
                if dist is None or dist > self.VISION_DISTANCE:
                    continue
                proximity = 1.0 - (dist / self.VISION_DISTANCE)
                if proximity > best_score:
                    best_score = proximity
                    best_color[:] = np.array(obj.color, dtype=np.float32) / 255.0

            # Store vision inputs
            self.inputs[idx]     = best_score
            self.inputs[idx + 1:idx + 4] = best_color[:]
            idx += 4

        # Fatigue (1 - energy) and damage (1 - health)
        self.inputs[-2] = 1.0 - self.energy
        self.inputs[-1] = 1.0 - self.health

    def think(self):
        """Compute outputs from brain given current inputs."""
        self.outputs[:] = self.brain.step(self.inputs)

    def act(self, world):
        """Perform actions based on self.outputs."""
        d_theta, velocity, eat_flag = self.outputs
        d_theta *= 0.1
        self.age += 1

        self._rotate(d_theta)
        self._move(world, velocity)
        if eat_flag > 0.0:
            self._consume_if_possible(world)

        prev_e, prev_h = self.energy, self.health
        total_cost = self.PASSIVE_COST + self.MOVEMENT_COST_FACTOR * velocity**2
        self._apply_energy_cost(total_cost)
        self._restore_health()

        # Learning commented out; implement as needed

    def _rotate(self, d_theta):
        self.angle = (self.angle + d_theta) % (2 * np.pi)

    def _move(self, world, velocity):
        d_pos = np.array([np.cos(self.angle), np.sin(self.angle)]) * velocity

        self.position = np.clip(self.position + d_pos,
                                [self.radius, self.radius],
                                [world.width - self.radius, world.height - self.radius])

    def _apply_energy_cost(self, cost):
        if self.energy >= cost:
            self.energy -= cost
        else:
            deficit = cost - self.energy
            self.energy = 0.0
            self.health = max(0.0, self.health - deficit)

    def _restore_health(self):
        if self.health < 1.0:
            heal = min(self.REGEN_COST, 1.0 - self.health, self.energy)
            self.health += heal
            self.energy -= heal

    def _consume_if_possible(self, world):
        for food in world.get_objects('food'):
            dx, dy = food.position - self.position

            dist = np.hypot(dx, dy)

            angle = (np.atan2(dy, dx) - self.angle + np.pi) % (2 * np.pi) - np.pi
            if dist <= self.radius + food.radius and abs(angle) <= self.VISION_ANGLE / 2:
                world.remove_object(food)
                self.energy = min(1.0, self.energy + self.FOOD_COST)
                world.add_object(type(food))
                self.score += 1
                break

    def _intersect_ray_circle(self, ray_dir, obj:WorldObject):
        ray_dir = ray_dir.copy()
        L = obj.position - self.position

        t_m = np.dot(L, L)

        if t_m > (self.VISION_DISTANCE + obj.radius)**2:
            return None
        t_ca = np.sum(L*ray_dir)
        d2 = t_m - t_ca*t_ca
        if d2 > obj.radius*obj.radius:
            return None
        t_hc = np.sqrt(obj.radius*obj.radius - d2)
        t0 = t_ca - t_hc
        t1 = t_ca + t_hc
        return t0 if t0 >= 0 else (t1 if t1 >= 0 else None)

    def _intersect_ray_rectangle(self, ray_dir, world):
        if (self.VISION_DISTANCE < self.x < world.width - self.VISION_DISTANCE and
            self.VISION_DISTANCE < self.y < world.height - self.VISION_DISTANCE):
            return None

        dx, dy = ray_dir
        max_x = self.x + dx * self.VISION_DISTANCE
        max_y = self.y + dy * self.VISION_DISTANCE

        if 0.0 < max_x < world.width and 0.0 < max_y < world.height:
            return None

        dist = self.VISION_DISTANCE

        if max_x > world.width:
            dist = min(dist, (world.width - self.x) / dx)
        if max_x < 0:
            dist = min(dist, -self.x / dx)
        if max_y > world.height:
            dist = min(dist, (world.height - self.y) / dy)
        if max_y < 0:
            dist = min(dist, -self.y / dy)

        return dist

    def draw(self, surface):
        """Рисует лучи зрения, агента, значение параметров и намеренье поесть"""
        for i in range(self.VISION_RAYS):
            score = self.inputs[4*i]
            color = (self.inputs[4*i+1:4*i+4] * 255).astype(int)
            dist = (1.0 - score) * self.VISION_DISTANCE
            start_angle = self.angle - self.VISION_ANGLE / 2
            ray_angle = start_angle + (i / (self.VISION_RAYS - 1)) * self.VISION_ANGLE
            tip = (self.x + np.cos(ray_angle)*dist, self.y + np.sin(ray_angle)*dist)
            pygame.draw.line(surface, color, (self.x, self.y), tip, 2)

        # Draw agent body and direction
        super().draw(surface)
        tip = (self.x + np.cos(self.angle)*self.radius,
               self.y + np.sin(self.angle)*self.radius)
        pygame.draw.line(surface, (255,255,255), (self.x, self.y), tip, 2)

