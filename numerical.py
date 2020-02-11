import numpy as np
from matplotlib import pyplot as plt
import sys
import argparse


###########################################
#               Constants
##########################################
k = 1.380649e-23
t = 300
N0 = k*t

###########################################
#               Arguments
###########################################
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--plotType',help='The type of plot you want', default=1, type=int)
parser.add_argument('-b', '--bsAntennas',help='The number of base station antenna elements', default=16, type=int, required=False)
parser.add_argument('-u', '--ueAntennas',help='The number of User Equipment antenna elements', default=4, type=int, required=False)
parser.add_argument('-t', '--txPower',help='The transmitter power in watts', default=1, type=int, required=False)
parser.add_argument('-l', '--pathLoss',help='The path loss in dB', default=-90, type=float, required=False)
parser.add_argument('-s', '--subcarrierSpacing',help='Numerology', default=3, type=float, required=False)
parser.add_argument('-n', '--extraUsers',help='Number of extra users sharing', default=0, type=int, required=False)
#parser.add_argument('-a','--availableSubcarriers', help='Available subcarriers', default=3300, type=int, required=False)
parser.add_argument('-a','--algorithmSlots',help='Number of slots taken by the algorithm to complete IA',default=5,type=int,required=False)

args = parser.parse_args()

plotType = args.plotType
B_BS = args.bsAntennas
B_UE = args.ueAntennas
p_tx = args.txPower #30 dBm
pl = args.pathLoss
tau_ofdm = (1e-3/(2**(args.subcarrierSpacing)))/14
tau_ssb = 4*tau_ofdm

userArray = [int(i*64/(3*args.algorithmSlots)) for i in range(4)]


if pl < 0:
    path_loss_w =  10**((pl - 30)/10)
else:
    path_loss_w = pl

if plotType == 1:
    system_capacity = []
    for s in range(241,3300):
        nSweeps = 64/B_BS
        temp = B_BS*((s-240)/tau_ssb)*np.log(1 + ((tau_ssb/(s-240))*(p_tx*path_loss_w/N0)))
        system_capacity.append(temp*nSweeps)
    plt.plot(system_capacity, label='exh', linestyle='--')


    algorithm_slots = args.algorithmSlots
    #for n in [0,4,8,12]:
    for n in userArray:
        system_capacity = []
        for s in range(241,3300):
            temp = (64 - (n*algorithm_slots))*(s/tau_ssb)*np.log(1 + ((tau_ssb/s)*(p_tx*path_loss_w/N0)))
            temp += (n*algorithm_slots)*((s-240)/tau_ssb)*np.log(1 + ((tau_ssb/(s-240))*(p_tx*path_loss_w/N0)))
            system_capacity.append(temp)
        plt.plot(system_capacity, label='alg '+str(n)+' users')

    plt.xlabel('Subcarriers')
    plt.ylabel('Burst Set Downlink Capacity')
    plt.legend()

    

elif plotType == 2:
    algorithm_slots = args.algorithmSlots
    ssb_capacity = []
    for n in range(1,int(np.floor(64/algorithm_slots))+1):
        temp = (64 - (n*algorithm_slots))*(240/tau_ssb)*np.log(1 + ((tau_ssb/240)*(p_tx*path_loss_w/N0)))
        ssb_capacity.append(temp)


    plt.plot([i for i in range(1, n+1)], ssb_capacity)
    plt.xlabel('Users Arriving in the Burst Set')
    plt.ylabel('Burst Set Downlink Capacity')

if plotType == 3:
    system_capacity = []
    for s in range(241,3300):
        nSweeps = 64/B_BS
        temp = B_BS*((s-240)/tau_ssb)*np.log(1 + ((tau_ssb/(s-240))*(p_tx*path_loss_w/N0)))
        temp += B_BS*(s/tau_ssb)*np.log(1 + ((tau_ssb/s)*(p_tx*path_loss_w/N0)))
        system_capacity.append(temp*nSweeps)
    plt.plot(system_capacity, label='exh', linestyle='--')


    algorithm_slots = args.algorithmSlots
    #for n in [0,4,8,12]:
    for n in userArray:
        system_capacity = []
        for s in range(241,3300):
            temp = (64 - (n*algorithm_slots))*(s/tau_ssb)*np.log(1 + ((tau_ssb/s)*(p_tx*path_loss_w/N0)))
            temp += (n*algorithm_slots)*((s-240)/tau_ssb)*np.log(1 + ((tau_ssb/(s-240))*(p_tx*path_loss_w/N0)))
            temp += 64*(s/tau_ssb)*np.log(1 + ((tau_ssb/s)*(p_tx*path_loss_w/N0)))
            system_capacity.append(temp)
        plt.plot(system_capacity, label='alg '+str(n)+' users')

    plt.xlabel('Subcarriers')
    plt.ylabel('Burst Set Downlink Capacity')
    plt.legend()

if plotType == 4:
    algorithm_slots = args.algorithmSlots
    #for n in [0,4,8,12]:
    for n in userArray:
        system_capacity = []
        for s in range(241,3300):
            nSweeps = 64/B_BS
            temp = B_BS*((s-240)/tau_ssb)*np.log(1 + ((tau_ssb/(s-240))*(p_tx*path_loss_w/N0)))
            system_capacity.append(temp*nSweeps)


            temp = (64 - (n*algorithm_slots))*(s/tau_ssb)*np.log(1 + ((tau_ssb/s)*(p_tx*path_loss_w/N0)))
            temp += (n*algorithm_slots)*((s-240)/tau_ssb)*np.log(1 + ((tau_ssb/(s-240))*(p_tx*path_loss_w/N0)))
            system_capacity[-1] = 100 - system_capacity[-1]*100/temp
        plt.plot(system_capacity, label='alg '+str(n)+' users')

    plt.xlabel('Subcarriers')
    plt.ylabel('Burst Set Downlink Capacity')
    plt.legend()

if plotType == 5:
    algorithm_slots = args.algorithmSlots
    #for n in [0,4,8,12]:
    for n in userArray:
        system_capacity = []
        for s in range(400,3300):
            nSweeps = 64/B_BS
            temp = B_BS*((s-240)/tau_ssb)*np.log(1 + ((tau_ssb/(s-240))*(p_tx*path_loss_w/N0)))
            temp += B_BS*(s/tau_ssb)*np.log(1 + ((tau_ssb/s)*(p_tx*path_loss_w/N0)))
            system_capacity.append(temp*nSweeps)
            #plt.plot(system_capacity, label='exh', linestyle='--')

            temp = (64 - (n*algorithm_slots))*(s/tau_ssb)*np.log(1 + ((tau_ssb/s)*(p_tx*path_loss_w/N0)))
            temp += (n*algorithm_slots)*((s-240)/tau_ssb)*np.log(1 + ((tau_ssb/(s-240))*(p_tx*path_loss_w/N0)))
            temp += 64*(s/tau_ssb)*np.log(1 + ((tau_ssb/s)*(p_tx*path_loss_w/N0)))
            system_capacity[-1] = 100 - 100*system_capacity[-1]/temp
        #print(system_capacity)
        plt.plot(system_capacity, label='alg '+str(n)+' users')

    plt.xlabel('Subcarriers')
    plt.ylabel('Burst Set Downlink Capacity')
    plt.legend()

plt.grid()
if len(sys.argv) == 3: plt.savefig(sys.argv[2])
plt.show()

