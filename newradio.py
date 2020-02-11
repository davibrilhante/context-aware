import simpy as sp
from scipy import stats
import numpy as np
from subprocess import call, check_output
import sys
import simutime as st
import argparse

import definitions as defs



"""
Input Arguments parsing
"""
parser = argparse.ArgumentParser()
parser.add_argument('-a','--alg', help='IA Algorithm to be performed', default='0')
parser.add_argument('-c','--cond',help='Channel condition: 1 (LOS), 2 (NLOS) or 3 (random)',default='1')
parser.add_argument('-m','--mean', help='mean of GPS error', default='10')
parser.add_argument('-s','--seed', help='random number generators seed', default='1')
parser.add_argument('-d','--adjacent', help='adjacent beams to specific algorithms', default='2', required=False, type=int)
parser.add_argument('-r','--reciprocity', help='Channel reciprocity assumption', default='2', required=False, type=int)
parser.add_argument('-l','--radius', help='Scenarios radius', default=defs.ENV_RADIUS, required=False, type=int)
parser.add_argument('-u','--users', help='Average users simultaneously', default=10, required=False, type=int)
parser.add_argument('-t','--rate', help='Users Arrival Rate', default=0.1, required=False, type=float)

args = parser.parse_args()
algorithm = args.alg
condition = args.cond
errorMean = args.mean
seed = args.seed
adjacent = args.adjacent
reciprocity = args.reciprocity
defs.ENV_RADIUS = args.radius
users = args.users

import components as comp
#from ExhaustiveSearch import ExhaustiveSearch


np.random.seed(int(seed))

def metricsCollector(scenario):
    accIA = []
    accSNR = []
    allUsers = scenario.offlineUsers+scenario.onlineUsers
    for user in allUsers:
        ### Average Initial Access time
        accIA.append(user.iatime)
        ### Average SINR
        if user.sinr != float('inf'):
            accSNR.append(user.sinr)

    print(np.mean(accIA))
    print(np.mean(accSNR))

    accAvg = []
    accAgg = []
    for frame in scenario.network.capacityPerFrame:
        ### Average capacity
        accAvg.append(np.mean(frame['capacityPerUser']))

        ### Aggregated capacity
        accAgg.append(sum(frame['capacityPerUser']))
    print(np.mean(accAvg))
    print(np.mean(accAgg))
    print(accAvg)
    print(accAgg)

        
def main():
    ### The average number of users simultaneously at the network
    nUsers = users
    env = sp.Environment()


    #An input adjustment
    if algorithm == '0':
        option = reciprocity
    elif algorithm == '2' or algorithm == '3':
        option = adjacent



    """ 
    The user mean user arrival/inter-arrival rate, i.e. 1 user per arrival 
    rate, in seconds
    """
    arrivalRate = st.seconds(args.rate).micro() 
    skipRate = arrivalRate
    activeUsers = [] 


    """
    Scheduling nerwork processes
    """
    fiveG = comp.Network(env,[8,8])
    print('-Network Object', fiveG)

    fiveG.setSubcarrierSpacing(120) #120 KHz subcarrier Spacing
    fiveG.setInitialAccessAlgorithm(algorithm, condition, errorMean, seed, option)
    fiveG.initializeServices()


    """
    Creating scenarios with users randomly uniform spread
    """
    scenario = comp.Scenario(env,fiveG)
    scenario.initializeUsers(arrivalRate, skipRate, nUsers)
    #time in milliseconds


    """
    Launch Simulation
    """
    env.run(until=defs.SIM_DURATION)
    
    print('\n\n\n@@@')

    metricsCollector(scenario)




if __name__ == "__main__":
    main()
