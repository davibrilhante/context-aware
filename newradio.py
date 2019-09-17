import simpy as sp
from scipy import stats
import numpy as np

FRAME_DURATION=0.010
SUBFRAME_DURATION=0.001
BURST_DURATION=0.005
BURST_PERIOD=0.020
RACH_PERIOD=0.040
SIM_DURATION=3600
ENV_RADIUS=50


def numerology(subcarrierSpacing):
    """
    Defines the time numerology based on the frame structure of 5G NR
    Needs the the subcarrier spacing in kHz, e.g. 15 means 15 kHz
    Thes possible subcarrier spacings are 15, 30, 60, 120 and 240
    """
    numerol = {
        'ofdmSymbolDuration':0,
        'slotDuration':SUBFRAME_DURATION,
        'minRB':20,
        'maxRB':275
    }
    if subcarrierSpacing == 15:
        numerol['ofdmSymbolDuration'] = SUBFRAME_DURATION/14
        return numerol

    elif subcarrierSpacing == 30:
        numerol['slotDuration'] = SUBFRAME_DURATION/2
        numerol['ofdmSymbolDuration'] = numerol['slotDuration']/14
        return numerol

    elif subcarrierSpacing == 60:
        numerol['slotDuration'] = SUBFRAME_DURATION/4
        numerol['ofdmSymbolDuration'] = numerol['slotDuration']/14
        return numerol

    elif subcarrierSpacing == 120:
        numerol['slotDuration'] = SUBFRAME_DURATION/8
        numerol['ofdmSymbolDuration'] = numerol['slotDuration']/14
        return numerol

    elif subcarrierSpacing == 240:
        numerol['slotDuration'] = SUBFRAME_DURATION/16
        numerol['ofdmSymbolDuration'] = numerol['slotDuration']/14
        return numerol
    else:
        print("Not a valid subcarrier spacing passed!")
        return -1




class Network(object):
    def __init__(self, env, antennaArray):
        self.env = env
        self.nBeams = antennaArray**2

    def burstSet(self, burstDuration, burstPeriod, rachPeriod):
        counter = 1
        while True:
            if (counter % (1 + rachPeriod/burstPeriod)) != 0:
                print('A new burst set is starting at %d' % self.env.now)
                yield self.env.timeout(burstDuration)
                print('The burst set has finished at %d' % self.env.now)
                yield self.env.timeout(burstPeriod - burstDuration)
            else:
                yield self.env.timeout(burstPeriod)
            counter += 1

    def rachOpportunity(self, rachDuration, rachPeriod):
        while True:
            yield self.env.timeout(rachPeriod)
            print('A new rach opportunity is starting at %d' % self.env.now)
            yield self.env.timeout(rachDuration)
            print('The rach opportunity  has finished at %d' % self.env.now)
            yield self.env.timeout(rachPeriod - rachDuration)

    def initializeServices(self):
        self.env.process(burstSet(BURST_DURATION, BURST_PERIOD, self.env))
        self.env.process(rachOpportunity(BURST_DURATION, RACH_PERIOD, self.env))


class User(object):
    def __init__(self, radius):
        self.x = radius
        self.y = radius
        while self.x**2 + self.y**2 > radius:
            self.x = np.random.uniform(-radius, radius)
            self.y = np.random.uniform(-radius, radius)

def userArrival(rate, arrayUsers, env, radius):
    while True:
        arrival = np.random.poisson(rate)
        yield env.timeout(arrival)
        arrayUsers.append(User(radius))
        print("there are %d at %d" %(len(arrayUsers),env.now))
        
        
def userSkip(averageUsers, rate, arrayUsers, env):
    while True:
        if len(arrayUsers) >= averageUsers:
            #skip = stats.erlang.rvs(rate)
            skip = np.random.poisson(rate) 
            yield env.timeout(skip)
            arrayUsers.remove(np.random.choice(arrayUsers))
            print("there are %d at %d" %(len(arrayUsers),env.now))
        else:
            skip = np.random.poisson(rate) 
            yield env.timeout(skip)

        

#class UserGenerator(object):
#    def __init__ (self, nUsers, radius, env):
#        self.env = env
#        self.r = radius
#        self.users = [User(radius) for i in range(nUsers)]
#        self.hmm = np.random.uniform(SIM_DURATION)
#        self.hmmDuration = np.random.uniform()
#
#    def usersNow(self):
#        return len(self.users)
#
#    def usersArriving(self, rate):
#        while :6
#            yield self.env.timeout(np.random.poisson(rate))
#            self.users.append(User(self.random))
#            
#
#    def usersQuiting(self):
#        1


if __name__ == "__main__":
    ### The average number of users simultaneously at the network
    nUsers = 10
    env = sp.Environment()

    """ The user mean user arrival/inter-arrival rate, i.e. 1 user per arrival 
    rate, in seconds
    """
    arrivalRate = 60 
    skipRate = arrivalRate
    activeUsers = [] 
    #env.process(burstSet(BURST_DURATION,BURST_PERIOD,env))
    #env.process(rachOpportunity(BURST_DURATION,RACH_PERIOD,env))

    """
    Scheduling nerwork processes
    """
    env.process(userArrival(arrivalRate,activeUsers,env,ENV_RADIUS))
    env.process(userSkip(nUsers,skipRate,activeUsers,env))

    #time in seconds
    env.run(until=SIM_DURATION)
