import simpy as sp
from scipy import stats
import numpy as np
from subprocess import call, check_output
import sys
import simutime as st
import argparse

import definitions as defs
import components as comp
from ExhaustiveSearch import ExhaustiveSearch



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

args = parser.parse_args()
algorithm = args.alg
condition = args.cond
errorMean = args.mean
seed = args.seed
adjacent = args.adjacent
reciprocity = args.reciprocity

np.random.seed(int(seed))



        

if __name__ == "__main__":
    ### The average number of users simultaneously at the network
    nUsers = 10
    env = sp.Environment()

    #An input adjustment
    if algorithm == 0:
        option = reciprocity
    elif algorithm == 1 or algorithm == 2:
        option = adjacent



    """ 
    The user mean user arrival/inter-arrival rate, i.e. 1 user per arrival 
    rate, in seconds
    """
    arrivalRate = st.seconds(0.1).micro() 
    skipRate = arrivalRate
    activeUsers = [] 


    """
    Scheduling nerwork processes
    """
    fiveG = comp.Network(env,[8,8])
    fiveG.initializeServices()
    fiveG.setSubcarrierSpacing(120) #120 KHz subcarrier Spacing
    fiveG.setInitialAccessAlgorithm(algorithm, condition, errorMean, seed, option)


    """
    Creating scenarios with users randomly uniform spread
    """
    scenario = comp.Scenario(env,fiveG)
    scenario.initializeUsers(arrivalRate, skipRate, nUsers)
    #time in milliseconds


    """
    Launch Simulation
    """
    env.run(until=SIM_DURATION)
