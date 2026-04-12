from dataclasses import dataclass
from typing import Tuple, List

@dataclass
class Position:
    x: float
    y: float

@dataclass
class Velocity:
    dx: float = 0.0
    dy: float = 0.0

@dataclass
class Health:
    value: float = 1.0

@dataclass
class Energy:
    value: float = 1.0

@dataclass
class Color:
    rgb: Tuple[int, int, int]

@dataclass
class Brain:
    brain: object  # Экземпляр NeuroBlob

@dataclass
class Size:
    value: float

@dataclass
class Category:
    name: str

@dataclass
class Vision:
    rays: int
    distance: float
    angle: float

@dataclass
class Metabolism:
    passive_cost: float = 0.0001
    movement_cost: float = 0.001
    biting_cost: float = 0.005
    regen_cost: float = 0.0001

@dataclass
class Consumable:
    energy_effect: float = 0.2
    health_effect: float = 0.0 

@dataclass
class DamageComponent:
    # Список (id агента, сила укуса)
    damage_requests: List[Tuple[int, float]]
    bitten_by: int = -1  # ID агента, который успешно укусил (для подсчета очков)

# Новые компоненты для ECS-логики

@dataclass
class Angle:
    angle: float = 0.0

@dataclass
class WantsToBite:
    value: bool = False

@dataclass
class Score:
    value: int = 0

@dataclass
class BrainIO:
    inputs: List[float]
    outputs: List[float]