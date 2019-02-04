from os import path

import pygame
from random import uniform


class Block:

    def __init__(self, game_display, x=None, y=None):
        self.game_display = game_display
        self.display_width, self.display_height = game_display.get_size()
        self.display_padding = 20
        if x and y:
            self.x, self.y = x, y
            self.update()
        else:
            self.setup()

    def setup(self):
        self.x = uniform(self.display_padding, self.display_width - self.display_padding)
        self.y = uniform(self.display_padding, self.display_height - self.display_padding)
        self.update()
        if ((self.display_width * 0.5 + self.image.get_width()) > self.x > (
                self.display_width * 0.5 - self.image.get_width()) and
                (self.display_height * 0.5 + self.image.get_height()) > self.y > (
                        self.display_height * 0.5 - self.image.get_height())):
            self.setup()

    def update(self):
        resources_dir = path.join(path.dirname(__file__), 'resources')
        self.image = pygame.image.load(resources_dir + '/block.png')

    def draw(self):
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.game_display.blit(self.image, (self.rect.x, self.rect.y))

    def remove(self):
        self.image.fill((255, 255, 255, 128), None, pygame.BLEND_RGBA_MULT)

    def get_position(self):
        return self.x, self.y
