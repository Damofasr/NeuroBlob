import pygame
import matplotlib.pyplot as plt
from typing import List, Dict
from world import World
from simulation_manager import SimulationManager
from config import *


class NeuroBlobGUI:
    """
    Класс для управления графическим интерфейсом

    Атрибуты:
        screen (pygame.Surface): Основная поверхность отрисовки
        font (pygame.font.Font): Шрифт для текста
        clock (pygame.time.Clock): Таймер FPS
    """

    def __init__(self):
        pygame.init()
        width = WORLD_SIZE[0] + 2 * UI_SETTINGS['border_width']
        height = WORLD_SIZE[1] + UI_SETTINGS['header_height'] + 2 * UI_SETTINGS['border_width']

        self.screen = pygame.display.set_mode((width, height))
        # Создаём отдельную поверхность для мира
        self.world_surface = pygame.Surface(WORLD_SIZE)
        self.drawing = True

        pygame.display.set_caption("NeuroBlob Evolution Simulator")

        try:
            self.font = pygame.font.Font('fonts/PressStart2P.ttf', 16)  # Путь к файлу шрифта
        except FileNotFoundError:
            print("Шрифт не найден, используется системный")
            self.font = pygame.font.SysFont('Arial', 16, bold=True)

        self.clock = pygame.time.Clock()

    def draw(self, world: World, manager: SimulationManager) -> None:
        """Отрисовка всего интерфейса"""
        self.screen.fill((30, 30, 30))

        # Отрисовка мира на отдельной поверхности
        self.world_surface.fill((30, 30, 30))  # Фон мира
        world.draw(self.world_surface)  # Без offset

        # Отрисовка UI элементов
        self._draw_borders()
        self._draw_header(manager)

        # Переносим поверхность мира на основной экран
        world_pos = (
            UI_SETTINGS['border_width'],
            UI_SETTINGS['header_height'] + UI_SETTINGS['border_width']
        )
        self.screen.blit(self.world_surface, world_pos)
        pygame.display.flip()

    def _draw_borders(self) -> None:
        """Отрисовка декоративных границ"""
        border_color = (30, 30, 30)
        pygame.draw.rect(self.screen, border_color,
                         (0, UI_SETTINGS['header_height'],
                          self.screen.get_width(),
                          self.screen.get_height()))

    def _draw_header(self, manager: SimulationManager) -> None:
        """Отрисовка верхней информационной панели"""
        # Статистика
        fps_text = self.font.render(f"FPS:{self.clock.get_fps():5.1f}", True, (255, 255, 0))
        gen_text = self.font.render(f"Поколение: {manager.generation}", True, (255, 255, 255))

        # Позиционирование
        self.screen.blit(fps_text, (665, 10))
        self.screen.blit(gen_text, (10, 10))

        # Лучший агент
        if manager.best_agent:
            stats_text = self.font.render(
                f"Лучший: Возраст {manager.best_agent.age} Счёт {manager.best_agent.score}",
                True, (255, 255, 255))
            self.screen.blit(stats_text, (10, 35))

    @staticmethod
    def show_plots(stats: Dict[str, List]) -> None:
        """Отображение графиков статистики"""
        plt.figure("Эволюция показателей")
        plt.plot( stats['scores'], label='Счёт')
        plt.xlabel("Время")
        plt.ylabel("Показатели")
        plt.legend()
        plt.show()