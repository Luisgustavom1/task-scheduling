
import numpy as np

def combination(a, b, c, d):
    return abs((a + 2*b + 3*c + 4*d) - 30)

def ga(
    costfunc, 
    npop,
    verbose,
    numvar,
    minbound,
    maxbound,
    generations,
):
    population = {}

    for i in range(npop):
        population[i] = {
            'cost': -1, 'solution': np.random.uniform(minbound, maxbound, numvar),
        }

    for it in range(generations):
        t = 0
        costs = []

        for i in range(npop):
            c = costfunc(population[i])
            population[i]['cost'] = c
            costs.push(c)
            t = t + (1/(1+c))

        costs = np.array(costs)
        probs = costs / t 
        
        print(probs)

ga(combination, 6, 1, 4, 0, 30, 6)
