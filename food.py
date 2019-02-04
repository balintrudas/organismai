from os import path

import pygame
from random import uniform


class Food:

    def __init__(self, game_display, blocks, x=None, y=None):
        self.game_display = game_display
        self.display_width, self.display_height = game_display.get_size()
        resources_dir = path.join(path.dirname(__file__), 'resources')
        self.base_food_image = pygame.image.load(resources_dir + '/food.png')
        self.best_food_image = pygame.image.load(resources_dir + '/food_best.png')
        self.display_padding = 20
        self.blocks = blocks
        self.is_best = False
        if x and y:
            self.x, self.y = x, y
            self.update()
        else:
            self.setup()

    def setup(self):
        self.x = uniform(self.display_padding, self.display_width - self.display_padding)
        self.y = uniform(self.display_padding, self.display_height - self.display_padding)
        self.update()
        for block in self.blocks:
            if ((self.x - block.x) ** 2 + (self.y - block.y) ** 2) < (
                    (block.image.get_width() / 2) + self.image.get_width()) ** 2:
                self.setup()

    def update(self):
        self.image = self.best_food_image if self.is_best else self.base_food_image

    def draw(self):
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.game_display.blit(self.image, (self.rect.x, self.rect.y))

    def remove(self):
        self.image.fill((255, 255, 255, 128), None, pygame.BLEND_RGBA_MULT)

    def get_position(self):
        return self.x, self.y
