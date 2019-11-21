import numpy as np
from matplotlib import pyplot as plt
import sys

k = 1.380649e-23
t = 300
N0 = k*t

B_BS = 16
B_UE = 4

tau_ofdm = 8.9e-6
tau_ssb = 4*tau_ofdm

p_tx = 1 #30 dBm
pl = -90


if pl < 0:
    path_loss_w =  10**((pl - 30)/10)
else:
    path_loss_w = pl

if sys.argv[1] == '1':
    system_capacity = []
    for s in range(241,3300):
        nSweeps = 64/B_BS
        temp = B_BS*((s-240)/tau_ssb)*np.log(1 + ((tau_ssb/(s-240))*(p_tx*path_loss_w/N0)))
        system_capacity.append(temp*nSweeps)
    plt.plot(system_capacity, label='exh', linestyle='--')


    algorithm_slots = 5
    for n in [0,4,8,12]:
        system_capacity = []
        for s in range(241,3300):
            temp = (64 - (n*algorithm_slots))*(s/tau_ssb)*np.log(1 + ((tau_ssb/s)*(p_tx*path_loss_w/N0)))
            temp += (n*algorithm_slots)*((s-240)/tau_ssb)*np.log(1 + ((tau_ssb/(s-240))*(p_tx*path_loss_w/N0)))
            system_capacity.append(temp)
        plt.plot(system_capacity, label='alg '+str(n)+' users')

    plt.xlabel('Subcarriers')
    plt.ylabel('Burst Set Downlink Capacity')
    plt.legend()

    

elif sys.argv[1] == '2':
    algorithm_slots = 5
    ssb_capacity = []
    for n in range(1,int(np.floor(64/algorithm_slots))+1):
        temp = (64 - (n*algorithm_slots))*(240/tau_ssb)*np.log(1 + ((tau_ssb/240)*(p_tx*path_loss_w/N0)))
        ssb_capacity.append(temp)


    plt.plot([i for i in range(1, n+1)], ssb_capacity)
    plt.xlabel('Users Arriving in the Burst Set')
    plt.ylabel('Burst Set Downlink Capacity')

if sys.argv[1] == '3':
    system_capacity = []
    for s in range(241,3300):
        nSweeps = 64/B_BS
        temp = B_BS*((s-240)/tau_ssb)*np.log(1 + ((tau_ssb/(s-240))*(p_tx*path_loss_w/N0)))
        temp += B_BS*(s/tau_ssb)*np.log(1 + ((tau_ssb/s)*(p_tx*path_loss_w/N0)))
        system_capacity.append(temp*nSweeps)
    plt.plot(system_capacity, label='exh', linestyle='--')


    algorithm_slots = 5
    for n in [0,4,8,12]:
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

if sys.argv[1] == '4':
    algorithm_slots = 5
    for n in [0,4,8,12]:
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

if sys.argv[1] == '5':
    algorithm_slots = 5
    for n in [0,4,8,12]:
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

