"""
This is the main script, which us functions from modules.

Theta (global param) is a list of dictionnaries.
"""
import random
import numpy as np
from sklearn.neighbors import NearestNeighbors
from absl import flags

from modules import * #TODO syntax
from config import PATH_TO_DATA#import the configuration variables

#FLAGS = flags.FLAGS

#flags.DEFINE_string('job', 'null', 'train or evaluate')

def train(data, W, agents_data_idx, privacy, mu, locL, max_steps, eps): #d is the dim of x
    """
    W : list of n lists with n float each, nonnegative weight matrix for n agents;

    agents_data_idx : list of n float, list of neighbors for the agent;

    privacy : boolean, is True for the private case, False else;

    mu : float, trade-off parameter between having similar models for strongly connected agents
    and models that are accurate on their respective local datasets;

    locL : list of n float, Lipschitz constants L for localLossGrad, L_i^{loc} for Lipschitz continuous gradien localLossGrad for each agent;

    max_steps : maximum number of training steps;

    random initialization
    for each step in range nb_steps :
        for each agent:
            if agent wakes up 
                update local theta_i (4)
                broadcast step
                calculate time before next wake up (random.poisson(lam=1.0, size=None))

    eps : list of ints (privacy level)
    """
    n = len(W) #W is a list of lists
    d = len(data[0][0])
    model = []
    clocks = [] #n times (int) wher the agent will wake up
    neighbors = [] #list of the indexs (int) of the neighbors for each agent
    C = [] #list of n float, confidence coeff for each agent
    alpha = [] #list of n float, alpha for each agent
    D = [] #list of n float, D for each agent
    lambd = [] #list of n float, lambd for each agent

    #random init of the model
    for i in range(0, n):
        submodel = []
        for j in range(0, n):
            theta = []
            for k in range (0,d):
                theta.append(2*random.random() - 1) #TODO change init
            submodel.append(theta)
        model.append(submodel)
    
    #set the first wakeup times
    for i in range(0, n):
        clocks.append(np.random.poisson(lam=1.0, size=None))

    #calculate neighbors
    for agent in range(0, n):
        neighbors.append(getNeighbors(W, agent))
    #calculate confidence coeff
    for agent in range(0, n):
        C.append(len(agents_data_idx[agent]))
    m_max = max(C)
    for agent in range(0, n):
        C[agent] = C[agent]/m_max

    #calculate alphas
    for agent in range(0, n):
        alpha.append(1 / (1 + mu * C[agent] * locL[agent]))
    
    #calculate D
    for agent in range(0, n):
        D.append(sum(W[agent]))

    #calculate lmbda
    for agent in range(0, n):
        lambd.append(1 / len(agents_data_idx[agent]))

    #log the loss
    losses = []

    if privacy:
        print('computing with privacy...')
        for step in range(0, max_steps):
            for agent in range (0, n):
                if step >= clocks[agent] : #agent wakes up
                    model = updateStep_private(data, model, W, agent, agents_data_idx, C, mu, alpha, lambd, locL, eps) #TODO args?
                    model = broadcastStep(model, neighbors, agent)
                    clocks[agent] = step + np.random.poisson(lam=1.0, size=None)
    else:
        print('computing without privacy...')
        #run of the algo for each step
        for step in range(0, max_steps):
            for agent in range (0, n):
                if step >= clocks[agent] : #agent wakes up
                    model = updateStep(data, model, W, agent, agents_data_idx, C, mu, alpha, lambd) #TODO args?
                    model = broadcastStep(model, neighbors, agent)
                    clocks[agent] = step + np.random.poisson(lam=1.0, size=None)

    return model

def evaluate(data, model, agents_data_idx): #makes predictions using a model on the data provided
    n = len(agents_data_idx)
    user_RMSEs = []
    for user in range(0,n):
        user_RMSE = []
        for data_idx in agents_data_idx[user]:
            user_RMSE.append(loss(model[user][user], data[data_idx][0], data[data_idx][1]))
    user_RMSEs.append(sum(user_RMSE)/len(user_RMSE))
    return user_RMSEs

### RUN ###
"""
if FLAGS.job == 'train':
    print('Will train')
elif FLAGS.job == 'evaluate':
    print('eval')
else:
    print('add flag job (train or evaluate)')
"""
path = PATH_TO_DATA
train_data, train_agents_data_idx, test_data, test_agents_data_idx = load_ml100k(path)

n = len(train_agents_data_idx)

mu=1000

locL = []
for i in range(0, n):
    locL.append(1)

max_steps = 30

W = []
for i in range(0, n):
    line = []
    for j in range(0,n):
        line.append(1)
    W.append(line)

#generate privacy epsilons
eps = [1.0]*n

#nbrs = NearestNeighbors(n_neighbors=10, algorithm='auto', metric=smp.cosine_similarity).fit(test)

W = np.identity(n)

### Compute scores ###
public_RMSEs = []
private_RMSEs = []

#Purely local models
RMSEs = []
W = np.identity(n)
mu=1000

for i in range(0,5):
    model = train(train_data, W, train_agents_data_idx, False, mu, locL, max_steps, eps)
    print('trained a model for {} steps'.format(max_steps))
    user_RMSEs = evaluate(test_data, model, test_agents_data_idx)
    print('Without privacy :', sum(user_RMSEs)/len(user_RMSEs))
    RMSEs.append(sum(user_RMSEs)/len(user_RMSEs))
    print('')

print('Purely local models RMSE : {}'.format(sum(RMSEs)/len(RMSEs)))
print('######################')

#Non-priv. CD
mu = 1
W = 

for i in range(0,5):
    model = train(train_data, W, train_agents_data_idx, False, mu, locL, max_steps, eps)
    print('trained a model for {} steps'.format(max_steps))
    user_RMSEs = evaluate(test_data, model, test_agents_data_idx)
    print('Without privacy :', sum(user_RMSEs)/len(user_RMSEs))
    RMSEs.append(sum(user_RMSEs)/len(user_RMSEs))
    print('')

print('Non-priv. CD RMSE : {}'.format(sum(RMSEs)/len(RMSEs)))
print('######################')
#private
RMSEs = []
eps = [1.0]*n

for i in range(0,5):
    model = train(train_data, W, train_agents_data_idx, True, mu, locL, max_steps, eps)
    print('trained a model for {} steps'.format(max_steps))
    user_RMSEs = evaluate(test_data, model, test_agents_data_idx)
    print('With privacy :', sum(user_RMSEs)/len(user_RMSEs))
    RMSEs.append(sum(user_RMSEs)/len(user_RMSEs))

print('Private RMSE with eps={} : {}'.format(eps[0],sum(RMSEs)/len(RMSEs)))

#private
RMSEs = []
eps = [0.5]*n

for i in range(0,5):
    model = train(train_data, W, train_agents_data_idx, True, mu, locL, max_steps, eps)
    print('trained a model for {} steps'.format(max_steps))
    user_RMSEs = evaluate(test_data, model, test_agents_data_idx)
    print('With privacy :', sum(user_RMSEs)/len(user_RMSEs))
    RMSEs.append(sum(user_RMSEs)/len(user_RMSEs))

print('Private RMSE with eps={} : {}'.format(eps[0],sum(RMSEs)/len(RMSEs)))

#private
RMSEs = []
eps = [0.1]*n

for i in range(0,5):
    model = train(train_data, W, train_agents_data_idx, True, mu, locL, max_steps, eps)
    print('trained a model for {} steps'.format(max_steps))
    user_RMSEs = evaluate(test_data, model, test_agents_data_idx)
    print('With privacy :', sum(user_RMSEs)/len(user_RMSEs))
    RMSEs.append(sum(user_RMSEs)/len(user_RMSEs))

print('Private RMSE with eps={} : {}'.format(eps[0],sum(RMSEs)/len(RMSEs)))