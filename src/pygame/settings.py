import os
import pygame


# SECTION 1. COLORS
WHITE = (255, 255, 255)
GREY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 201, 87)
BLUE = (0, 0, 255)
YELLOW = (255, 236, 139)
CYAN = (0, 255, 255)
BLACK = (0, 0, 0)
BROWN = (138, 54, 15)
WOOD = (205, 192, 176)
VIOLET = (148, 0, 211)
NIGHT_VISION = (40, 40, 40)
NIGHT_COLOR = (100, 100, 100)


# SECTION 2. PATHS

# 2.3. General paths
ROOT_PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# 2.2. Config
CONFIG_DIRECTORY_NAME = 'config'

# 2.3. Assets
ASSETS_DIRECTORY_NAME = 'assets'
AVATAR = 'bot.png'
SPIDER = 'spider.png'
FOOD = 'hamburguer.png'
WALL = 'bricks_wall.png'
LIGHT_MASK = 'light_350_med.png'


# SECTION 3. GAME SETTINGS

# 3.1. General settings
WIDTH = 1024
HEIGHT = 768
TILESIZE = 64
TITLE = "TIMIK v0.1"
FPS = 60
MAP_FILE = 'map.txt'
USE_TILED_MAP = True
TILEDMAP_FILE = 'custom_map_one.tmx'
FIELD_OF_VIEW = TILESIZE * 10

# 3.2. Environment settings
ENVIRONMENT_TEMPERATURE = 30 # [ºC]

# 3.3. Avatar settings
BODY_TEMPERATURE = 37 # [ºC]
STORED_ENERGY = 3000 # [kcal]
BASAL_ENERGY = 130000 # [kcal] Reference: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3302369/
BODY_AREA = 1.8 # [m²]
MATERIAL_THICKNESS = 0.003 # [m]
STORED_WATER = 3 # [l]
BASAL_WATER = 4 # [l]
BASAL_METABOLIC_RATE = 80 # [W]


# SECTION 4. OBJECTS

# 4.1. Bobbing animation
ENABLE_ANIMATION = False
BOB_RANGE = 15
BOB_SPEED = 0.5

# 4.2. Full list of assets
OBJECT_IMAGES = {'apple': 'apple.png', 'hamburguer': 'hamburguer.png', 'cup': 'cup.png', 'water-dispenser': 'water-dispenser.png', 'fire': 'fire.png'}
RANDOM_INIT = ['apple', 'hamburguer', 'cup', 'water-dispenser', 'fire']
UNIQUE_ITEMS = ['cup', 'water-dispenser', 'fire']

# 4.3. Object attributes
CONSUMABLES = {'apple': {'kcal': 119},
               'hamburguer': {'kcal': 550}
               }
NON_CONSUMABLES = {'cup': {'capacity': 0.33},
                   'water-dispenser': {'perishable': False},
                   'fire': {'activation_radius': 400, 'perishable': False}
                   }


# SECTION 5. ACTIONS

# 5.1. Action definitions
# For required_energy, all the values do not include the BMR. Given in [W/s]
ACTIONS = {"stand": {"required_energy": 45, "required_time": 0.1},
           "movement": {"required_energy": 115, "required_time": 0.1},
           "eat": {"required_energy": 0, "required_time": 0.5},
           "drink": {"required_energy": 0, "required_time": 0.01},
           "pickup": {"required_energy": 0, "required_time": 0.01},
           "sleep": {"required_energy": 0, "required_time": 8}
           }

# 5.2. User events
CUSTOM_EVENT = pygame.USEREVENT + 1