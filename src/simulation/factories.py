from src.simulation.components import (
    Position,
    Velocity,
    Health,
    Energy,
    Color,
    Brain,
    Size,
    Category,
    Vision,
    Metabolism,
    Consumable,
    Angle,
    WantsToBite,
    Score,
    BrainIO,
)
from src.core.neuroblob import NeuroBlob

# Фабрика для создания агента
def create_agent(world, x, y, color=(0, 100, 255), health=1.0, energy=1.0, size=6.0,
                 rays: int = 11, distance: float = 100.0, angle: float = 2.0 * 3.141592653589793 * (120.0 / 360.0)):
    entity = world.create_entity()
    world.add_component(entity, Category('agent'))
    world.add_component(entity, Color(color))
    world.add_component(entity, Size(size))
    world.add_component(entity, Position(x, y))
    world.add_component(entity, Velocity())
    world.add_component(entity, Health(health))
    world.add_component(entity, Energy(energy))
    # Vision: 120 градусов по умолчанию
    world.add_component(entity, Vision(rays=rays, distance=distance, angle=2.0943951023931953))

    # Размеры мозга: совместимы с Agent (n_input = rays*4 + 2; n_output = 3; n_hidden = (in+out)*2)
    n_input = rays * 4 + 2
    n_output = 3
    n_hidden = (n_input + n_output) * 2
    brain = NeuroBlob(n_input=n_input, n_hidden=n_hidden, n_output=n_output)
    world.add_component(entity, Brain(brain))

    # IO буферы для мозга
    world.add_component(entity, BrainIO(inputs=[0.0] * n_input, outputs=[0.0] * n_output))

    # Угол, намерение кусать и счёт
    world.add_component(entity, Angle())
    world.add_component(entity, WantsToBite())
    world.add_component(entity, Score())
    world.add_component(entity, Metabolism())
    return entity

# Фабрика для создания еды
def create_food(world, x, y, color=(0, 255, 0), health=1.0, size=3.0):
    entity = world.create_entity()
    world.add_component(entity, Category('food'))
    world.add_component(entity, Color(color))
    world.add_component(entity, Size(size))
    world.add_component(entity, Position(x, y))
    world.add_component(entity, Health(health))
    world.add_component(entity, Consumable(energy_effect=0.2, health_effect=0.0))
    return entity

# Фабрика для создания яда
def create_poison(world, x, y, color=(128, 0, 128), health=1.0, size=3.0):
    entity = world.create_entity()
    world.add_component(entity, Category('poison'))
    world.add_component(entity, Color(color))
    world.add_component(entity, Size(size))
    world.add_component(entity, Position(x, y))
    world.add_component(entity, Health(health))
    world.add_component(entity, Consumable(energy_effect=0.0, health_effect=-0.1))
    return entity 