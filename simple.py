import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import copy
import warnings
import random

# individuals
POPULATION_SIZE = 100

# genes
GENES = '''abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP
QRSTUVWXYZ 1234567890, .-;:_!"#%&/()=?@${[]}'''

# target
TARGET = "Kaggle!"

class Individual(object):
        def __init__(self, chromosome):
            self.chromosome = chromosome;
            self.fitness = self.calc_fitness()

        @classmethod
        def mutate_genes(self):
            global GENES
            gene = random.choice(GENES)
            return gene

        @classmethod
        def create_gnome(self):
            global TARGET
            gnome_len = len(TARGET)
            return [self.mutate_genes() for _ in range(gnome_len)]

        def mate(self, par2):
            child_chromosome = []
            for gp1, gp2 in zip(self.chromosome, par2.chromosome):
                prob = random.random()

                if prob < 0.45:
                    child_chromosome.append(gp1)
                elif prob < 0.90:
                    child_chromosome.append(gp2)
                else:
                    # for maintaining diversity
                    child_chromosome.append(self.mutate_genes())

            return Individual(child_chromosome)

        def calc_fitness(self):
            global TARGET
            fitness = 0
            for gs, target in zip(self.chromosome, TARGET):
                if gs != target: fitness += 1
            return fitness

def main(): 
    global POPULATION_SIZE

    generation = 1

    found = False
    population = []

    for _ in range(POPULATION_SIZE):
        gnome = Individual.create_gnome()
        population.append(Individual(gnome))

    while not found:
        population = sorted(population, key = lambda x: x.fitness)

        if population[0].fitness <= 0:
            found = True
            break

        new_generation = []

        bias = int((10*POPULATION_SIZE)/100)
        new_generation.extend(population[:bias])

        bias = int((90*POPULATION_SIZE)/100)
        for _ in range(bias):
            parent1 = random.choice(population[:50])
            parent2 = random.choice(population[:50])

            child = parent1.mate(parent2)
            new_generation.append(child)

        population = new_generation
        
        print("Generation: {}\tString: {}\tFitness: {}".format(generation, "".join(population[0].chromosome), population[0].fitness))
        generation += 1
        
        
    print("Generation: {}\tString: {}\tFitness: {}".format(generation, "".join(population[0].chromosome), population[0].fitness))

if __name__ == '__main__':
    main()