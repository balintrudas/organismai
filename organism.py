import math
import time
from copy import copy
from os import path

import numpy
import pygame
from pygame.math import Vector2

from environment import Environment


class Organism(pygame.sprite.Sprite):

    def __init__(self, game_display, wih, whh, who, env):
        super(Organism, self).__init__()
        resources_dir = path.join(path.dirname(__file__), 'resources')
        self.image = pygame.image.load(resources_dir + '/organism.png')
        self.best_organism_image = pygame.image.load(resources_dir + '/organism_best.png')
        self.base_organism_image = self.image
        self.game_display = game_display
        self.display_width, self.display_height = game_display.get_size()
        self.angle, self.angle_speed, self.speed = 0, 0, 0
        self.position = Vector2((self.display_width * 0.5, self.display_height * 0.5))
        self.direction = Vector2(0, -1)
        self.rect = self.image.get_rect(center=(self.display_width * 0.5, self.display_height * 0.8))
        self.wih = wih
        self.whh = whh
        self.who = who
        self.environment = self.map_env(env)
        self.sprite = {}
        self.fitness = 0
        self.max_speed = 4
        self.max_angle_speed = 16
        self.dead = False
        self.last_eat_time = time.time()
        self.lifetime = 30
        self.sight_distance = 60
        self.organism_padding = 15

        self.positive_distance = 0
        self.negative_distance = 0
        self.eaten_food, self.eaten_food_score = 0, 300
        self.alive_time, self.alive_time_score = 0, 0.01

        self.org_food_dist = self.calc_distance()
        self.show_sight_points = False
        self.is_best = False

    def map_env(self, env):
        detached_env = Environment(self.game_display, env.settings, env.blocks, env.foods)
        return detached_env

    def update(self):
        if self.angle_speed != 0:
            self.direction.rotate_ip(self.angle_speed)
            self.angle += self.angle_speed
            self.angle = self.angle % 360
            self.image = pygame.transform.rotozoom(self.best_organism_image if self.is_best else self.base_organism_image, -self.angle, 1)
            self.rect = self.image.get_rect(center=self.rect.center)
        if not self.check_boundary():
            if not self.dead:
                self.position += self.direction * self.speed
                self.rect.center = self.position

    def check_boundary(self):
        next_position = self.position + (self.direction * self.speed)
        image_half_width = self.image.get_width() / 2
        image_half_height = self.image.get_height() / 2
        if (self.display_width + self.organism_padding <= next_position.x + image_half_width or
                0 - self.organism_padding >= next_position.x - image_half_width or
                self.display_height + self.organism_padding <= next_position.y + image_half_height or
                0 - self.organism_padding >= next_position.y - image_half_height):
            return True
        for block in self.environment.blocks:
            if ((self.position.x - block.x) ** 2 + (self.position.y - block.y) ** 2) < (
                    (block.image.get_width() / 2) + self.organism_padding) ** 2:
                self.kill()
                self.fitness -= self.eaten_food_score
                return True
        return False

    def is_dead(self):
        if (time.time() - self.last_eat_time) > self.lifetime or self.dead:
            return True
        return False

    def kill(self):
        self.dead = True
        self.image.fill((255, 255, 255, 128), None, pygame.BLEND_RGBA_MULT)

    def learn(self):
        if self.is_dead():
            self.kill()
            self.environment.get_food().remove()
        else:
            self.alive_time += self.alive_time_score
            if self.org_food_dist <= 25:
                self.last_eat_time = time.time()
                self.eaten_food += 1
                self.environment.next_state()
            dis = self.calc_distance()
            heading = self.calc_heading()[0]
            if dis < self.org_food_dist and (-0.2 < heading < 0.2):
                self.positive_distance += 1
            if dis > self.org_food_dist:
                self.negative_distance -= 1
            self.org_food_dist = dis
            inputs = heading, self.calc_norm_dist()
            self.think(numpy.array(inputs, dtype=float))
            self.update()
            self.calc_fitness()

    def think(self, input):
        sight_input = self.calc_norm_sight()
        merges_input = numpy.hstack([input, sight_input])
        activ_func = lambda x: numpy.tanh(x)
        h1 = activ_func(numpy.dot(self.wih, merges_input))
        h2 = activ_func(numpy.dot(self.whh, h1))
        out = activ_func(numpy.dot(self.who, h2))
        self.nn_speed = float(out[0])
        self.nn_angle = float(out[1])
        self.speed += self.nn_speed
        if self.speed > self.max_speed:
            self.speed = self.max_speed
        if self.speed < 0:
            self.speed = 0
        self.angle_speed = self.nn_angle * self.max_angle_speed

    def calc_norm_sight(self):
        sight_points = []
        next_0_position = self.position + (self.direction * self.sight_distance)
        sight_points.append(next_0_position)

        direction_45 = copy(self.direction)
        direction_45.rotate_ip(45)
        next_45_position = self.position + (direction_45 * self.sight_distance)
        sight_points.append(next_45_position)

        direction_90 = copy(self.direction)
        direction_90.rotate_ip(90)
        next_90_position = self.position + (direction_90 * self.sight_distance)
        sight_points.append(next_90_position)

        direction_n45 = copy(self.direction)
        direction_n45.rotate_ip(-45)
        next_n45_position = self.position + (direction_n45 * self.sight_distance)
        sight_points.append(next_n45_position)

        direction_n90 = copy(self.direction)
        direction_n90.rotate_ip(-90)
        next_n90_position = self.position + (direction_n90 * self.sight_distance)
        sight_points.append(next_n90_position)

        if self.show_sight_points:
            pygame.draw.lines(self.game_display, (255, 0, 0), False,
                              [(self.position.x, self.position.y), (next_0_position.x, next_0_position.y)], 1)
            pygame.draw.lines(self.game_display, (255, 0, 0), False,
                              [(self.position.x, self.position.y), (next_45_position.x, next_45_position.y)], 1)
            pygame.draw.lines(self.game_display, (255, 0, 0), False,
                              [(self.position.x, self.position.y), (next_90_position.x, next_90_position.y)], 1)
            pygame.draw.lines(self.game_display, (255, 0, 0), False,
                              [(self.position.x, self.position.y), (next_n45_position.x, next_n45_position.y)], 1)
            pygame.draw.lines(self.game_display, (255, 0, 0), False,
                              [(self.position.x, self.position.y), (next_n90_position.x, next_n90_position.y)], 1)
        norm_results = []
        for point in sight_points:
            norm_result = None
            for block in self.environment.blocks:
                radius = block.image.get_width() / 2
                point_dist = math.hypot(point.x - block.x, point.y - block.y)
                if point_dist <= radius:
                    norm_result = (self.sight_distance - (radius - point_dist)) / self.sight_distance
                    break

            if self.display_width <= point.x:
                norm_result = (self.sight_distance - (point.x - self.display_width)) / self.sight_distance
            elif 0 >= point.x:
                norm_result = (self.sight_distance - abs(point.x)) / self.sight_distance
            elif self.display_height <= point.y:
                norm_result = (self.sight_distance - (point.y - self.display_height)) / self.sight_distance
            elif 0 >= point.y:
                norm_result = (self.sight_distance - abs(point.y)) / self.sight_distance
            norm_results.append(0 if norm_result is None else norm_result)
        return norm_results

    def calc_heading(self):
        d_x = self.environment.get_food().x - self.position.x
        d_y = self.environment.get_food().y - self.position.y
        rads = math.atan2(d_x, -d_y)
        theta_d = math.degrees(rads) - self.angle
        if abs(theta_d) > 180: theta_d += 360
        return theta_d / 180, theta_d

    def calc_distance(self):
        return math.hypot(self.position.x - self.environment.get_food().x,
                          self.position.y - self.environment.get_food().y)

    def calc_norm_dist(self):
        return self.org_food_dist / math.hypot(self.display_width, self.display_height)

    def calc_fitness(self):
        self.fitness = self.alive_time + self.positive_distance + self.negative_distance + (
                self.eaten_food * self.eaten_food_score)
