import pygame
import pytweening

from collections import deque
from drives import BodyDrives
from tilemap import Map, TiledMap
from settings import *


vec = pygame.math.Vector2


class Avatar(pygame.sprite.Sprite):
    def __init__(self, game, x_init_pos, y_init_pos, create_mask=False):
        # x and y position are given in terms of tiles, not pixels
        self.groups = game.all_sprites, game.avatar_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.avatar_img
        self.rect  = self.image.get_rect()
        if create_mask:
            self.mask = pygame.mask.from_surface(self.image)
        self.pos = vec(x_init_pos, y_init_pos)
        if isinstance(self.game.map, Map):
            self.rect.x = self.pos.x * self.game.tilesize
            self.rect.y = self.pos.y * self.game.tilesize
        elif isinstance(self.game.map, TiledMap):
            self.rect.x = self.pos.x
            self.rect.y = self.pos.y
        self.drives = BodyDrives(self.game.environment_temperature, self)
        self.inventory = deque()

    def update_position(self):
        if isinstance(self.game.map, Map):
            self.rect.x = self.pos.x * self.game.tilesize
            self.rect.y = self.pos.y * self.game.tilesize
        elif isinstance(self.game.map, TiledMap):
            self.rect.x = self.pos.x
            self.rect.y = self.pos.y

    def movement(self, dx=0, dy=0):
        # dx and dy is the variation in the next move in tiles
        if not self.analyze_collisions(dx, dy):
            if isinstance(self.game.map, Map):
                self.pos.x += dx
                self.pos.y += dy
            elif isinstance(self.game.map, TiledMap):
                self.pos.x += dx * self.game.tilesize
                self.pos.y += dy * self.game.tilesize
            self.update_position()
            self.drives.run_action("movement")

    def analyze_collisions(self, dx=0, dy=0):
        # dx and dy is the variation in the next move in tiles
        if isinstance(self.game.map, Map):
            for mob in self.game.mob_sprites:
                if mob.pos.x == self.pos.x + dx and mob.pos.y == self.pos.y + dy:
                    return True
            for wall in self.game.wall_sprites:
                if wall.pos.x == self.pos.x + dx and wall.pos.y == self.pos.y + dy:
                    return True
            return False
        elif isinstance(self.game.map, TiledMap):
            for mob in self.game.mob_sprites:
                if mob.pos.x == self.pos.x + (dx * self.game.tilesize) and mob.pos.y == self.pos.y + (dy * self.game.tilesize):
                    return True
            for wall in self.game.wall_sprites:
                if wall.pos.x == self.pos.x + (dx * self.game.tilesize) and wall.pos.y == self.pos.y + (dy * self.game.tilesize):
                    return True
            return False

    def add_food_intake(self, quantity):
        self.drives.update_energy(quantity)

    def add_water_intake(self, quantity):
        self.drives.update_water(quantity)

    def update_game_time(self, quantity):
        if self.game.hours + quantity < 24:
            self.game.hours += quantity
        else:
            self.game.days += 1
            self.game.hours = (self.game.hours + quantity) - 24

    def add_object_inventory(self, object):
        self.inventory.append(object)

    def remove_object_inventory(self, object):
        self.inventory.remove(object)

    def eat(self):
        if self.inventory and self.drives.stored_energy < self.drives.basal_energy:
            for object in self.inventory:
                if object in CONSUMABLES:
                    self.add_food_intake(CONSUMABLES[object]['kcal'])
                    self.inventory.remove(object)
                    self.drives.run_action("eat", CONSUMABLES[object]['kcal'])
                    break

    def drink(self):
        if self.inventory and self.drives.water < self.drives.basal_water:
            if 'cup' in self.inventory:
                self.add_water_intake(NON_CONSUMABLES['cup']['capacity'])
                self.drives.run_action("drink")

    def pick_up(self, object):
        if len(self.inventory) + 1 > 5:
            self.inventory.popleft(0)
        self.add_object_inventory(object)
        self.drives.run_action("pickup")
    
    def sleep(self):
        self.drives.run_action("sleep")
        self.drives.biological_clock = 0
        self.drives.sleepiness = 0
        self.update_game_time(8)

    def get_rect_center(self):
        return self.rect.center
    
    def get_rect(self):
        return self.rect
    
    def get_image(self):
        return self.image


class Mob(pygame.sprite.Sprite):
    def __init__(self, game, x_init_pos, y_init_pos, create_mask=False):
        # x and y position are given in terms of tiles, not pixels
        self.groups = game.all_sprites, game.mob_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.mob_img
        self.rect  = self.image.get_rect()
        if create_mask:
            self.mask = pygame.mask.from_surface(self.image)
        self.pos = vec(x_init_pos, y_init_pos)
        if isinstance(self.game.map, Map):
            self.rect.x = self.pos.x * self.game.tilesize
            self.rect.y = self.pos.y * self.game.tilesize
        elif isinstance(self.game.map, TiledMap):
            self.rect.x = self.pos.x
            self.rect.y = self.pos.y

    def update_position(self):
        if isinstance(self.game.map, Map):
            self.rect.x = self.pos.x * self.game.tilesize
            self.rect.y = self.pos.y * self.game.tilesize
        elif isinstance(self.game.map, TiledMap):
            self.rect.x = self.pos.x
            self.rect.y = self.pos.y

    def get_rect_center(self):
        return self.rect.center

    def get_rect(self):
        return self.rect

    def get_image(self):
        return self.image


class Object(pygame.sprite.Sprite):
    def __init__(self, game, x_init_pos, y_init_pos, type, create_mask=False):
        # x and y position are given in terms of tiles, not pixels
        self.groups = game.all_sprites, game.object_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.object_images[type]
        self.rect  = self.image.get_rect()
        self.type = type
        if create_mask:
            self.mask = pygame.mask.from_surface(self.image)
        self.pos = vec(x_init_pos, y_init_pos)
        if isinstance(self.game.map, Map):
            self.rect.x = self.pos.x * self.game.tilesize
            self.rect.y = self.pos.y * self.game.tilesize
        elif isinstance(self.game.map, TiledMap):
            self.rect.x = self.pos.x
            self.rect.y = self.pos.y
        self.tweening = pytweening.easeInOutSine
        self.step = 0
        self.direction = 1

    def distance_to_avatar(self, radius):
        for avatar in self.game.avatar_sprites:
            self.target = avatar
            target_dist = self.target.pos - self.pos
            if target_dist.length_squared() <= (radius**2)/6: # Done this way to boost performance
                if self.type == 'fire':
                    avatar.drives.perceived_temperature = self.game.environment_temperature + 8
                    avatar.drives.update_bmr(avatar.drives.perceived_temperature)
            elif target_dist.length_squared() <= (radius**2)/3:
                if self.type == 'fire':
                    avatar.drives.perceived_temperature = self.game.environment_temperature + 4
                    avatar.drives.update_bmr(avatar.drives.perceived_temperature)
            elif target_dist.length_squared() <= radius**2:
                if self.type == 'fire':
                    avatar.drives.perceived_temperature = self.game.environment_temperature + 2
                    avatar.drives.update_bmr(avatar.drives.perceived_temperature)
            else:
                if self.type == 'fire':
                    avatar.drives.perceived_temperature = self.game.environment_temperature
                    avatar.drives.update_bmr(avatar.drives.perceived_temperature)

    def update_position(self):
        if isinstance(self.game.map, Map):
            self.rect.x = self.pos.x * self.game.tilesize
            self.rect.y = self.pos.y * self.game.tilesize
        elif isinstance(self.game.map, TiledMap):
            self.rect.x = self.pos.x
            self.rect.y = self.pos.y

    def update(self):
        # Generates the bobbing motion animation
        if ENABLE_ANIMATION:
            if isinstance(self.game.map, TiledMap):
                offset = BOB_RANGE * (self.tweening(self.step / BOB_RANGE) - 0.5)
                self.rect.centery = self.pos.y + offset * self.direction
                self.step += BOB_SPEED
                if self.step > BOB_RANGE:
                    self.step = 0
                    self.direction *= -1
        
        # Update distances
        if self.type in NON_CONSUMABLES and 'activation_radius' in NON_CONSUMABLES[self.type]:
            self.distance_to_avatar(NON_CONSUMABLES[self.type]['activation_radius'])

    def get_rect_center(self):
        return self.rect.center
    
    def get_rect(self):
        return self.rect
    
    def get_image(self):
        return self.image


class Wall(pygame.sprite.Sprite):
    def __init__(self, game, x_init_pos, y_init_pos):
        # x and y position are given in terms of tiles, not pixels 
        self.groups = game.all_sprites, game.wall_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.wall_img
        self.rect  = self.image.get_rect()
        self.pos = vec(x_init_pos, y_init_pos)
        self.rect.x = self.pos.x * self.game.tilesize
        self.rect.y = self.pos.y * self.game.tilesize

    def get_rect( self ):
        return self.rect


class Obstacle(pygame.sprite.Sprite):
    """ This class is to be used only with TiledMaps and Object Layers"""
    def __init__(self, game, x_init_pos, y_init_pos, width, height):
        # x and y position are given in terms of tiles, not pixels 
        self.groups = game.wall_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.pos = vec(x_init_pos, y_init_pos)
        self.rect  = pygame.Rect(self.pos.x, self.pos.y, width, height)
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y

    def get_rect( self ):
        return self.rect
