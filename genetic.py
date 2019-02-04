import operator
import time
from copy import copy
from os import path
from pathlib import Path
from random import randint

import numpy
import pygame
from matplotlib import pyplot

from block import Block
from environment import Environment
from food import Food
from organism import Organism


class Genetic:

    def __init__(self, settings):
        self.settings = settings
        self.game_display, self.clock = self.initialize_simulation(800, 800)
        self.resources_folder = path.join(path.dirname(__file__), 'resources')
        self.saves_folder = path.join(path.dirname(__file__), 'saves')
        self.env = self.load_environment()
        self.stat = {}
        self.stat_history = []

    def execute(self):
        organisms = []

        for i in range(0, self.settings["population_size"]):
            wih_init = numpy.random.uniform(-1, 1, (self.settings["hidden_nodes_size"], self.settings["input_nodes_size"]))
            whh_init = numpy.random.uniform(-1, 1, (self.settings["hidden_nodes_2_size"], self.settings["hidden_nodes_size"]))
            who_init = numpy.random.uniform(-1, 1, (self.settings["out_nodes_size"], self.settings["hidden_nodes_2_size"]))
            organisms.append(Organism(self.game_display, wih_init, whh_init, who_init, self.env))

        self.stat['best_organism'] = {}
        for gen in range(0, self.settings["max_generation"]):
            self.stat['generation'] = gen
            self.stat['start_time'] = time.time()
            organisms, exit_simulation = self.simulate(organisms)
            if exit_simulation:
                break
            organisms = self.evolve(organisms)
            self.stat_history.append(copy(self.stat))
            if self.settings["draw_stats"]:
                self.plot_stat()
        pygame.quit()
        quit()

    def load_environment(self):
        env = None
        if not self.settings["always_generate_environment"]:
            saved_env = self.load_env_file()
            if saved_env:
                env = saved_env
        if not env:
            env = Environment(self.game_display, self.settings)
            env.generate_environment()
            if not self.settings["always_generate_environment"]:
                self.save_env_file(env)
        return env

    def save_env_file(self, env):
        foods_coordinates = []
        blocks_coordinates = []
        for food in env.foods:
            foods_coordinates.append(food.get_position())
        for block in env.blocks:
            blocks_coordinates.append(block.get_position())
        numpy.savez(self.saves_folder + '/env.npz', foods_coordinates=foods_coordinates, blocks_coordinates=blocks_coordinates)

    def load_env_file(self):
        if not Path(self.saves_folder + "/env.npz").exists():
            return None
        saved_env = numpy.load(self.saves_folder + "/env.npz")
        env = Environment(self.game_display, self.settings)
        foods = []
        blocks = []
        for block_pos in saved_env['blocks_coordinates']:
            block = Block(self.game_display, block_pos[0], block_pos[1])
            blocks.append(block)
        for food_pos in saved_env['foods_coordinates']:
            food = Food(self.game_display, blocks, food_pos[0], food_pos[1])
            foods.append(food)
        env.foods = foods
        env.blocks = blocks
        return env

    def initialize_simulation(self, display_width, display_height):
        game_display = pygame.display.set_mode((display_width, display_height))
        pygame.display.set_caption('Genetic learning')
        clock = pygame.time.Clock()
        pygame.init()
        pygame.font.init()
        return game_display, clock

    def simulate(self, organisms):
        close_session = False
        exit_simulation = False
        while not close_session and not exit_simulation:
            if self.generation_is_dead(organisms):
                close_session = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_simulation = True

            self.draw_background(self.game_display)
            self.env.draw_blocks()
            for org in reversed(organisms):
                org.learn()
                org.environment.draw_food()
                pygame.sprite.RenderPlain(org).draw(self.game_display)

            for org in organisms:
                org.is_best = False
                org.environment.get_food().is_best = False

            organisms = sorted(organisms, key=operator.attrgetter('fitness'), reverse=True)
            organisms[0].is_best = True
            organisms[0].environment.get_food().is_best = True

            self.calc_stat(organisms)
            self.draw_stat()
            pygame.display.flip()
            self.clock.tick(30)
        return organisms, exit_simulation

    def generation_is_dead(self, organisms):
        for org in organisms:
            if not org.is_dead():
                return False
        return True

    def draw_background(self, game_display):
        game_display.fill((255, 255, 255))

    def calc_stat(self, organisms):
        best_fitness = 0
        sum_fitness = 0
        dead_organism = 0
        best_organism = {}
        eaten_food = 0
        for org in organisms:
            sum_fitness += org.fitness
            if org.fitness > best_fitness:
                best_fitness = org.fitness
                best_organism = org
            if org.is_dead():
                dead_organism += 1
            if org.environment.state > eaten_food:
                eaten_food = org.environment.state
        self.stat['best_fitness'] = best_fitness
        self.stat['sum_fitness'] = sum_fitness
        self.stat['dead_organism'] = dead_organism
        self.stat['eaten_food'] = eaten_food
        saved_best_organism = self.stat['best_organism']
        if 'best_organism' not in self.stat or not saved_best_organism or (bool(best_organism) and
                                                                           saved_best_organism.fitness < best_organism.fitness):
            self.stat['best_organism'] = best_organism

    def draw_stat(self):
        myfont = pygame.font.SysFont('Comic Sans MS', 12, bold=True)
        texts = ['Elapsed time: {elapsed}',
                 'Population size: {population_size}',
                 'Best fitness: {best_fitness}',
                 'Sum fitness: {sum_fitness}',
                 'Dead organism: {dead_organism} / {population_size}',
                 'Generation: {generation}',
                 'Eaten food: {eaten_food}']
        d = dict(elapsed="%.f" % (time.time() - self.stat['start_time']),
                 best_fitness="%.f" % self.stat['best_fitness'],
                 sum_fitness="%.f" % self.stat['sum_fitness'],
                 dead_organism=self.stat['dead_organism'],
                 population_size=self.settings["population_size"],
                 generation=self.stat['generation'] + 1,
                 eaten_food=self.stat['eaten_food'])
        for i, text in enumerate(texts):
            textsurface = myfont.render(text.format(**d), False, (0, 0, 0))
            self.game_display.blit(textsurface, (5, i * 15))

    def evolve(self, organisms):
        offsprings = []

        parents = self.select_elite(organisms)
        numpy.random.shuffle(parents)
        pairs = []
        while len(pairs) != self.settings["population_size"]:
            pairs.append(self.pair(parents))

        for pair in pairs:
            offspring_pair = self.crossover(pair[0], pair[1])
            pick = randint(0, 1)
            offsprings.append(offspring_pair[pick])

        self.mutation(offsprings)

        return offsprings

    def select_elite(self, organisms):
        elites = []
        organisms_sorted = sorted(organisms, key=operator.attrgetter('fitness'), reverse=True)
        for i in range(0, self.settings["elite_size"]):
            organism = Organism(self.game_display, organisms_sorted[i].wih, organisms_sorted[i].whh,
                                          organisms_sorted[i].who, self.env)
            organism.environment.reset_state()
            organism.fitness = organisms_sorted[i].fitness
            elites.append(organism)
        return elites

    def pair(self, parents):
        total_fitness_parents = sum([parent.fitness for parent in parents])
        pick = numpy.random.uniform(0, total_fitness_parents)
        pair_1 = self.r_selection(parents, pick)
        pair_2 = self.r_selection(parents, pick)
        while pair_1[1] == pair_2[1]:
            pick = numpy.random.uniform(0, total_fitness_parents)
            pair_2 = self.r_selection(parents, pick)
        return [pair_1[0], pair_2[0]]

    def r_selection(self, parents, pick):
        current = 0
        for i, parent in enumerate(parents):
            current += parent.fitness
            if current > pick:
                return Organism(self.game_display, copy(parent.wih), copy(parent.whh),
                                          copy(parent.who), self.env), i

    def crossover(self, x, y):
        x.wih, y.wih = self.crossover_weight(x.wih, y.wih)
        x.whh, y.whh = self.crossover_weight(x.whh, y.whh)
        x.who, y.who = self.crossover_weight(x.who, y.who)
        return x, y

    def crossover_weight(self, x, y):
        weigth_x = x
        weigth_y = y
        for i in range(len(x)):
            for j in range(len(x[i])):
                if numpy.random.choice([True, False]):
                    weigth_x[i][j] = y[i][j]
                    weigth_y[i][j] = x[i][j]
        return weigth_x, weigth_y

    def mutation(self, base_offsprings):
        for offspring in base_offsprings:
            offspring.wih = self.mutate_weight(offspring.wih)
            offspring.whh = self.mutate_weight(offspring.whh)
            offspring.who = self.mutate_weight(offspring.who)
        return base_offsprings

    def mutate_weight(self, offspring_weights):
        for i in range(len(offspring_weights)):
            for j in range(len(offspring_weights[i])):
                if numpy.random.choice([True, False], p=[self.settings["mutation_rate"], 1 - self.settings["mutation_rate"]]):
                    offspring_weights[i][j] = numpy.random.uniform(-1, 1)
        return offspring_weights

    def plot_stat(self):
        best_fitnesses = []
        sum_fitnesses = []
        dead_organisms = []
        for stat in self.stat_history:
            best_fitnesses.append(stat['best_fitness'])
            sum_fitnesses.append(stat['sum_fitness'])
            dead_organisms.append(stat['dead_organism'])
        pyplot.subplot(3, 1, 1)
        pyplot.plot(best_fitnesses)
        pyplot.legend(['Best fitness'], loc='upper left')
        pyplot.subplot(3, 1, 2)
        pyplot.plot(sum_fitnesses)
        pyplot.legend(['Sum fitness'], loc='upper left')
        pyplot.subplot(3, 1, 3)
        pyplot.plot(dead_organisms)
        pyplot.legend(['Dead organism'], loc='upper left')
        pyplot.show()