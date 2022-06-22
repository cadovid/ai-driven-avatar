import math
from random import choice
import pygame
import os
import sys

from hud import draw_text_on_screen, draw_drive_on_screen
from settings import *
from sprites import Avatar, Mob, Object, Wall, Obstacle
from tilemap import Map, Camera, TiledMap


class Game:
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
        self.timer = pygame.time.get_ticks()

    def load_data(self):
        # Paths
        game_folder = os.path.dirname(__file__)
        parent_game_folder = os.path.dirname(game_folder)
        assets_folder = os.path.join(parent_game_folder, ASSETS_DIRECTORY_NAME)
        config_folder = os.path.join(parent_game_folder, CONFIG_DIRECTORY_NAME)

        # Charge map
        if USE_TILED_MAP:
            self.map = TiledMap(os.path.join(parent_game_folder, os.path.join(config_folder, TILEDMAP_FILE)))
            self.map_img = self.map.make_map()
            self.map_rect = self.map_img.get_rect()
        else:
            self.map = Map(os.path.join(parent_game_folder, os.path.join(config_folder, MAP_FILE)))
        
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
        self.fog.fill(NIGHT_COLOR)
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

        # Set map attributes
        self.on_water_source = False
        self.hitted_object = None

        # Spawn contents of the map
        self.all_sprites = pygame.sprite.Group()
        self.avatar_sprites = pygame.sprite.Group()
        self.mob_sprites = pygame.sprite.Group()
        self.object_sprites = pygame.sprite.Group()
        self.wall_sprites = pygame.sprite.Group()

        if isinstance(self.map, Map):
            for row, line in enumerate(self.map.data):
                for col, tile in enumerate(line):
                    if tile == 'a':
                        Avatar(self, col, row)
                    elif tile == 's':
                        Mob(self, col, row)
                    elif tile == 'o':
                        Object(self, col, row, choice(RANDOM_INIT))
                    elif tile == 'w':
                        Object(self, col, row, 'water-dispenser')
                    elif tile == 'f':
                        Object(self, col, row, 'fire')
                    elif tile == '=':
                        Wall(self, col, row)
        elif isinstance(self.map, TiledMap):
            for tile_object in self.map.tmxdata.objects:
                if tile_object.name == 'avatar':
                    Avatar(self, tile_object.x, tile_object.y)
                elif tile_object.name == 'mob':
                    Mob(self, tile_object.x, tile_object.y)
                elif tile_object.name == 'object':
                    Object(self, tile_object.x, tile_object.y, choice(RANDOM_INIT))
                elif tile_object.name == 'dispenser':
                    Object(self, tile_object.x, tile_object.y, 'water-dispenser')
                elif tile_object.name == 'fire':
                    Object(self, tile_object.x, tile_object.y, 'fire')
                elif tile_object.name == 'wall':
                    Obstacle(self, tile_object.x, tile_object.y, tile_object.width, tile_object.height)

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
                self.hit_interaction(hit, avatar)

        # Update objects
        for object in self.object_sprites:
            object.update()

    def hit_interaction(self, hit, avatar):
        if hit.type in CONSUMABLES:
            self.hitted_object = hit
        elif hit.type in NON_CONSUMABLES:
            if (hit.type == 'cup') and (hit.type not in avatar.inventory):
                self.hitted_object = hit
            elif (hit.type == 'water-dispenser'):
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

            # Events
            self.events()

            # Update information of the map
            if not self.paused:
                self.update()

            # Draw the map
            self.draw_window()

    def raycasting(self):
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
                    else:
                        pygame.draw.line(self.window, RED, avatar_center, sprite_center)

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
        self.fog.fill(NIGHT_COLOR)
        for avatar in self.avatar_sprites:
            self.light_rect.center = self.camera.apply(avatar).center
        self.fog.blit(self.light_mask, self.light_rect)
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

        # Draw fog
        if self.night_mode:
            self.draw_fog()

        # Draw HUD functions
        for avatar in self.avatar_sprites:
            energy_bar = avatar.drives.stored_energy if avatar.drives.stored_energy >= avatar.drives.standard_kcalh_production()[0] else avatar.drives.standard_kcalh_production()[0]
            draw_drive_on_screen(self.window, 60, 10, avatar.drives.stored_energy, energy_bar, "Energy")
            draw_drive_on_screen(self.window, 60, 20, avatar.drives.water, BASAL_WATER, "Water")
            draw_drive_on_screen(self.window, 60, 30, 1 - avatar.drives.sleepiness, 1, "Sleepiness")
            draw_text_on_screen(self.window, f"ENVIRONMENT TEMPERATURE: {avatar.drives.environment_temperature}", "monospace", 15, BLACK, self.width - (self.width / 2), 10, "center")
            draw_text_on_screen(self.window, f"DAYS: {self.days} HOURS: {self.hours:.2f}", "monospace", 15, BLACK, self.width - (self.width / 2), 25, "center")
            draw_text_on_screen(self.window, f"INVENTORY: {list(avatar.inventory)}", "monospace", 15, BLACK, self.width - (self.width / 2), 40, "center")
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
