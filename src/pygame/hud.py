import pygame
from src.pygame.settings import *


# HUD functions
def draw_avatar_bar(window, x_pos, y_pos, percentage):
    if percentage < 0:
        percentage = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    fill = percentage * BAR_LENGTH
    outline_rect = pygame.Rect(x_pos, y_pos, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(x_pos, y_pos, fill, BAR_HEIGHT)
    if percentage > 0.5:
        color = GREEN
    elif percentage > 0.2:
        color = YELLOW
    else:
        color = RED
    pygame.draw.rect(window, color, fill_rect)
    pygame.draw.rect(window, BLACK, outline_rect, 1)


def draw_hud_text(window, x_pos, y_pos, text, size):
    font = pygame.font.SysFont("monospace", size)
    label = font.render(text, 1, BLACK)
    window.blit(label, (x_pos, y_pos))


def draw_drive_on_screen(window, x_pos, y_pos, measure, baseline, text):
    draw_avatar_bar(window, x_pos + 45, y_pos, measure / baseline)
    draw_hud_text(window, x_pos - 55, y_pos - 5, text, 15)
    draw_hud_text(window, x_pos + 65, y_pos - 2, f'{measure:.2f}', 11)


def draw_text_on_screen(window, text, font_name, size, color, x, y, align="nw"):
    font = pygame.font.SysFont(font_name, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if align == "nw":
        text_rect.topleft = (x, y)
    if align == "ne":
        text_rect.topright = (x, y)
    if align == "sw":
        text_rect.bottomleft = (x, y)
    if align == "se":
        text_rect.bottomright = (x, y)
    if align == "n":
        text_rect.midtop = (x, y)
    if align == "s":
        text_rect.midbottom = (x, y)
    if align == "e":
        text_rect.midright = (x, y)
    if align == "w":
        text_rect.midleft = (x, y)
    if align == "center":
        text_rect.center = (x, y)
    window.blit(text_surface, text_rect)


def get_text_info(text, font_name, size, color, x, y, align="nw"):
    font = pygame.font.SysFont(font_name, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if align == "nw":
        text_rect.topleft = (x, y)
    if align == "ne":
        text_rect.topright = (x, y)
    if align == "sw":
        text_rect.bottomleft = (x, y)
    if align == "se":
        text_rect.bottomright = (x, y)
    if align == "n":
        text_rect.midtop = (x, y)
    if align == "s":
        text_rect.midbottom = (x, y)
    if align == "e":
        text_rect.midright = (x, y)
    if align == "w":
        text_rect.midleft = (x, y)
    if align == "center":
        text_rect.center = (x, y)
    width, height = text_surface.get_size()
    return x, width, height, text_surface, text_rect


def draw_text_on_rectangle(window, left, top, width, height, color, text_surfaces, text_rects):
    pygame.draw.rect(window, color, pygame.Rect(left, top, width, height))
    for surface, rect in zip(text_surfaces, text_rects):
        window.blit(surface, rect)
