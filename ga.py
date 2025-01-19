"""Untitled7.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1_EpV2cSWtGwPokRoosebWnOo4xPea84b
"""

import numpy as np
import matplotlib.pyplot as plt
import copy
import random

def sphere(x):
  return sum(x**2)

def roulette_wheel_selection(p):
  c = np.cumsum(p)
  r = sum(p) * np.random.rand()
  ind = np.argwhere(r <= c)
  return ind[0][0]

def crossover(p1, p2):
  c1 = copy.deepcopy(p1)
  c2 = copy.deepcopy(p2)
  alpha = np.random.uniform(0, 1, *(c1['position'].shape))
  c1['position'] = alpha*p1['position'] + (1 - alpha)*p2['position']
  c2['position'] = alpha*p2['position'] + (1 - alpha)*p1['position']
  return c1, c2

def mutate(c, mu, sigma):
  y = copy.deepcopy(c)
  flag = np.random.rand(*(c['position'].shape)) <= mu
  ind = np.argwhere(flag)
  y['position'][ind] += sigma * np.random.randn(*ind.shape)
  return y

def bounds(c, varmin, varmax):
  c['position'] = np.maximum(c['position'], varmin)
  c['position'] = np.minimum(c['position'], varmax)
  return c['position']

def ga(
    # problem definition
    costfunc,
    # number of decicion variables
    num_var,
    # lower bound
    varmin,
    # upper bound
    varmax,
    # number of iterations
    maxit,
    # initial population size
    npop,
    # proportion of children to population
    num_children,
    # mutation rate
    mu,
    # step size of mutation
    sigma,
    # index for somewhere
    beta,
    # verbose fot print frequency
    verbose
  ):
    # each individual has position and cost
    population = {}
    for i in range(npop):
      population[i] = {'position': None, 'cost': None}

    # Best solution found
    bestsol = {'position': None, 'cost': None}
    # initial best cost is infinity
    bestsol_cost = np.inf

    # initialize population
    for i in range(npop):
      population[i]['position'] = np.random.uniform(varmin, varmax, num_var)
      population[i]['cost'] = costfunc(population[i]['position'])

      if population[i]['cost'] < bestsol_cost:
        bestsol = copy.deepcopy(population[i])

    bestcost = np.empty(maxit)

    print("Results return per {} iter".format(verbose))

    for it in range(maxit):
      costs = []
      for i in range(len(population)):
        costs.append(population[i]['cost'])

      costs = np.array(costs)
      avg_cost = np.mean(costs)
      # taking average of the costs
      if avg_cost != 0:
          costs = costs/avg_cost

      # probability is exponensial of -ve beta times costs
      probs = np.exp(-beta*costs)

      for _ in range(num_children//2):
        p1 = population[roulette_wheel_selection(probs)]
        p2 = population[roulette_wheel_selection(probs)]

        c1, c2 = crossover(p1, p2)

        c1 = mutate(c1, mu, sigma)
        c2 = mutate(c2, mu, sigma)

        c1['position'] = bounds(c1, varmin, varmax)
        c2['position'] = bounds(c2, varmin, varmax)

        c1['cost'] = costfunc(c1['position'])

        if type(bestsol_cost) == float:
          if c1['cost'] < bestsol_cost:
            bestsol_cost = copy.deepcopy(c1)
        else:
          # TODO: try not save a entire individual in bestsol_cost
          if c1['cost'] < bestsol_cost['cost']:
            bestsol_cost = copy.deepcopy(c1)

        if c2['cost'] < bestsol_cost['cost']:
          bestsol_cost = copy.deepcopy(c2)

      # TODO always c2?????
      population[len(population)] = c1
      population[len(population)] = c2

      population = sort(population)

      # store best cost to this iteration
      bestcost[it] = bestsol_cost['cost']

      if it % verbose == 0:
        print('Iteration {}: Best Cost = {}'. format(it, bestcost[it]))

    out = population
    Bestsol = bestsol
    Bestcost = bestcost
    return (out, Bestsol, bestcost)

costfunc = sphere
num_var = 5
varmin = -10
varmax = 10

# GA Parameters
# number of iterations
maxit = 500
# initial population size
npop = 20
beta = 1 # index for somewhere
# proportion of children to population
prop_children = 4
# making sure it always an even number
num_children = int(np.round(prop_children * npop/2)*2)
# mutation rate 40%
mu = 0.2
# step size of mutation
sigma = 0.2
# verbose for print frequency
verbose = 100

out = ga(costfunc, num_var, varmin, varmax, maxit, npop, num_children, mu, sigma, beta, verbose)

plt.plot(out[2])
plt.xlim(0, maxit)
plt.xlabel('Generations')
plt.ylabel('Best Cost')
plt.title('Genetic Algorithm')
plt.grid(True)
plt.show
