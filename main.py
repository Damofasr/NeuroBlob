import sys
import pygame
from neuroblob_gui import NeuroBlobGUI
from simulation_manager import SimulationManager
from config import *


def main() -> None:
    """Основная функция с обработкой аргументов"""
    # parser = argparse.ArgumentParser(description='NeuroBlob Simulation')
    # parser.add_argument('-l', '--load', type=str,
    #                    help='Путь к файлу мозга для загрузки')
    # args = parser.parse_args()

    gui = NeuroBlobGUI()
    manager = SimulationManager(brain_file='brains/best_brain_2.json')  # Передаем аргумент
    running = True
    drawing = True

    while running:
        gui.clock.tick()

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                handle_key_events(event, manager, gui)

        # Логика обновления
        manager.update()

        # Отрисовка
        if gui.drawing:
            gui.draw(manager.world, manager)

        # Перезапуск поколения
        if not manager.world.get_objects('agent'):
            manager.start_new_generation()

    # Завершение работы
    pygame.quit()
    gui.show_plots(manager.stats)
    sys.exit()


def handle_key_events(event: pygame.event.Event,
                      manager: SimulationManager,
                      gui: NeuroBlobGUI) -> None:
    """Обработка нажатий клавиш"""
    match event.key:
        case pygame.K_p:  # Пауза
            gui.drawing = not gui.drawing
        case pygame.K_s:  # Сохранение мозга
            save_filename = 'best_brain.json'
            manager.best_agent.brain.save(save_filename)
            print(f'Мозг сохранён в {save_filename}')
        case pygame.K_l:  # Загрузка мозга
            load_filename = 'best_brain.json'
            manager.best_agent.brain.load(load_filename)
            print(f'Мозг загружен из {load_filename}')
        case pygame.K_m:  # Мутация
            for agent in manager.world.get_objects('agent'):
                agent.brain.mutate()


if __name__ == "__main__":
    main()