from genetic import Genetic


def main():
    settings = {
        "population_size": 100,
        "block_numbers": 10,
        "food_numbers": 150,
        "max_generation": 30,
        "input_nodes_size": 7,
        "hidden_nodes_size": 20,
        "hidden_nodes_2_size": 50,
        "out_nodes_size": 2,
        "mutation_rate": 0.01,
        "elite_size": 10,
        "always_generate_environment": True,
        "draw_stats": False
    }
    genetic = Genetic(settings)
    genetic.execute()


if __name__ == '__main__':
    main()
