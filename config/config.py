import pygame

WIDTH, HEIGHT = 1100, 700
FPS = 60

pygame.init
FONT = pygame.font.SysFont("arial", 24)
BIG = pygame.font.SysFont("arial", 42, bold=True)
SMALL = pygame.font.SysFont("arial", 18)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
LIGHT = (230, 230, 230)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
BLUE = (52, 152, 219)
YELLOW = (241, 196, 15)
ORANGE = (243, 156, 18)
PURPLE = (155, 89, 182)

TIMER = 60
PRIZE_CAP = 25

REFERENCE_KEY = [
    "RUBY-Δ1",
    "GEAR-A",
    "RUBY-◇2",
    "GEAR-B",
    "RUBY-◇3",
]

ITEMS = [
    "RUBY-Δ1", "GEAR-A", "RUBY-◇2", "GEAR-B", "RUBY-◇3",
    "GEAR-C", "RUBY-◇4", "GEAR-D", "RUBY-Δ2", "GEAR-E",
]
