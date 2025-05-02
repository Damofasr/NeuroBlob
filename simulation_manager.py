import copy
import pygame
from typing import Optional
from agent import Agent
from food import Food, Poison
from world import World
from config import *


class SimulationManager:
    """
    Класс для управления симуляцией эволюции агентов

    Отвечает за:
    - Создание и обновление мира
    - Управление поколениями агентов
    - Сбор статистики
    - Взаимодействие с GUI

    Атрибуты:
        world (World): Игровой мир
        best_agent (Optional[Agent]): Лучший агент текущего поколения
        generation (int): Номер текущего поколения
        stats (Dict[str, List]): Собранная статистика
    """

    def __init__(self, brain_file: Optional[str] = None):
        self.world = World(*WORLD_SIZE)
        self.best_agent: Optional[Agent] = None
        self.generation = 0
        self.stats = {
            'timestamps': [],
            'scores': []
        }
        self.current_tick = 0
        self.brain_file = brain_file  # Новый атрибут

        # Инициализация первого поколения с загрузкой мозга
        try:
            if self.brain_file:
                self._load_initial_brain()
        except Exception as e:
            print(f"Ошибка загрузки мозга: {str(e)}")
            self.brain_file = None

        # Инициализация первого поколения
        self.start_new_generation()

    def _load_initial_brain(self) -> None:
        """Загрузка начального мозга из файла"""
        temp_agent = Agent(0, 0)
        temp_agent.brain.load(self.brain_file)
        self.best_agent = temp_agent
        print(f"Загружен мозг из {self.brain_file}")

    def start_new_generation(self) -> None:
        """Запуск нового поколения агентов"""
        self.current_tick = 0

        if self.best_agent:
            if self.generation > 0:
                print(f"Поколение {self.generation}: Возраст {self.best_agent.age}, Счёт {self.best_agent.score}")
            self._update_stats()

        self.generation += 1
        self._reset_world()
        self._create_new_population()
        self.best_agent = None

    def _reset_world(self) -> None:
        """Полная переинициализация мира"""
        self.world = World(*WORLD_SIZE)
        self._spawn_objects()

    def _spawn_objects(self) -> None:
        """Создание начальных объектов в мире"""
        self.world.add_object(Food, count=50)
        self.world.add_object(Poison, count=50)
        self.world.add_object(Agent, count=10)

    def _create_new_population(self) -> None:
        """Создание популяции с учётом загруженного мозга"""
        # if self.brain_file and not self.best_agent:
        #     self._load_initial_brain()

        if not self.best_agent:
            return

        for agent in self.world.get_objects('agent'):
            agent.brain = copy.deepcopy(self.best_agent.brain)
            if agent != self.world.get_objects('agent'):
                agent.brain.mutate()

    def _update_stats(self) -> None:
        """Обновление статистики симуляции"""
        self.current_tick += 1
        self.stats['timestamps'].append(pygame.time.get_ticks())
        self.stats['scores'].append(self.best_agent.score if self.best_agent else 0)

    def update(self) -> None:
        """Основной цикл обновления"""
        self.world.update()
        self._check_agents_state()

    def _check_agents_state(self) -> None:
        """Проверка состояния агентов и обновление лучшего"""
        for agent in self.world.get_objects('agent'):
            if agent.health <= 0 or self.current_tick > UI_SETTINGS['simulation_duration']:
                self._evaluate_agent(agent)
                self.world.remove_object(agent)

    def _evaluate_agent(self, agent: Agent) -> None:
        """Оценка пригодности агента"""
        if not self.best_agent or agent.score > self.best_agent.score:
            self.best_agent = copy.deepcopy(agent)