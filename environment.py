
from block import Block
from food import Food


class Environment:

    def __init__(self, game_display, settings, blocks=[], foods=[]):
        self.game_display = game_display
        self.blocks = blocks
        self.foods = foods
        self.state = 0
        self.settings = settings
        if foods and blocks:
            self.set_current_food()

    def generate_environment(self):
        self.blocks = self.generate_blocks()
        self.foods = self.generate_foods(self.blocks)

    def generate_foods(self, blocks):
        foods = []
        for i in range(0, self.settings["food_numbers"]):
            food = Food(self.game_display, blocks)
            foods.append(food)
        return foods

    def generate_blocks(self):
        blocks = []
        for i in range(0, self.settings["block_numbers"]):
            block = Block(self.game_display)
            blocks.append(block)
        return blocks

    def set_current_food(self):
        self.current_food = Food(self.game_display, self.blocks, self.foods[self.state].x, self.foods[self.state].y)

    def get_food(self):
        return self.current_food

    def draw(self):
        self.draw_blocks()
        self.draw_food()

    def draw_food(self):
        self.get_food().update()
        self.get_food().draw()

    def draw_blocks(self):
        for block in self.blocks:
            block.draw()

    def next_state(self):
        self.state += 1
        self.set_current_food()

    def reset_state(self):
        self.state = 0
        self.set_current_food()

