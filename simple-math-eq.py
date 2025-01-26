import numpy as np
import copy

def combination(a, b, c, d):
    return abs((a + 2*b + 3*c + 4*d) - 30)

def roullette_wheel_selection(probs, pop):
  c = np.cumsum(probs)
  ra = np.random.rand(4)
  newpop = {}
  for i, r in enumerate(ra):
    w = np.argwhere(r <= c)
    pos = w[0][0]    
    newpop[i] = pop[pos]
  return newpop

def crossover_selection(pop, crossrate):
  i = 0
  selection = []
  while(i < len(pop)):
    r = np.random.rand();
    if(r < crossrate):
      selection.append(pop[i])
    i+=1
  return selection

def crossover(p1, p2, l):
  r = np.random.randint(0, l - 1) + 1
  return np.concatenate([p1['solution'][:r], p2['solution'][r:]])

def mutate(population, npop, numvar, mrate):
  totalgen = npop + numvar
  rate = round(totalgen * rate, 0)
  
  for _ in rate:
    r = np.random.randint(1, totalgen)
    ind = round(r / numvar)
    gen = r % numvar
    population[ind]['solution'][gen] = np.random.randint(0, 30)


def ga(
    costfunc, 
    npop,
    verbose,
    numvar,
    minbound,
    maxbound,
    generations,
    crossrate,
    mrate
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
            ch = population[i]['solution']
            c = 1 / (1 + costfunc(ch[0], ch[1], ch[2], ch[3]))
            population[i]['cost'] = c
            costs.append(c)
            t = t + c

        costs = np.array(costs)
        probs = costs / t
        
        newpop = roullette_wheel_selection(probs, population)

        parents = crossover_selection(newpop, crossrate)
        lparents = len(parents)
        if lparents <= 1:
          continue

        for i, p in enumerate(parents):
          parent = parents[(i + 1) % lparents]
          ch = crossover(p, parent, lparents)
          parent['solution'] = ch


        mutate(newpop, npop * numvar, mrate)

ga(combination, 6, 1, 4, 0, 30, 10, 0.25)

