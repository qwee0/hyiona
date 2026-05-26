#!/usr/bin/env python3
"""
Классическая игра «Змейка» на Pygame с процедурной графикой.
Все текстуры генерируются внутри кода — внешние файлы не требуются.

Запуск: python snake.py
Управление: Стрелки — движение, P — пауза, Esc — выход
"""

import pygame
import random
import math
import os
from typing import List, Tuple, Optional, Dict
from enum import Enum, auto

# =============================================================================
# КОНСТАНТЫ И НАСТРОЙКИ
# =============================================================================

# Размеры сетки и клеток
GRID_WIDTH = 20  # количество клеток по горизонтали
GRID_HEIGHT = 20  # количество клеток по вертикали
CELL_SIZE = 32  # размер клетки в пикселях

# Отступы для интерфейса
UI_TOP_HEIGHT = 60  # высота верхней панели

# Размеры окна
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = UI_TOP_HEIGHT + GRID_HEIGHT * CELL_SIZE

# Частота кадров
FPS = 60

# Начальная скорость змеи (обновлений в секунду)
INITIAL_SNAKE_SPEED = 8.0

# Увеличение скорости каждые N съеденных яблок
SPEED_INCREASE_EVERY = 5
SPEED_INCREASE_PERCENT = 1.10  # +10%

# Цвета
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (220, 50, 50)
COLOR_DARK_GREEN = (34, 139, 34)
COLOR_GREEN = (76, 175, 80)
COLOR_LIGHT_GREEN = (129, 199, 132)
COLOR_YELLOW_GREEN = (186, 220, 88)
COLOR_BROWN = (139, 69, 19)
COLOR_GOLD = (255, 215, 0)
COLOR_GRAY = (128, 128, 128)
COLOR_DARK_GRAY = (64, 64, 64)

# Направления
class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

# Состояния игры
class GameState(Enum):
    START = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()

# Путь к файлу рекорда
RECORD_FILE = "snake_record.txt"


# =============================================================================
# ГЕНЕРАТОР ТЕКСТУР
# =============================================================================

class TextureGenerator:
    """
    Класс для процедурной генерации всех текстур игры.
    Использует кэширование для оптимизации.
    """
    
    _cache: Dict[str, pygame.Surface] = {}
    
    @staticmethod
    def get_texture(name: str) -> pygame.Surface:
        """Получить текстуру по имени (создаёт если нет в кэше)."""
        if name not in TextureGenerator._cache:
            TextureGenerator._cache[name] = TextureGenerator._generate(name)
        return TextureGenerator._cache[name].copy()
    
    @staticmethod
    def _generate(name: str) -> pygame.Surface:
        """Сгенерировать текстуру по имени."""
        if name == "grass_tile":
            return TextureGenerator._create_grass_tile()
        elif name == "snake_head":
            return TextureGenerator._create_snake_head()
        elif name == "snake_body":
            return TextureGenerator._create_snake_body()
        elif name == "snake_tail":
            return TextureGenerator._create_snake_tail()
        elif name == "apple":
            return TextureGenerator._create_apple()
        elif name == "particle":
            return TextureGenerator._create_particle()
        else:
            # Возвращаем пустую поверхность по умолчанию
            return pygame.Surface((CELL_SIZE, CELL_SIZE))
    
    @staticmethod
    def _create_grass_tile() -> pygame.Surface:
        """
        Создать текстуру травяной плитки с вариацией оттенков.
        Использует шумоподобный паттерн из случайных точек.
        """
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
        
        # Базовый цвет травы
        base_colors = [COLOR_DARK_GREEN, COLOR_GREEN, COLOR_LIGHT_GREEN]
        
        for y in range(CELL_SIZE):
            for x in range(CELL_SIZE):
                # Создаём псевдо-шум на основе координат
                noise_val = (x * 7 + y * 13) % 100
                if noise_val < 33:
                    color = base_colors[0]
                elif noise_val < 66:
                    color = base_colors[1]
                else:
                    color = base_colors[2]
                
                # Добавляем небольшие вариации
                variation = ((x + y) % 5) - 2
                color = tuple(max(0, min(255, c + variation * 3)) for c in color)
                surface.set_at((x, y), color)
        
        # Добавляем несколько "травинок"
        for _ in range(15):
            x = random.randint(0, CELL_SIZE - 1)
            y = random.randint(0, CELL_SIZE - 1)
            grass_color = tuple(min(255, c + 20) for c in COLOR_LIGHT_GREEN)
            if y > 0:
                surface.set_at((x, y - 1), grass_color)
            surface.set_at((x, y), grass_color)
        
        return surface
    
    @staticmethod
    def _create_snake_head() -> pygame.Surface:
        """
        Создать текстуру головы змеи с глазами, ноздрями и язычком.
        Имеет скруглённые углы и чешуйчатый узор.
        """
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        
        # Основной цвет головы
        head_color = COLOR_GREEN
        scale_color = tuple(max(0, c - 20) for c in COLOR_GREEN)
        
        # Рисуем основную форму (скруглённый прямоугольник)
        head_rect = pygame.Rect(4, 4, CELL_SIZE - 8, CELL_SIZE - 8)
        pygame.draw.ellipse(surface, head_color, head_rect)
        
        # Чешуйчатый узор (маленькие ромбики)
        for i in range(3):
            for j in range(3):
                cx = 8 + i * 8
                cy = 8 + j * 8
                # Рисуем маленький ромб
                points = [
                    (cx, cy - 3),
                    (cx + 3, cy),
                    (cx, cy + 3),
                    (cx - 3, cy)
                ]
                pygame.draw.polygon(surface, scale_color, points)
        
        # Глаза (будут добавлены в зависимости от направления при отрисовке)
        # Здесь рисуем базовые позиции для направления вправо
        eye_white = COLOR_WHITE
        eye_pupil = COLOR_BLACK
        
        # Левый глаз
        pygame.draw.circle(surface, eye_white, (22, 10), 4)
        pygame.draw.circle(surface, eye_pupil, (23, 10), 2)
        
        # Правый глаз
        pygame.draw.circle(surface, eye_white, (22, 22), 4)
        pygame.draw.circle(surface, eye_pupil, (23, 22), 2)
        
        # Ноздри
        nostril_color = tuple(max(0, c - 40) for c in COLOR_GREEN)
        pygame.draw.circle(surface, nostril_color, (26, 14), 1)
        pygame.draw.circle(surface, nostril_color, (26, 18), 1)
        
        # Язычок (красный, раздвоенный)
        tongue_color = COLOR_RED
        tongue_points = [(28, 16), (32, 14), (30, 16), (32, 18)]
        pygame.draw.polygon(surface, tongue_color, tongue_points)
        
        return surface
    
    @staticmethod
    def _create_snake_body() -> pygame.Surface:
        """
        Создать текстуру сегмента тела змеи с чешуйчатым узором.
        """
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        
        # Цвет тела (чуть темнее головы)
        body_color = tuple(max(0, c - 15) for c in COLOR_GREEN)
        scale_color = tuple(max(0, c - 30) for c in COLOR_GREEN)
        
        # Основная форма (круг/эллипс)
        body_rect = pygame.Rect(4, 4, CELL_SIZE - 8, CELL_SIZE - 8)
        pygame.draw.ellipse(surface, body_color, body_rect)
        
        # Чешуйчатый узор
        center_x, center_y = CELL_SIZE // 2, CELL_SIZE // 2
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            sx = int(center_x + math.cos(rad) * 8)
            sy = int(center_y + math.sin(rad) * 8)
            pygame.draw.circle(surface, scale_color, (sx, sy), 3)
        
        # Центральный узор
        pygame.draw.circle(surface, scale_color, (center_x, center_y), 4)
        
        return surface
    
    @staticmethod
    def _create_snake_tail() -> pygame.Surface:
        """
        Создать текстуру хвоста змеи (зауженный сегмент).
        """
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        
        # Цвет хвоста (ещё темнее)
        tail_color = tuple(max(0, c - 25) for c in COLOR_GREEN)
        scale_color = tuple(max(0, c - 40) for c in COLOR_GREEN)
        
        # Зауженная форма (треугольник/конус)
        tail_points = [
            (4, 8),
            (4, 24),
            (28, 16),
            (32, 16)
        ]
        pygame.draw.polygon(surface, tail_color, tail_points)
        
        # Детали
        for i in range(3):
            x = 8 + i * 6
            pygame.draw.circle(surface, scale_color, (x, 16), 2)
        
        return surface
    
    @staticmethod
    def _create_apple() -> pygame.Surface:
        """
        Создать текстуру яблока с глянцевым бликом и листочком.
        """
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        
        # Тень под яблоком
        shadow_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surface, (0, 0, 0, 50), 
                          (8, CELL_SIZE - 10, CELL_SIZE - 16, 8))
        surface.blit(shadow_surface, (0, 0))
        
        # Основное яблоко (красный круг)
        apple_center = (CELL_SIZE // 2, CELL_SIZE // 2 + 2)
        apple_radius = 12
        pygame.draw.circle(surface, COLOR_RED, apple_center, apple_radius)
        
        # Градиент/блик для объёма
        highlight_color = (255, 100, 100)
        pygame.draw.circle(surface, highlight_color, 
                          (apple_center[0] - 4, apple_center[1] - 4), 5)
        
        # Глянцевый блик (белый)
        gloss_color = (255, 255, 255, 200)
        gloss_surface = pygame.Surface((6, 4), pygame.SRCALPHA)
        pygame.draw.ellipse(gloss_surface, gloss_color, (0, 0, 6, 4))
        surface.blit(gloss_surface, (apple_center[0] - 6, apple_center[1] - 8))
        
        # Стебелёк
        stem_color = COLOR_BROWN
        pygame.draw.rect(surface, stem_color, 
                        (apple_center[0] - 1, apple_center[1] - apple_radius - 2, 2, 6))
        
        # Листочек
        leaf_color = COLOR_LIGHT_GREEN
        leaf_points = [
            (apple_center[0], apple_center[1] - apple_radius),
            (apple_center[0] + 8, apple_center[1] - apple_radius - 4),
            (apple_center[0] + 4, apple_center[1] - apple_radius + 2)
        ]
        pygame.draw.polygon(surface, leaf_color, leaf_points)
        
        return surface
    
    @staticmethod
    def _create_particle() -> pygame.Surface:
        """Создать текстуру частицы для эффектов."""
        surface = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(surface, COLOR_GOLD, (4, 4), 3)
        pygame.draw.circle(surface, COLOR_WHITE, (3, 3), 1)
        return surface


# =============================================================================
# КЛАСС ЗМЕИ
# =============================================================================

class Snake:
    """
    Класс змеи. Хранит сегменты, направление, методы движения и роста.
    """
    
    def __init__(self, start_pos: Tuple[int, int]):
        """
        Инициализировать змею.
        
        Args:
            start_pos: Начальная позиция головы (x, y) в координатах сетки.
        """
        self.segments: List[Tuple[int, int]] = [start_pos]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.grow_pending = False
        self.alive = True
    
    def set_direction(self, new_dir: Direction) -> None:
        """
        Установить новое направление (с проверкой на разворот на 180°).
        """
        opposites = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT
        }
        
        # Нельзя развернуться на 180 градусов
        if opposites.get(self.direction) != new_dir:
            self.next_direction = new_dir
    
    def move(self) -> Tuple[int, int]:
        """
        Переместить змею на одну клетку.
        
        Returns:
            Позицию головы после движения или None если змея мертва.
        """
        if not self.alive:
            return self.segments[0]
        
        # Применяем направление
        self.direction = self.next_direction
        
        # Вычисляем новую позицию головы
        head_x, head_y = self.segments[0]
        
        if self.direction == Direction.UP:
            new_head = (head_x, head_y - 1)
        elif self.direction == Direction.DOWN:
            new_head = (head_x, head_y + 1)
        elif self.direction == Direction.LEFT:
            new_head = (head_x - 1, head_y)
        else:  # RIGHT
            new_head = (head_x + 1, head_y)
        
        # Добавляем новую голову
        self.segments.insert(0, new_head)
        
        # Удаляем хвост если не растём
        if not self.grow_pending:
            self.segments.pop()
        else:
            self.grow_pending = False
        
        return new_head
    
    def grow(self) -> None:
        """Запланировать рост змеи на один сегмент."""
        self.grow_pending = True
    
    def check_collision(self, grid_width: int, grid_height: int) -> bool:
        """
        Проверить столкновения со стенами или собственным телом.
        
        Returns:
            True если есть столкновение (змея должна умереть).
        """
        if not self.segments:
            return False
        
        head_x, head_y = self.segments[0]
        
        # Столкновение со стенами
        if head_x < 0 or head_x >= grid_width:
            return True
        if head_y < 0 or head_y >= grid_height:
            return True
        
        # Столкновение с собственным телом
        if self.segments.count(self.segments[0]) > 1:
            return True
        
        return False
    
    def get_head_pos(self) -> Tuple[int, int]:
        """Вернуть позицию головы."""
        return self.segments[0] if self.segments else (0, 0)
    
    def kill(self) -> None:
        """Убить змею."""
        self.alive = False
    
    def reset(self, start_pos: Tuple[int, int]) -> None:
        """Сбросить змею к начальному состоянию."""
        self.segments = [start_pos]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.grow_pending = False
        self.alive = True


# =============================================================================
# КЛАСС ЯБЛОКА
# =============================================================================

class Apple:
    """
    Класс яблока (еды).
    """
    
    def __init__(self, position: Tuple[int, int]):
        """
        Инициализировать яблоко.
        
        Args:
            position: Позиция яблока в координатах сетки.
        """
        self.position = position
        self.texture = TextureGenerator.get_texture("apple")
    
    def draw(self, screen: pygame.Surface, offset_x: int, offset_y: int) -> None:
        """
        Нарисовать яблоко на экране.
        
        Args:
            screen: Поверхность для отрисовки.
            offset_x: Смещение по X (для UI).
            offset_y: Смещение по Y (для UI).
        """
        x = self.position[0] * CELL_SIZE + offset_x
        y = self.position[1] * CELL_SIZE + offset_y
        screen.blit(self.texture, (x, y))
    
    def respawn(self, position: Tuple[int, int]) -> None:
        """Переместить яблоко в новую позицию."""
        self.position = position


# =============================================================================
# КЛАСС ЧАСТИЦ (ЭФФЕКТЫ)
# =============================================================================

class Particle:
    """Частица для визуальных эффектов."""
    
    def __init__(self, x: float, y: float, vx: float, vy: float, lifetime: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.age = 0.0
        self.texture = TextureGenerator.get_texture("particle")
    
    def update(self, dt: float) -> bool:
        """
        Обновить частицу.
        
        Returns:
            True если частица ещё жива.
        """
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 50 * dt  # Гравитация
        return self.age < self.lifetime
    
    def draw(self, screen: pygame.Surface, offset_x: int, offset_y: int) -> None:
        """Нарисовать частицу."""
        alpha = int(255 * (1 - self.age / self.lifetime))
        particle_surface = self.texture.copy()
        particle_surface.set_alpha(alpha)
        screen.blit(particle_surface, (int(self.x) + offset_x, int(self.y) + offset_y))


class ParticleSystem:
    """Система частиц для эффектов."""
    
    def __init__(self):
        self.particles: List[Particle] = []
    
    def emit(self, x: float, y: float, count: int = 10) -> None:
        """Создать взрыв частиц в точке."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.2, 0.4)
            self.particles.append(Particle(x, y, vx, vy, lifetime))
    
    def update(self, dt: float) -> None:
        """Обновить все частицы."""
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def draw(self, screen: pygame.Surface, offset_x: int, offset_y: int) -> None:
        """Нарисовать все частицы."""
        for p in self.particles:
            p.draw(screen, offset_x, offset_y)


# =============================================================================
# ОСНОВНОЙ КЛАСС ИГРЫ
# =============================================================================

class Game:
    """
    Главный класс игры. Управляет игровым циклом, состояниями и отрисовкой.
    """
    
    def __init__(self):
        """Инициализировать игру."""
        pygame.init()
        pygame.display.set_caption("Змейка")
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Шрифт для интерфейса
        self.font = pygame.font.Font(None, 36)
        self.large_font = pygame.font.Font(None, 72)
        
        # Загрузка/создание фоновой текстуры
        self.grass_texture = TextureGenerator.get_texture("grass_tile")
        
        # Игровые объекты
        self.snake = Snake((GRID_WIDTH // 2, GRID_HEIGHT // 2))
        self.apple = Apple(self._get_random_free_position())
        self.particles = ParticleSystem()
        
        # Состояние игры
        self.state = GameState.START
        self.score = 0
        self.record = self._load_record()
        self.apples_eaten = 0
        self.snake_speed = INITIAL_SNAKE_SPEED
        
        # Таймеры
        self.move_timer = 0.0
        self.flash_timer = 0.0
        self.flash_alpha = 0
        
        # Для отрисовки
        self.offset_x = 0
        self.offset_y = UI_TOP_HEIGHT
    
    def _load_record(self) -> int:
        """Загрузить рекорд из файла."""
        try:
            if os.path.exists(RECORD_FILE):
                with open(RECORD_FILE, 'r') as f:
                    return int(f.read().strip())
        except (ValueError, IOError):
            pass
        return 0
    
    def _save_record(self) -> None:
        """Сохранить рекорд в файл."""
        try:
            with open(RECORD_FILE, 'w') as f:
                f.write(str(self.record))
        except IOError:
            pass
    
    def _get_random_free_position(self) -> Tuple[int, int]:
        """Получить случайную свободную позицию (не занятую змеёй)."""
        while True:
            pos = (random.randint(0, GRID_WIDTH - 1), 
                   random.randint(0, GRID_HEIGHT - 1))
            if pos not in self.snake.segments:
                return pos
    
    def _handle_events(self) -> bool:
        """
        Обработать события ввода.
        
        Returns:
            False если нужно выйти из игры.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                
                if self.state == GameState.START:
                    self.state = GameState.PLAYING
                
                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_p:
                        self.state = GameState.PAUSED
                    
                    # Управление змеёй
                    if event.key == pygame.K_UP:
                        self.snake.set_direction(Direction.UP)
                    elif event.key == pygame.K_DOWN:
                        self.snake.set_direction(Direction.DOWN)
                    elif event.key == pygame.K_LEFT:
                        self.snake.set_direction(Direction.LEFT)
                    elif event.key == pygame.K_RIGHT:
                        self.snake.set_direction(Direction.RIGHT)
                
                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_p:
                        self.state = GameState.PLAYING
                
                elif self.state == GameState.GAME_OVER:
                    # Любая клавиша для перезапуска
                    self._restart_game()
        
        return True
    
    def _restart_game(self) -> None:
        """Перезапустить игру."""
        self.snake.reset((GRID_WIDTH // 2, GRID_HEIGHT // 2))
        self.apple.respawn(self._get_random_free_position())
        self.particles = ParticleSystem()
        self.score = 0
        self.apples_eaten = 0
        self.snake_speed = INITIAL_SNAKE_SPEED
        self.state = GameState.PLAYING
        self.flash_timer = 0
    
    def _update(self, dt: float) -> None:
        """Обновить логику игры."""
        if self.state != GameState.PLAYING:
            return
        
        # Движение змеи по таймеру
        self.move_timer += dt
        move_interval = 1.0 / self.snake_speed
        
        if self.move_timer >= move_interval:
            self.move_timer -= move_interval
            self._move_snake()
        
        # Обновление частиц
        self.particles.update(dt)
        
        # Таймер вспышки
        if self.flash_timer > 0:
            self.flash_timer -= dt
            self.flash_alpha = int(255 * (self.flash_timer / 0.3))
    
    def _move_snake(self) -> None:
        """Переместить змею и проверить столкновения."""
        new_head = self.snake.move()
        
        # Проверка столкновений
        if self.snake.check_collision(GRID_WIDTH, GRID_HEIGHT):
            self._game_over()
            return
        
        # Проверка съедения яблока
        if new_head == self.apple.position:
            self._eat_apple()
    
    def _eat_apple(self) -> None:
        """Обработать съедение яблока."""
        self.snake.grow()
        self.score += 10
        self.apples_eaten += 1
        
        # Эффект частиц
        apple_x = self.apple.position[0] * CELL_SIZE + CELL_SIZE // 2
        apple_y = self.apple.position[1] * CELL_SIZE + CELL_SIZE // 2
        self.particles.emit(apple_x, apple_y, 15)
        
        # Увеличение скорости
        if self.apples_eaten % SPEED_INCREASE_EVERY == 0:
            self.snake_speed *= SPEED_INCREASE_PERCENT
        
        # Новое яблоко
        self.apple.respawn(self._get_random_free_position())
    
    def _game_over(self) -> None:
        """Обработать проигрыш."""
        self.snake.kill()
        self.state = GameState.GAME_OVER
        self.flash_timer = 0.3
        
        # Обновление рекорда
        if self.score > self.record:
            self.record = self.score
            self._save_record()
    
    def _draw_background(self) -> None:
        """Нарисовать фон игрового поля."""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                screen_x = x * CELL_SIZE + self.offset_x
                screen_y = y * CELL_SIZE + self.offset_y
                self.screen.blit(self.grass_texture, (screen_x, screen_y))
    
    def _draw_snake(self) -> None:
        """Нарисовать змею."""
        if not self.snake.segments:
            return
        
        head_texture = TextureGenerator.get_texture("snake_head")
        body_texture = TextureGenerator.get_texture("snake_body")
        tail_texture = TextureGenerator.get_texture("snake_tail")
        
        for i, segment in enumerate(self.snake.segments):
            x = segment[0] * CELL_SIZE + self.offset_x
            y = segment[1] * CELL_SIZE + self.offset_y
            
            if i == 0:  # Голова
                # Поворот головы в зависимости от направления
                angle = 0
                if self.snake.direction == Direction.UP:
                    angle = -90
                elif self.snake.direction == Direction.DOWN:
                    angle = 90
                elif self.snake.direction == Direction.LEFT:
                    angle = 180
                
                rotated_head = pygame.transform.rotate(head_texture, angle)
                # Центрируем повёрнутую текстуру
                rect = rotated_head.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                self.screen.blit(rotated_head, rect)
                
                # Эффект красной вспышки при проигрыше
                if self.state == GameState.GAME_OVER and self.flash_timer > 0:
                    flash_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    pygame.draw.rect(flash_surface, (*COLOR_RED, self.flash_alpha), 
                                   (0, 0, CELL_SIZE, CELL_SIZE))
                    self.screen.blit(flash_surface, (x, y))
            
            elif i == len(self.snake.segments) - 1:  # Хвост
                self.screen.blit(tail_texture, (x, y))
            else:  # Тело
                self.screen.blit(body_texture, (x, y))
    
    def _draw_ui(self) -> None:
        """Нарисовать интерфейс (счёт, рекорд)."""
        # Полупрозрачная панель
        panel_surface = pygame.Surface((WINDOW_WIDTH, UI_TOP_HEIGHT), pygame.SRCALPHA)
        panel_color = (0, 0, 0, 150)
        pygame.draw.rect(panel_surface, panel_color, (0, 0, WINDOW_WIDTH, UI_TOP_HEIGHT))
        self.screen.blit(panel_surface, (0, 0))
        
        # Текст счёта
        score_text = f"Счёт: {self.score}"
        record_text = f"Рекорд: {self.record}"
        
        score_render = self.font.render(score_text, True, COLOR_WHITE)
        record_render = self.font.render(record_text, True, COLOR_GOLD)
        
        # Обводка текста для читаемости
        score_outline = self.font.render(score_text, True, COLOR_BLACK)
        record_outline = self.font.render(record_text, True, COLOR_BLACK)
        
        self.screen.blit(score_outline, (12, 18))
        self.screen.blit(score_render, (10, 20))
        
        self.screen.blit(record_outline, (WINDOW_WIDTH - 150, 18))
        self.screen.blit(record_render, (WINDOW_WIDTH - 152, 20))
    
    def _draw_overlay(self) -> None:
        """Нарисовать оверлей для состояний START и GAME_OVER."""
        if self.state == GameState.START:
            # Затемнение
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            # Текст
            title = self.large_font.render("ЗМЕЙКА", True, COLOR_GREEN)
            subtitle = self.font.render("Нажми любую клавишу для старта", True, COLOR_WHITE)
            
            title_outline = self.large_font.render("ЗМЕЙКА", True, COLOR_BLACK)
            subtitle_outline = self.font.render("Нажми любую клавишу для старта", True, COLOR_BLACK)
            
            title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
            subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
            
            self.screen.blit(title_outline, (title_rect.x + 2, title_rect.y + 2))
            self.screen.blit(title, title_rect)
            self.screen.blit(subtitle_outline, (subtitle_rect.x + 1, subtitle_rect.y + 1))
            self.screen.blit(subtitle, subtitle_rect)
        
        elif self.state == GameState.PAUSED:
            # Затемнение
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            text = self.large_font.render("ПАУЗА", True, COLOR_YELLOW_GREEN)
            text_outline = self.large_font.render("ПАУЗА", True, COLOR_BLACK)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            
            self.screen.blit(text_outline, (text_rect.x + 2, text_rect.y + 2))
            self.screen.blit(text, text_rect)
        
        elif self.state == GameState.GAME_OVER:
            # Затемнение
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            # Вспышка по краям
            if self.flash_timer > 0:
                edge_width = 10
                flash_color = (*COLOR_RED, self.flash_alpha)
                
                # Верх
                edge_surface = pygame.Surface((WINDOW_WIDTH, edge_width), pygame.SRCALPHA)
                edge_surface.fill(flash_color)
                self.screen.blit(edge_surface, (0, 0))
                # Низ
                self.screen.blit(edge_surface, (0, WINDOW_HEIGHT - edge_width))
                # Лево
                edge_surface = pygame.Surface((edge_width, WINDOW_HEIGHT), pygame.SRCALPHA)
                edge_surface.fill(flash_color)
                self.screen.blit(edge_surface, (0, 0))
                # Право
                self.screen.blit(edge_surface, (WINDOW_WIDTH - edge_width, 0))
            
            # Текст Game Over
            go_text = self.large_font.render("GAME OVER", True, COLOR_RED)
            score_text = self.font.render(f"Финальный счёт: {self.score}", True, COLOR_WHITE)
            record_text = self.font.render(f"Рекорд: {self.record}", True, COLOR_GOLD)
            restart_text = self.font.render("Нажми любую клавишу для рестарта", True, COLOR_WHITE)
            
            # Обводка
            go_outline = self.large_font.render("GAME OVER", True, COLOR_BLACK)
            
            go_rect = go_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
            score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            record_rect = record_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 35))
            restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80))
            
            self.screen.blit(go_outline, (go_rect.x + 2, go_rect.y + 2))
            self.screen.blit(go_text, go_rect)
            self.screen.blit(score_text, score_rect)
            self.screen.blit(record_text, record_rect)
            self.screen.blit(restart_text, restart_rect)
    
    def _draw(self) -> None:
        """Отрисовать всё на экране."""
        # Очистка
        self.screen.fill(COLOR_BLACK)
        
        # Фон
        self._draw_background()
        
        # Яблоко
        self.apple.draw(self.screen, self.offset_x, self.offset_y)
        
        # Частицы
        self.particles.draw(self.screen, self.offset_x, self.offset_y)
        
        # Змея
        self._draw_snake()
        
        # Интерфейс
        self._draw_ui()
        
        # Оверлей (меню, пауза, game over)
        self._draw_overlay()
        
        # Обновление экрана
        pygame.display.flip()
    
    def run(self) -> None:
        """Запустить главный игровой цикл."""
        running = True
        
        while running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time в секундах
            
            running = self._handle_events()
            self._update(dt)
            self._draw()
        
        pygame.quit()


# =============================================================================
# ТОЧКА ВХОДА
# =============================================================================

if __name__ == "__main__":
    game = Game()
    game.run()
