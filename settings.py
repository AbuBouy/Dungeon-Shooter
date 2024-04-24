import pygame

# Program Settings
GAME_TITLE = "Dungeon Destruction"
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 720
FPS = 60
BG_COLOUR = "gray"


# Player Settings
MAX_PLAYER_HEALTH = 150
PLAYER_SPEED = 5
INVENTORY_SIZE = 3
INVENTORY_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3]
RELOAD_KEY = pygame.K_r

# Score constants
MINUTE_POINTS = 5
ELIM_POINTS = 10

# Map dimensions
TILE_SIZE = 90
MAP_WIDTH = WINDOW_WIDTH * 5 // TILE_SIZE
MAP_HEIGHT = WINDOW_HEIGHT * 5 // TILE_SIZE

# Image preload
FLOOR_IMAGE = pygame.transform.scale(pygame.image.load("tiles/floor.png"), (TILE_SIZE, TILE_SIZE))
WALL_IMAGE = pygame.transform.scale(pygame.image.load("tiles/wall.png"), (TILE_SIZE, TILE_SIZE))


# Mouse Crosshair
class Crosshair:
    def __init__(self):
        self.image = pygame.image.load("crosshair.png").convert_alpha()
        self.rect = self.image.get_rect()

    def update(self):
        self.rect.center = pygame.mouse.get_pos()

    def draw(self, window):
        window.blit(self.image, (self.rect.x, self.rect.y))
