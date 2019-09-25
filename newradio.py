import simpy as sp
from scipy import stats
import numpy as np
from subprocess import call
import sys



'''
Global definitions 
'''
FRAME_DURATION=10
SUBFRAME_DURATION=1
BURST_DURATION=5
BURST_PERIOD=20
RACH_PERIOD=40
SIM_DURATION=10000
LTE_RTT=1
ENV_RADIUS=50
SPACE=[[0 for j in range(2*ENV_RADIUS+1)] for i in range(2*ENV_RADIUS+1)]


def numerology(subcarrierSpacing, ):
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
        #'ssblocks':4,
        #'ssblockMapping':[0 for i in range(14)]
    }

    if subcarrierSpacing == 15:
        numerol['ofdmSymbolDuration'] = SUBFRAME_DURATION/14
#        if numerol['ssblocks']==4:
#            numerol['ssblockMapping'] = []
#        elif numerol['ssblocks']==8:
#            numerol['ssblockMapping'] = []
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
        self.antennaArray = antennaArray
        self.numberBeams = antennaArray[0]+antennaArray[1]
        self.antennaGain = antennaArray[0]*antennaArray[1]
        self.associatedUsers = []
        self.inRangeUsers = []
        self.frameIndex = 1
        self.ssbIndex = 1
        #Defines the position of the BS at the spatial occupation matrix
        SPACE[ENV_RADIUS-1][ENV_RADIUS-1]=1

    def burstSet(self, burstDuration, burstPeriod, rachPeriod):
        '''
        Schedules a Burst Set event with burstDuration (in seconds)
        each burstPeriod (in seconds), except when a RACH Opportunity
        is scheduled.

        The counter verifies if its time of a burst set or a RACH Opportunity

        burstDuration = 5 milliseconds
        burstPeriod = 20 milliseconds
        rachPeriod = 40 milliseconds
        '''
        while True:
            if (self.ssbIndex % (rachPeriod/burstPeriod)) != 0:
                print('A new burst set is starting at %d' % self.env.now)
                yield self.env.timeout(burstDuration)
                print('The burst set has finished at %d' % self.env.now)
                yield self.env.timeout(burstPeriod - burstDuration)
            else:
                yield self.env.timeout(burstPeriod)

    def updateFrame(self):
        while True:
            yield self.env.timeout(FRAME_DURATION)
            self.frameIndex+=1
            if self.frameIndex % 2 == 1:
                self.ssbIndex+=1

    def rachOpportunity(self, rachDuration, rachPeriod):
        '''
        Schedules a RACH Opportunity event with rachDuration (in seconds)
        each rachPeriod (in seconds)
        
        rachDuration = 5 milliseconds
        rachOpportunity = 40 milliseconds
        '''
        while True:
            ### Grants a SS Burst at the first frame but avoids a RACH at the first frame
            if self.frameIndex==1:
                yield self.env.timeout(rachPeriod)
            else:
                print('A new rach opportunity is starting at %d' % self.env.now)
                yield self.env.timeout(rachDuration)
                print('The rach opportunity  has finished at %d' % self.env.now)
                yield self.env.timeout(rachPeriod - rachDuration)

    def initializeServices(self):
        self.env.process(self.updateFrame())
        self.env.process(self.burstSet(BURST_DURATION, BURST_PERIOD, RACH_PERIOD))
        self.env.process(self.rachOpportunity(BURST_DURATION, RACH_PERIOD))

    def calcUserDist(self, user):
        '''
        Returns the distance from user to base station
        '''
        return np.hypot(user.x, user.y)

    def calcUserAngle(self, user):
        '''
        Returns the the angle between user and cartesian plane  
        defined with base station at the center
        '''
        return np.rad2deg(np.arctan2(user.y, user.x))

    def initialAccess(self, algorithm, condition):
        timeSpent = 0
        neededSSB = 0
        for user in self.inRangeUsers:
            Pt = ' 30'
            dist = str(self.calcUserDist(user)) #{5 10 15 20 30 40 50 60 70 80 90 100 140 180 200}; # VOU PASSAR ESSE VALOR
            npontos = ' 50'
            seed = sys.argv[4]
            NF = ' 5'
            TN = ' -174'
            BW = ' 400000000' #1000000000
            div = ' 4'
            move = ' 75000'
            minSNR = ' -5'
            Tper = ' 1'
            Tcanal = ' 1'
            protoID = ' 1'
            protoParam = ' 500'
            limite = protoParam # O QUE SER ISSO?
            tipoErro = ' 1'
            mediaErroGPS = sys.argv[3]
            desvErroGPS = ' 10'
            alg = algorithm #sys.argv[1]
            log= ' 0'
            velocityUSR = ' 0'
            velocityOBJ = ' 5'
            decaimentoTaxaRx = protoParam # O QUE SER ISSO 
            quedaTaxaRx = protoParam #O QUE SER ISSO
            fastIA = ' 0'
            limFastIA = ' 0'
            condCanal = condition #sys.argv[2]
            angle = str(self.calcUserAngle(user))
            bs_array = str(self.antennaArray[0])
            ue_array = str(user.antennaArray[0])
            arqname = ' /dev/null'#' initial-access-'+alg+'-'+condCanal+'-'+mediaErroGPS+'-'+seed
            

            command = ('./initial-access'+Pt+' '+dist+npontos+' '+seed+arqname+NF+TN+BW+div+move+minSNR+Tper+Tcanal+limite+tipoErro
                      +' '+mediaErroGPS+desvErroGPS+' '+alg+log+velocityUSR+velocityOBJ+protoID+decaimentoTaxaRx+quedaTaxaRx+fastIA+limFastIA
                      +' '+condCanal+' '+condCanal+' '+angle+' '+bs_array+' '+ue_array)
            print(command)
            try:
                result = call(command, shell=True)
                if result < 0:
                    print("initial-access was terminated by signal", -result, file=sys.stderr)
                else:
                    print("initial-access returned", result)#, file=sys.stderr)
            except:
                print("Execution failed:", e, file=sys.stderr)

            if algorithm == '0': #exhaustive
                1

            #The feedback is a problem
            elif algorithm == '1': #iterative
                neededSSB = user.numberBeams*(self.numberBeams/2) + 2

            elif algorithm == '2': #gps+iterative
                neededSSB = user.numberBeams*(self.numberBeams/4) + 4

            elif algorithm == '3': #refined+search
                neededSSB = 5
        self.inRangeUsers=[]
            

    def associationRequest(self,user):
        print("chamou a callback")
        algorithm = sys.argv[1]
        condition = sys.argv[2]
        #The search is exhaustive, so the search is a little different
        if algorithm == '0':
            #UE join the network before the nearest SSB
            if self.env.now < (self.ssbIndex+1)*BURST_DURATION:
                1
            #UE join the network during a BURST
            elif self.env.now < (self.ssbIndex+1)*BURST_DURATION + 5:
                1
        #The search is not exhaustive
        else:
            if (int(self.env.now) + LTE_RTT) < (self.ssbIndex*BURST_PERIOD):
                '''
                In this occasion, the message containig the lacation had the time
                to travel through the LTE control channel before the next SS Burst
                '''
                print("Condition: ",int(self.env.now) + LTE_RTT, (self.ssbIndex+1)*BURST_PERIOD)
                self.inRangeUsers.append(user)
                self.initialAccess(algorithm, condition)
            else:
                1

class User(object):
    def __init__(self, radius, antennaArray):
        self.x = radius
        self.y = radius
        self.antennaArray = antennaArray
        self.antennaGain = antennaArray[0]*antennaArray[1]
        self.numberBeams = antennaArray[0]+antennaArray[1]
        while self.x**2 + self.y**2 > radius or SPACE[int(self.x+radius)][int(self.y+radius)]==1:
            self.x = np.random.uniform(-radius, radius)
            self.y = np.random.uniform(-radius, radius)
        SPACE[int(self.x+radius)][int(self.y+radius)]=1

class Scenario(object):
    def __init__(self, env, net):
        self.users = []
        self.env = env
        self.network = net
        
    def userArrival(self, rate, radius, callback=None):
        """
        Add a new user to the array of users following a poisson distribtuion
        """
        while True:
            arrival = np.random.poisson(rate)
            yield self.env.timeout(arrival)
            self.users.append(User(radius,[2,2]))
            print("there are %d users at %d" %(len(self.users), self.env.now))
            if callback:
                callback(self.users[-1])
            
            
    def userSkip(self, averageUsers, rate):
        while True:
            if len(self.users) >= averageUsers:
                #skip = stats.erlang.rvs(rate)
                skip = np.random.poisson(rate) 
                yield self.env.timeout(skip)
                droppingUser = np.random.choice(self.users)
                SPACE[int(droppingUser.x+ENV_RADIUS)][int(droppingUser.y+ENV_RADIUS)]=0
                self.users.remove(droppingUser)
                print("there are %d users at %d" %(len(self.users),self.env.now))
            else:
                skip = np.random.poisson(rate) 
                yield self.env.timeout(skip)

    def initializeUsers(self, arrivalRate, skipRate, nUsers):
        env.process(self.userArrival(arrivalRate,ENV_RADIUS, self.network.associationRequest))
        env.process(self.userSkip(nUsers,skipRate))

        

if __name__ == "__main__":
    ### The average number of users simultaneously at the network
    nUsers = 10
    env = sp.Environment()

    """ 
    The user mean user arrival/inter-arrival rate, i.e. 1 user per arrival 
    rate, in seconds
    """
    arrivalRate = 1000
    skipRate = arrivalRate
    activeUsers = [] 
    """
    Scheduling nerwork processes
    """
    fiveG = Network(env,[8,8])
    fiveG.initializeServices()
    scenario = Scenario(env,fiveG)
    scenario.initializeUsers(arrivalRate, skipRate, nUsers)
    #time in milliseconds
    env.run(until=SIM_DURATION)
