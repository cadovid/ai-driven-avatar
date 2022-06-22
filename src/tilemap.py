import pygame
import pytmx

from settings import *


class Map:
    def __init__(self, filename):
        self.data = []
        with open(filename, 'r') as f:
            for line in f:
                self.data.append(line.strip())
        self.tilewidth = len(self.data[0])
        self.tileheight = len(self.data)
        self.width = self.tilewidth * TILESIZE # Pixel width of the map
        self.height = self.tileheight * TILESIZE # Pixel height of the map


class TiledMap:
    def __init__(self, filename):
        self.tmxdata = pytmx.load_pygame(filename, pixelalpha=True)
        self.width = self.tmxdata.width * self.tmxdata.tilewidth # (how many tiles across the map) * (how many pixels each tile)
        self.height = self.tmxdata.height * self.tmxdata.tileheight
    
    def render(self, surface):
        ti = self.tmxdata.get_tile_image_by_gid # find the image that goes with a certain tile
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = ti(gid)
                    if tile:
                        surface.blit(tile, (x * self.tmxdata.tilewidth, y * self.tmxdata.tileheight))
    
    def make_map(self):
        temp_surface = pygame.Surface((self.width, self.height))
        self.render(temp_surface)
        return temp_surface


class Camera:
    def __init__(self, width, height):
        """ Keeps track of the whole map """
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        """ Apply offset to a sprite """
        return entity.rect.move(self.camera.topleft)
    
    def apply_rect(self, rect):
        """ Apply offset to a rect """
        return rect.move(self.camera.topleft)

    def update(self, target):
        """ Whenever the player moves, it calculates an offset of how much the player has shifted in the opposite direction """
        x = -target.rect.x + int(WIDTH / 2)
        y = -target.rect.y + int(HEIGHT / 2)

        # Limit scrolling of the camara to the map size
        x = min(0, x) # limit left
        y = min(0, y) # limit top
        x = max(-(self.width - WIDTH), x) # limit right
        y = max(-(self.height - HEIGHT), y) # limit bottom
        self.camera = pygame.Rect(x, y, self.width, self.height)
