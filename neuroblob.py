import json
import numpy as np
from typing import List, Optional, Dict, Any


class NeuroBlob:
    """
    Класс реализующий рекуррентную нейронную сеть с возможностями:
    - Прямого распространения сигнала
    - Мутаций весов
    - Обучения с подкреплением
    - Сохранения/загрузки состояния

    Атрибуты:
        n_input (int): Количество входных нейронов
        n_hidden (int): Количество скрытых нейронов
        n_output (int): Количество выходных нейронов
        n_neurons (int): Общее количество нейронов (1 + n_input + n_hidden + n_output)
        W (np.ndarray): Матрица весов [n_recurrent x n_neurons]
        state (np.ndarray): Текущее состояние нейронов
    """

    def __init__(self, n_input: int, n_hidden: int, n_output: int,
                 allow_self_connections: bool = True):
        """
        Инициализация нейросети

        Args:
            n_input: Количество входных нейронов
            n_hidden: Количество скрытых нейронов
            n_output: Количество выходных нейронов
            allow_self_connections: Разрешить связи нейронов самих с собой
        """
        self.n_input = n_input
        self.n_hidden = n_hidden
        self.n_output = n_output
        self.n_recurrent = n_hidden + n_output
        self.n_neurons = 1 + n_input + n_hidden + n_output

        # Индексы групп нейронов
        self.bias_idx = 0
        self.input_start = 1
        self.hidden_start = self.input_start + n_input
        self.output_start = self.hidden_start + n_hidden

        # Инициализация весов
        self.W = np.random.uniform(-1.0, 1.0, (self.n_recurrent, self.n_neurons)).astype(np.float32)
        if not allow_self_connections:
            np.fill_diagonal(self.W[:, -self.n_recurrent:], 0.0)

        # Состояния нейронов
        self.state = np.zeros(self.n_neurons, dtype=np.float32)
        self.state[self.bias_idx] = 1.0  # Смещение всегда 1.0
        self.buffer = np.zeros(self.n_recurrent, dtype=np.float32)

    def step(self, input_values: List[float], steps_count: int = 1) -> List[float]:
        """
        Выполняет шаг обработки сигнала

        Args:
            input_values: Входные значения [n_input]
            steps_count: Количество итераций обработки

        Returns:
            Выходные значения [n_output]

        Raises:
            ValueError: При несоответствии размера входных данных
        """
        if len(input_values) != self.n_input:
            raise ValueError(f"Ожидается {self.n_input} входов, получено {len(input_values)}")

        # Установка входных значений
        self.state[self.input_start:self.hidden_start] = input_values

        # Многократное обновление состояния
        for _ in range(steps_count):
            np.dot(self.W, self.state, out=self.buffer)
            np.tanh(self.buffer, out=self.state[self.hidden_start:])

        return self.state[self.output_start:].tolist()

    def mutate(self, rate: float = 0.1, scale: float = 0.01) -> None:
        """
        Случайная мутация весов

        Args:
            rate: Вероятность мутации каждого веса (0.0-1.0)
            scale: Максимальная величина изменения веса
        """
        mask = np.random.rand(*self.W.shape) < rate
        mutation = np.random.uniform(-scale, scale, self.W.shape)
        self.W += mask * mutation
        np.clip(self.W, -1.0, 1.0, out=self.W)

    def learn(self, reward: float, lr: float = 0.01) -> None:
        """
        Обучение методом Хебба с регуляризацией
        
        Args:
            scale: Масштаб изменений весов сети
            forgotten_rate: Скорость забывания (затухание всех весов)
        """
        delta = lr * reward * np.outer(self.state, self.state)
        self.W += delta[-self.n_recurrent:, :]
        np.clip(self.W, -1.0, 1.0, out=self.W)

    def save(self, filename: str) -> None:
        """
        Сохраняет состояние нейросети в файл

        Args:
            filename: Путь к файлу для сохранения
        """
        data = {
            'W': self.W.tolist(),
            'state': self.state.tolist()
        }
        with open(filename, 'w') as file:
            json.dump(data, file)

    def load(self, filename: str) -> None:
        """
        Загружает состояние нейросети из файла

        Args:
            filename: Путь к файлу для загрузки

        Raises:
            ValueError: При несовместимой структуре файла
        """
        with open(filename, 'r') as file:
            data = json.load(file)

        # Проверка совместимости
        if (len(data['W']) != self.n_recurrent or
                len(data['W'][0]) != self.n_neurons):
            raise ValueError("Несовместимая структура весов")

        self.W = np.array(data['W'], dtype=np.float32)
        self.state = np.array(data['state'], dtype=np.float32)
