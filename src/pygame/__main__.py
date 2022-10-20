import math
import numpy as np
import pygame
import pytweening
import os
import sys

from random import choice, random

from src.pygame.hud import draw_text_on_screen, draw_drive_on_screen, draw_text_on_rectangle, get_text_info
from src.pygame.settings import *
from src.pygame.sprites import Avatar, Mob, Object, Wall, Obstacle
from src.pygame.tilemap import Map, Camera, TiledMap, Spot


class Game():

    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        pygame.init()
        self.window = pygame.display.set_mode((self.width, self.height))
        self.tilesize = TILESIZE
        self.rows = self.width // self.tilesize
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.fps = FPS
        self.field_of_view = FIELD_OF_VIEW
        # self.timer = pygame.time.get_ticks()

    def load_data(self):
        # Paths
        assets_folder = os.path.join(ROOT_PROJECT_PATH, ASSETS_DIRECTORY_NAME)
        config_folder = os.path.join(ROOT_PROJECT_PATH, CONFIG_DIRECTORY_NAME)

        # Charge map
        if USE_TILED_MAP:
            self.map = TiledMap(os.path.join(ROOT_PROJECT_PATH, os.path.join(config_folder, TILEDMAP_FILE)))
            self.map_img = self.map.make_map()
            self.map_rect = self.map_img.get_rect()
        else:
            self.map = Map(os.path.join(ROOT_PROJECT_PATH, os.path.join(config_folder, MAP_FILE)))
        
        # Charge general assets
        self.avatar_img = pygame.transform.scale(pygame.image.load(os.path.join(assets_folder, AVATAR)).convert_alpha(), (self.tilesize, self.tilesize))
        self.mob_img = pygame.transform.scale(pygame.image.load(os.path.join(assets_folder, SPIDER)).convert_alpha(), (self.tilesize, self.tilesize))
        self.wall_img = pygame.transform.scale(pygame.image.load(os.path.join(assets_folder, WALL)).convert_alpha(), (self.tilesize, self.tilesize))

        # Charge object assets
        self.object_images = {}
        for object in OBJECT_IMAGES:
            self.object_images[object] = pygame.transform.scale(pygame.image.load(os.path.join(assets_folder, OBJECT_IMAGES[object])).convert_alpha(), (self.tilesize, self.tilesize))

        # Lighting effect
        self.fog = pygame.Surface((self.width, self.height))
        self.fog.fill(NIGHT_VISION)
        self.light_mask = pygame.transform.scale(pygame.image.load(os.path.join(assets_folder, LIGHT_MASK)).convert_alpha(), (self.field_of_view * 2.35, self.field_of_view * 2.35))
        self.light_rect = self.light_mask.get_rect()

        # Dim screen effect
        self.dim_screen = pygame.Surface(self.window.get_size()).convert_alpha()
        self.dim_screen.fill((0, 0, 0, 180))

    def new(self):
        # Load all initial data
        self.load_data()

        # Set the night_mode
        self.night_mode = False

        # Set the pause mode
        self.paused = False

        # Set time
        self.hours = 0
        self.days = 0

        # Set day/night cycle conditions
        self.environment_temperature = ENVIRONMENT_TEMPERATURE

        # Set map attributes
        self.on_water_source = False
        self.hitted_object = None
        self.objects_on_sight = []
        self.sight_objects = {}

        # Spawn contents of the map
        self.all_sprites = pygame.sprite.Group()
        self.avatar_sprites = pygame.sprite.Group()
        self.mob_sprites = pygame.sprite.Group()
        self.object_sprites = pygame.sprite.Group()
        self.wall_sprites = pygame.sprite.Group()

        # Set spawn coordinates
        self.spawn_coordinates = []

        if isinstance(self.map, Map):
            # This option is deprecated. Need update
            for row, line in enumerate(self.map.data):
                for col, tile in enumerate(line):
                    if tile == 'a':
                        Avatar(self, col, row)
                    elif tile == 's':
                        Mob(self, col, row)
                    elif tile == 'o':
                        random_object = choice(RANDOM_INIT)
                        if random_object in UNIQUE_ITEMS:
                            for object in self.object_sprites:
                                while random_object == object.type and object.type in UNIQUE_ITEMS:
                                    random_object = choice(RANDOM_INIT)
                        Object(self, col, row, random_object)
                    elif tile == 'w':
                        Object(self, col, row, 'water-dispenser')
                    elif tile == 'f':
                        Object(self, col, row, 'fire')
                    elif tile == '=':
                        Wall(self, col, row)
        elif isinstance(self.map, TiledMap):
            # Build graph map
            current_objects = set()
            n_objects = 0
            self.graph_map = []
            total_rows = self.map.tmxdata.height
            total_cols = self.map.tmxdata.width
            for _ in range(total_rows):
                self.graph_map.append([])
            for layer in self.map.tmxdata.visible_layers:
                for tile in layer.tiles(): # tile[0] es la x = col, tile[1] es la y = row
                    self.graph_map[tile[1]].append(Spot(tile[1], tile[0], TILESIZE, TILESIZE, total_rows, total_cols))
                break
            for tile_object in self.map.tmxdata.objects:
                if tile_object.name == 'wall':
                    self.graph_map[int(tile_object.y / tile_object.height)][int(tile_object.x / tile_object.width)].make_obstacle()
                if tile_object.name == 'object':
                    n_objects += 1

            # Update neighbors of the graph map (edges)
            for row in self.graph_map:
                for spot in row:
                    spot.update_neighbors(self.graph_map)

            # Place objects on the map
            for tile_object in self.map.tmxdata.objects:
                if tile_object.name == 'avatar':
                    Avatar(self, tile_object.x, tile_object.y)
                elif tile_object.name == 'mob':
                    Mob(self, tile_object.x, tile_object.y)
                elif tile_object.name == 'object':
                    random_object = choice(RANDOM_INIT)
                    for object in self.object_sprites:
                        current_objects.add(object.type)
                    # Avoid unique items duplication on the map
                    if random_object in UNIQUE_ITEMS and random_object in current_objects:
                        while random_object in UNIQUE_ITEMS and random_object in current_objects:
                            random_object = choice(RANDOM_INIT)
                    # Check at least one object per item in unique items
                    if (len(self.object_sprites) >= n_objects - len(UNIQUE_ITEMS)):
                        for item in UNIQUE_ITEMS:
                            if item not in current_objects:
                                random_object = item
                                break
                    Object(self, tile_object.x, tile_object.y, random_object)
                    if random_object in CONSUMABLES:
                        self.spawn_coordinates.append([tile_object.x, tile_object.y])
                elif tile_object.name == 'wall':
                    Obstacle(self, tile_object.x, tile_object.y, tile_object.width, tile_object.height)

        # Set max items
        self.max_items = len(self.object_sprites)

        # Set countdown for spawn objects
        self.n_trials = 0
        self.countdown = 0

        # Debug for collisions mode
        self.draw_debug = False

        # Spawn camera
        self.camera = Camera(self.map.width, self.map.height)

    def events(self):
        """ Here place all general events of the game """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                if event.key == pygame.K_c:
                    self.draw_debug = not self.draw_debug
                if event.key == pygame.K_n:
                    self.night_mode = not self.night_mode
                if event.key == pygame.K_e:
                    for avatar in self.avatar_sprites:
                        avatar.eat()
                if event.key == pygame.K_d and self.on_water_source:
                    for avatar in self.avatar_sprites:
                        avatar.drink()
                if event.key == pygame.K_p and self.hitted_object is not None:
                    for avatar in self.avatar_sprites:
                        if len(avatar.inventory) <= 4 and self.hitted_object.type in PICKABLE_ITEMS:
                            avatar.pick_up(self.hitted_object.type)
                            self.hitted_object.kill()
            if event.type == CUSTOM_EVENT:
                pass

    def update(self):
        """ Update window with game information """
        for avatar in self.avatar_sprites:
            # Check game over condition
            if avatar.drives.stored_energy <= 0 or avatar.drives.water <= 0:
                self.running = False
            
            # Check sleep condition
            if avatar.drives.sleepiness > 0.9:
                avatar.sleep()

            # Movement key assignments
            keys_pressed = pygame.key.get_pressed()
            self.key_movement_management(keys_pressed, avatar)

            # Updates camera position in accordance with the entity
            self.camera.update(avatar)

            # Avatar hits an object
            hits = pygame.sprite.spritecollide(avatar, self.object_sprites, False)
            for hit in hits:
                self.hit_interaction(hit)
            
            # Randomly spawn new objects at empty locations stochastically
            self.n_trials = round(abs(self.time - self.hours), 1)
            if self.n_trials >= 12:
                self.n_trials = 24 - self.n_trials
            if self.n_trials != 0:
                rest = self.n_trials - math.floor(self.n_trials)
            else:
                rest = 0
            self.countdown += rest
            self.countdown = round(self.countdown, 1)
            for _ in range(math.floor(self.n_trials)):
                capacity_items = (len(self.object_sprites) - (len(UNIQUE_ITEMS) - 1)) / (self.max_items - (len(UNIQUE_ITEMS) - 1))
                if random() < pytweening.easeInQuad(1-capacity_items):
                    x_r, y_r = choice(self.spawn_coordinates)
                    o_coordinates = []
                    for o in self.object_sprites:
                        if o.type in CONSUMABLES:
                            o_coordinates.append([o.rect.x, o.rect.y])
                    if (len(self.spawn_coordinates) == len(o_coordinates)):
                        break
                    while [int(x_r), int(y_r)] in o_coordinates:
                        x_r, y_r = choice(self.spawn_coordinates)
                    self.spawn_new_object(x_r, y_r, choice(COMMON_ITEMS))
            if self.countdown >= 1:
                for _ in range(math.floor(self.countdown)):
                    capacity_items = (len(self.object_sprites) - (len(UNIQUE_ITEMS) - 1)) / (self.max_items - (len(UNIQUE_ITEMS) - 1))
                    if random() < pytweening.easeInQuad(1-capacity_items):
                        x_r, y_r = choice(self.spawn_coordinates)
                        o_coordinates = []
                        for o in self.object_sprites:
                            if o.type in CONSUMABLES:
                                o_coordinates.append([o.rect.x, o.rect.y])
                        if (len(self.spawn_coordinates) == len(o_coordinates)):
                            break
                        while [int(x_r), int(y_r)] in o_coordinates:
                            x_r, y_r = choice(self.spawn_coordinates)
                        self.spawn_new_object(x_r, y_r, choice(COMMON_ITEMS))
                self.countdown = 1 - math.floor(self.countdown)
            self.n_trials = 0

            # Update day/night cycle conditions
            if self.hours >= 22 or self.hours < 6:
                self.environment_temperature = ENVIRONMENT_TEMPERATURE - 10
            else:
                self.environment_temperature = ENVIRONMENT_TEMPERATURE
            avatar.drives.update_bmr(self.environment_temperature)
        
        # Update objects
        for object in self.object_sprites:
            object.update()

    def hit_interaction(self, hit):
        self.hitted_object = hit
        if (hit.type == 'water-dispenser'):
            self.on_water_source = True

    def key_movement_management(self, keys_pressed, avatar):
        try:
            if keys_pressed[pygame.K_LEFT]:
                avatar.movement(-1, 0)
            if keys_pressed[pygame.K_RIGHT]:
                avatar.movement(1, 0)
            if keys_pressed[pygame.K_UP]:
                avatar.movement(0, -1)
            if keys_pressed[pygame.K_DOWN]:
                avatar.movement(0, 1)
        finally:
            self.on_water_source = False
            self.hitted_object = None

    def quit(self):
        pygame.quit()
        sys.exit()
        
    def run(self):
        self.running = True
        while self.running:
            # Setup fps
            self.clock.tick(self.fps)

            # Setup time
            self.time = self.hours

            # Events
            self.events()

            # Update information of the map
            if not self.paused:
                self.update()

            # Draw the map
            self.draw_window()

    def raycasting(self):
        self.objects_on_sight = []
        self.sight_objects = {}
        # Check to see if the avatar can see any objects or mobs
        def iterate_over(sprites):
            for sprite in sprites:
                sprite_center = self.camera.apply(sprite).center
                distance = math.sqrt((sprite_center[0]-avatar_center[0])**2 + (sprite_center[1]-avatar_center[1])**2)
                if distance <= self.field_of_view:
                    # Does the line <avatar> to <sprite> intersect any obstacles?
                    line_of_sight = [avatar_center[0], avatar_center[1], sprite_center[0], sprite_center[1]]
                    found = True
                    for wall in self.wall_sprites:
                    # is anyting walling the line-of-sight?
                        intersection_points = self.line_rect_intersection_points(line_of_sight, self.camera.apply(wall))
                        if (len(intersection_points) > 0):
                            found = False
                            break # seen already
                    if (found):
                        pygame.draw.line(self.window, GREEN, avatar_center, sprite_center)
                        self.sight_objects.update({sprite: distance})
                    else:
                        pygame.draw.line(self.window, RED, avatar_center, sprite_center)
                    self.objects_on_sight.append(found)

        for avatar in self.avatar_sprites:
            avatar_center = self.camera.apply(avatar).center
            iterate_over(self.mob_sprites)
            iterate_over(self.object_sprites)

    def line_rect_intersection_points(self, line, rect):
        """ Get the list of points where the line and rect intersect. The result may be zero, one or two points.

            BUG: This function fails when the line and the side of the rectangle overlap """

        def are_lines_parallel(x1, y1, x2, y2, x3, y3, x4, y4):
            """ Return True if the given lines (x1,y1)-(x2,y2) and (x3,y3)-(x4,y4) are parallel """
            return (((x1-x2)*(y3-y4)) - ((y1-y2)*(x3-x4)) == 0)

        def intersection_point(x1, y1, x2, y2, x3, y3, x4, y4):
            """ Return the point where the lines through (x1,y1)-(x2,y2) and (x3,y3)-(x4,y4) cross """
            # Use determinant method, as per Ref: https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection
            px = ((((x1*y2)-(y1*x2))*(x3 - x4)) - ((x1-x2)*((x3*y4)-(y3*x4)))) / (((x1-x2)*(y3-y4)) - ((y1-y2)*(x3-x4)))
            py = ((((x1*y2)-(y1*x2))*(y3 - y4)) - ((y1-y2)*((x3*y4)-(y3*x4)))) / (((x1-x2)*(y3-y4)) - ((y1-y2)*(x3-x4)))
            return px, py

        ### Begin the intersection tests
        result = []
        line_x1, line_y1, line_x2, line_y2 = line
        pos_x, pos_y, width, height = rect

        ### Convert the rectangle into 4 lines
        rect_lines = [(pos_x, pos_y, pos_x + width, pos_y), (pos_x, pos_y + height, pos_x + width, pos_y + height),  # top & bottom
                    (pos_x, pos_y, pos_x, pos_y + height), (pos_x + width, pos_y, pos_x + width, pos_y + height)] # left & right

        ### intersect each rect-side with the line
        for r in rect_lines:
            rx1, ry1, rx2, ry2 = r
            if not are_lines_parallel(line_x1, line_y1, line_x2, line_y2, rx1, ry1, rx2, ry2):
                pX, pY = intersection_point(line_x1, line_y1, line_x2, line_y2, rx1, ry1, rx2, ry2)
                pX = round(pX)
                pY = round(pY)
                # Lines intersect, but is on the rectangle, and between the line end-points?
                if (rect.collidepoint(pX, pY) and pX >= min(line_x1, line_x2) and
                    pX <= max(line_x1, line_x2) and pY >= min(line_y1, line_y2) and
                    pY <= max(line_y1, line_y2)):
                    pygame.draw.circle(self.window, BLACK, (pX, pY), 4)
                    result.append((pX, pY))
                    if (len(result) == 2):
                        break   # Once we've found 2 intersection points, that's it
        return result

    def draw_fog(self):
        # Draw the light mask (gradient) onto the fog image
        self.fog.fill(NIGHT_VISION)
        for avatar in self.avatar_sprites:
            self.light_rect.center = self.camera.apply(avatar).center
        self.fog.blit(self.light_mask, self.light_rect)
        self.window.blit(self.fog, (0, 0), special_flags=pygame.BLEND_MULT)

    def draw_night(self):
        self.fog.fill(NIGHT_COLOR)
        self.window.blit(self.fog, (0, 0), special_flags=pygame.BLEND_MULT)

    def draw_grid(self):
        for x in range(0, self.width, self.tilesize):
            pygame.draw.line(self.window, GREY, (x, 0), (x, self.height))
        for y in range(0, self.height, self.tilesize):
            pygame.draw.line(self.window, GREY, (0, y), (self.width, y))

    def draw_window(self):
        # Note: This is just for development stage. It shows the fps info on the screen
        pygame.display.set_caption("{:.2f}".format(self.clock.get_fps()))
        
        # Draw background
        if isinstance(self.map, Map):
            self.window.fill(WOOD)
        elif isinstance(self.map, TiledMap):
            self.window.blit(self.map_img, self.camera.apply_rect(self.map_rect))

        # Draw grid
        self.draw_grid()

        # Draw content of the map on the camera area
        for sprite in self.all_sprites:
            self.window.blit(sprite.image, self.camera.apply(sprite))
            if self.draw_debug:
                pygame.draw.rect(self.window, CYAN, self.camera.apply_rect(sprite.rect), 1)
        if isinstance(self.map, TiledMap):
            if self.draw_debug:
                for wall in self.wall_sprites:
                    pygame.draw.rect(self.window, CYAN, self.camera.apply_rect(wall.rect), 1)

        # Draw area of vision
        for avatar in self.avatar_sprites:
            pygame.draw.circle(self.window, VIOLET, self.camera.apply(avatar).center, self.field_of_view, 1)

        # Draw line of vision
        self.raycasting()

        # Draw day/night cycle
        if self.hours >= 22 or self.hours < 6:
            self.draw_night()

        # Draw fog
        if self.night_mode:
            self.draw_fog()

        # Draw HUD functions
        for avatar in self.avatar_sprites:
            pygame.draw.rect(self.window, ANTIQUE_WHITE, pygame.Rect(0, 7, 210, 40))
            energy_bar = avatar.drives.stored_energy if avatar.drives.stored_energy >= avatar.drives.standard_kcalh_production()[0] else avatar.drives.standard_kcalh_production()[0]
            draw_drive_on_screen(self.window, 60, 10, avatar.drives.stored_energy, energy_bar, "Energy")
            draw_drive_on_screen(self.window, 60, 22, avatar.drives.water, BASAL_WATER, "Water")
            draw_drive_on_screen(self.window, 60, 34, 1 - avatar.drives.sleepiness, 1, "Sleepiness")
            _, width_temp, height_temp, surf_temp, rect_temp = get_text_info(f"ENV TEMPERATURE: {avatar.drives.perceived_temperature}", "monospace", 15, BLACK, self.width - (self.width / 2), 10, "center")
            _, width_time, height_time, surf_time, rect_time = get_text_info(f"DAYS: {self.days} HOURS: {self.hours:.2f}", "monospace", 15, BLACK, self.width - (self.width / 2), 25, "center")
            x_inv, width_inv, height_inv, surf_inv, rect_inv = get_text_info(f"INVENTORY: {list(avatar.inventory)}", "monospace", 15, BLACK, self.width - (self.width / 2), 40, "center")
            surfaces, rectangles = [surf_temp, surf_time, surf_inv], [rect_temp, rect_time, rect_inv]
            draw_text_on_rectangle(self.window, x_inv - (max(width_inv, width_temp, width_time) / 2) - 2, 2, max(width_temp, width_time, width_inv) + 4, height_temp + height_time + height_inv + 2, ANTIQUE_WHITE, surfaces, rectangles)
        if self.paused:
            self.window.blit(self.dim_screen, (0, 0))
            draw_text_on_screen(self.window, "Paused", "monospace", 50, WHITE, self.width / 2, self.height / 2, "center")

        # Update display
        pygame.display.update()

    def end_screen(self):
        self.window.fill(BLACK)
        draw_text_on_screen(self.window, "Press a key to restart", "monospace", 50, WHITE, self.width / 2, self.height / 2, "center")
        pygame.display.update()
        self.restart()
    
    def restart(self):
        pygame.event.wait()
        self.waiting = True
        while self.waiting:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.waiting = False
                    self.quit()
                if event.type == pygame.K_ESCAPE:
                    self.waiting = False
                    self.quit()
                if event.type == pygame.KEYUP:
                    self.waiting = False

    def _get_obs(self):
        for avatar in self.avatar_sprites:
            return {#"avatar_position": np.array([avatar.pos.x, avatar.pos.y], dtype=np.int32),
                    "environment_temperature": np.array([self._normalize_value(avatar.drives.perceived_temperature, 20, 40)], dtype=np.float32),
                    "energy_stored": np.array([self._normalize_value(avatar.drives.stored_energy, 0, 4000)], dtype=np.float32),
                    "water_stored": np.array([self._normalize_value(avatar.drives.water, 0, 4)], dtype=np.float32),
                    "sleepiness": np.array([avatar.drives.sleepiness], dtype=np.float32),
                    "objects_at_sight": np.array([any(self.objects_on_sight)], dtype=np.int32),
                    "objects_on_inventory": np.array([int(bool(avatar.inventory))], dtype=np.int32),
                    "on_water_source": np.array([int(self.on_water_source)], dtype=np.int32),
                    "on_object": np.array([int(bool(self.hitted_object))], dtype=np.int32)
                    }
    
    def _normalize_value(self, value, min_range, max_range):
        # Min-max normalization
        return (value - min_range)/(max_range - min_range)

    def spawn_new_object(self, x, y, name):
        Object(self, x, y, name)


# ---------- Main algorithm -----------
# -------------------------------------

def main():
    game = Game()

    while True:
        game.new()
        game.run()
        game.end_screen()

if __name__ == "__main__":
    main()
