import numpy as np
import copy
import matplotlib.pyplot as plt

def combination(a, b, c, d):
    return abs((a + 2*b + 3*c + 4*d) - 30)

def roullette_wheel_selection(probs, pop):
  c = np.cumsum(probs)
  ra = np.random.rand(len(pop))
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

def mutate(population, npop, numvar, mrate, minbound, maxbound):
  totalgen = npop * numvar
  rate = int(totalgen * mrate)
  
  for a in range(rate):
    r = np.random.randint(1, totalgen)
    ind = r // numvar
    gen = r % numvar
    population[ind]['solution'][gen] = np.random.randint(minbound, maxbound)

def getmostfitness(p, costfunc):
  cost = -1
  for i in range(len(p)):
      ch = p[i]['solution']
      c = costfunc(ch[0], ch[1], ch[2], ch[3])
      if cost == -1 or c < cost:
        cost = c

  return cost

def plot_solution_decrease(best_solutions, title="Best Solution Decrease Over Iterations"):
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(best_solutions) + 1), best_solutions, marker='o', color='g', label='Best Solution')
    plt.xlabel('Iteration', fontsize=12)
    plt.ylabel('Solution Value', fontsize=12)
    plt.title(title, fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=10)
    plt.show()

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
    bestsolutions = []

    for i in range(npop):
        population[i] = {
            'cost': -1, 'solution': np.random.randint(minbound, maxbound, numvar),
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

        mutate(newpop, npop, numvar, mrate, minbound, maxbound)

        mostfitness = getmostfitness(newpop, costfunc)
        bestsolutions.append(mostfitness)

    bestsolutions.reverse()
    plot_solution_decrease(bestsolutions)

ga(combination, 6, 1, 4, 0, 30, 50, 0.25, 0.1)

