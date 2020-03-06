import simpy as sp
from scipy import stats
import numpy as np
from subprocess import call, check_output
import sys

import simutime as st
import definitions as defs
from ExhaustiveSearch import ExhaustiveSearch
from GeolocationAlgorithms import IterativeGeolocation, EnhancedGeolocation, ModIterativeGeolocation



SPACE=[[0 for j in range(2*defs.ENV_RADIUS+1)] for i in range(2*defs.ENV_RADIUS+1)]



def numerology(subcarrierSpacing, ssburstLength=None):
    """
    Defines the time numerology based on the frame structure of 5G NR
    Needs the the subcarrier spacing in kHz, e.g. 15 means 15 kHz
    Thes possible subcarrier spacings are 15, 30, 60, 120 and 240
    """
    numerol = {
        'ofdmSymbolDuration':0,
        'slotDuration':defs.SUBFRAME_DURATION,
        'minRB':20,
        'maxRB':275,
        'ssblocks':4,
        'ssBurstSlots':0, #defs.BURST_PERIOD/numerol['slotDuration'],
        'ssblockMapping':0 #[0 for i in range(14*numerol['ssBurstSlots'])]
    }

    if subcarrierSpacing == 15:
        numerol['ofdmSymbolDuration'] = defs.SUBFRAME_DURATION/14
        numerol['ssBurstSlots'] = defs.BURST_PERIOD/numerol['slotDuration'],
        if ssburstLength == 4 or ssburstLength==None:
            numerol['ssblocks']=4
            numerol['ssblockMapping'] = ([0,0]+[1 for i in range(4)]+[0,0]+\
                    [1 for i in range(4)]+[0,0])*2 + [0 for i in range((numerol['ssBurstSlots']-2)*14)]
        elif ssburstLength == 8:
            numerol['ssblocks'] = 8
            numerol['ssblockMapping'] = ([0,0]+[1 for i in range(4)]+[0,0]+[1 for i in range(4)]+[0,0])*4 + [0 for i in range(14)]
        return numerol

    elif subcarrierSpacing == 30:
        numerol['slotDuration'] = defs.SUBFRAME_DURATION/2
        numerol['ofdmSymbolDuration'] = numerol['slotDuration']/14
        numerol['ssBurstSlots'] = defs.BURST_PERIOD/numerol['slotDuration'],
        if ssburstLength == 4 or ssburstLength==None:
            numerol['ssblocks'] = 4
            numerol['ssblockMapping'] = ([0 for i in range(4)]+[1 for i in range(4)]*2)*2+\
                    [0 for i in range(4)] +[0 for i in range((numerol['ssBurstSlots']-2)*14)]
        elif ssburstLength == 8:
            numerol['ssblocks'] = 8
            numerol['ssblockMapping'] = ([0,0]+[1 for i in range(4)]+[0,0]+[1 for i in range(4)]+\
                    [0,0])*4 + [0 for i in range((numerol['ssBurstSlots']-4)*14)]
        return numerol

    elif subcarrierSpacing == 60:
        numerol['slotDuration'] = defs.SUBFRAME_DURATION/4
        numerol['ofdmSymbolDuration'] = numerol['slotDuration']/14
        numerol['ssBurstSlots'] = defs.BURST_PERIOD/numerol['slotDuration'],
        numerol['ssblocks'] = 8
        numerol['ssblockMapping'] = []
        return numerol

    elif subcarrierSpacing == 120:
        numerol['slotDuration'] = defs.SUBFRAME_DURATION/8
        numerol['ofdmSymbolDuration'] = numerol['slotDuration']/14
        numerol['ssBurstSlots'] = defs.BURST_PERIOD/numerol['slotDuration'],
        numerol['ssblocks'] = 64
        numerol['ssblockMapping'] = ((([0 for i in range(4)]+[1 for i in range(8)])*2+[0 for i in range(4)])*4+[0 for i in range(14)]*2)*4
        return numerol

    elif subcarrierSpacing == 240:
        numerol['slotDuration'] = defs.SUBFRAME_DURATION/16
        numerol['ofdmSymbolDuration'] = numerol['slotDuration']/14
        numerol['ssBurstSlots'] = defs.BURST_PERIOD/numerol['slotDuration'],
        numerol['ssblocks']= 64
        numerol['ssblockMapping'] = ((([0 for i in range(8)]+[1 for i in range(16)])*2+[0 for i in range(8)])*4+[0 for i in range(14)]*4)*2+[0 for i in range(14)]*32
        numerol['maxRB'] = 138
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
        self.frameIndex = 0
        self.ssbIndex = 0
        #Defines the position of the BS at the spatial occupation matrix
        SPACE[defs.ENV_RADIUS-1][defs.ENV_RADIUS-1]=1
        self.subcarrierSpacing = 120
        self.numerology = numerology(self.subcarrierSpacing)
        

        #GAMBIARRA
        self.ALG = '0'
        self.COND = '1'
        self.MEAN = '10'
        self.SEED = '1'
        self.ADJ = 2
        self.REC = 2

        
        self.capacityPerFrame = []
        self.availableSlots = self.numerology['ssblocks']
        self.downlinkRatio = 0.5 #time ratio between downlink and uplink

    def setDownlinkRatio(self, ratio):
        self.downlinkRatio = ratio

    def calcNetworkCapacity(self):
        #Decide whether it is or not a burst set frame!
        rachFlag = False
        if self.ssbIndex % defs.RATIO != 0:
            #Burst Set Frame
            dataPeriod = defs.FRAME_DURATION - defs.BURST_DURATION
        elif self.ssbIndex % defs.RATIO == 0:
            #RACH Frame
            dataPeriod = defs.FRAME_DURATION - defs.BURST_DURATION
            rachFlag = True
        elif self.frameIndex % 2 == 1:
            #Normal Frame
            dataPeriod = defs.FRAME_DURATION
        #dataPeriod = defs.BURST_PERIOD - defs.BURST_DURATION

        capacity = {
                'activeUsers' : len(self.associatedUsers),
                'timePerUser' : 0,
                #'bandwidthPerUser' : int(self.numerology['maxRB']/len(self.associatedUsers))*12*self.subcarrierSpacing*1e3, #each resource block has 12 subcarriers
                'bandwidthPerUser' : self.numerology['maxRB']*12*self.subcarrierSpacing*1e3, #each resource block has 12 subcarriers
                'capacityPerUser' : [],
                'amountData' : 0,
                'NetworkCapacity' : 0
                }

        if self.associatedUsers != []:
            if self.ALG == '0':
                accessTimePerUser = dataPeriod*self.downlinkRatio/capacity['activeUsers']
                accessTimePerUser /= 1e6
                for i in self.associatedUsers:
                    if i.sinr ==float('inf'):
                        continue
                    capacity['capacityPerUser'].append(capacity['bandwidthPerUser']*np.log2(1+i.sinr))#*accessTimePerUser)
                    capacity['amountData'] += capacity['bandwidthPerUser']*np.log2(1+i.sinr)*accessTimePerUser
                capacity['timePerUser'] = accessTimePerUser
                capacity['NetworkCapacity'] = capacity['amountData']/(dataPeriod*1e-6*self.downlinkRatio)


            else:
                usedBurstSlots = self.numerology['ssblocks'] - self.availableSlots
                '''
                count = 0
                ssb = 0
                for x in self.numerology['ssblockMapping']:
                    count+=1
                    if x==1:
                        ssb += 1
                    if ssb == usedBurstSlots:
                        break

                controlPeriod = usedBurstSlots - count*4*self.numerology['ofdmSymbolDuration']
                '''
                if rachFlag: 
                    burstsetExploit = 0
                else:
                    burstsetExploit = self.numerology['ssblockMapping'][usedBurstSlots:].count(1)*self.numerology['ofdmSymbolDuration']

                accessTimePerUser = (dataPeriod*self.downlinkRatio + burstsetExploit)/capacity['activeUsers']
                accessTimePerUser /= 1e6 #microseconds to seconds conversion
                for i in self.associatedUsers:
                    if i.sinr ==float('inf'):
                        continue
                    capacity['capacityPerUser'].append(capacity['bandwidthPerUser']*np.log2(1+i.sinr))#*accessTimePerUser)
                    capacity['amountData'] += capacity['bandwidthPerUser']*np.log2(1+i.sinr)*accessTimePerUser
                capacity['timePerUser'] = accessTimePerUser
                capacity['NetworkCapacity'] = capacity['amountData']/(dataPeriod*1e-6*self.downlinkRatio)
            print(dataPeriod, capacity['timePerUser'])

            self.capacityPerFrame.append(capacity)



    def setSubcarrierSpacing(self, subcarrierSpacing, burstSetLength=None):
        self.numerology = numerology(subcarrierSpacing, burstSetLength)

    def setInitialAccessAlgorithm(self, algorithm, condition, mean, seed=1, option='2'):
        self.ALG = algorithm
        self.COND = condition
        self.MEAN = mean
        self.SEED = seed
        if algorithm == '0':
            self.REC = option
        elif algorithm =='2' or algorithm=='3' or algorithm=='4':
            self.ADJ = option



    def burstSet(self, burstDuration, burstPeriod, rachPeriod):
        '''
        Schedules a Burst Set event with burstDuration (in seconds)
        each burstPeriod (in seconds), except when a defs.RACH Opportunity
        is scheduled.

        The counter verifies if its time of a burst set or a defs.RACH Opportunity

        burstDuration = 5 milliseconds
        burstPeriod = 20 milliseconds
        rachPeriod = 40 milliseconds
        '''
        while True:
            self.availableSlots = self.numerology['ssblocks']
            if (self.frameIndex % (rachPeriod/defs.FRAME_DURATION) != 0) and (self.frameIndex != 1):
                print('A new burst set is starting at %d and it is the %d ss burst in %d frame' % (self.env.now, self.ssbIndex, self.frameIndex))
                yield self.env.timeout(burstDuration)
                print('The burst set has finished at %d' % self.env.now)
                #self.calcNetworkCapacity()
                yield self.env.timeout(burstPeriod - burstDuration)
            else:
                yield self.env.timeout(burstPeriod)

    def updateFrame(self):
        #self.frameIndex+=1
        while True:
            print('Frame:',self.frameIndex,'in',self.env.now)
            self.frameIndex+=1
            yield self.env.timeout(defs.FRAME_DURATION)
            self.calcNetworkCapacity()
            if self.frameIndex % (defs.BURST_PERIOD/defs.FRAME_DURATION) == 0:
                self.ssbIndex+=1

    def rachOpportunity(self, rachDuration, rachPeriod):
        '''
        Schedules a defs.RACH Opportunity event with rachDuration (in seconds)
        each rachPeriod (in seconds)
        
        rachDuration = 5 milliseconds
        rachOpportunity = 40 milliseconds
        '''
        while True:
            ### Grants a SS Burst at the first frame but avoids a defs.RACH at the first frame
            if self.frameIndex==1:
                yield self.env.timeout(rachPeriod)
            else:
                print('A new rach opportunity is starting at %d and it is the %d ss burst in %d frame' % (self.env.now, self.ssbIndex, self.frameIndex))
                yield self.env.timeout(rachDuration)
                print('The rach opportunity  has finished at %d' % self.env.now)
                '''
                #GAMBIARRA
                temp = self.ALG
                self.ALG = '0'
                self.calcNetworkCapacity()
                self.ALG = temp
                '''
                yield self.env.timeout(rachPeriod - rachDuration)

    def initializeServices(self):
        self.env.process(self.updateFrame())
        self.env.process(self.burstSet(defs.BURST_DURATION, defs.BURST_PERIOD, defs.RACH_PERIOD))
        self.env.process(self.rachOpportunity(defs.BURST_DURATION, defs.RACH_PERIOD))

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
            Pt = '30'                      #Transmission Power
            dist = str(self.calcUserDist(user)) #Distanica Usuario x base
            npontos = '1' #' 50'
            seed = str(int(self.env.now)) #self.SEED #sys.argv[4]
            NF = '5'                       #Noise Figure
            TN = '-174'                    #Thermal Noise
            BW = str(self.numerology['maxRB']*12*self.subcarrierSpacing*1e3) ### '400000000' #1000000000   #Bandwidth
            div = '4'                      #antenna array divisor of wavelength
            move = '75000'                 #Time to keep a path
            minSNR = '-5'                  #Minimal signal to detection
            Tper = '1'                     #
            Tcanal = '1'                   #
            protoID = '1'                  #Protocol Type: 1 - Fixed Interval (static scenario) | 2 - Reactive
            protoParam = '500'             #In protocol type 1 - Period of IA
            limite = protoParam            #Simulation Time
            tipoErro = '1'                 #GPS Error Type: 1 - Normal Distribution | 2 - Uniform Distribution
            mediaErroGPS = self.MEAN #sys.argv[3]      #
            desvErroGPS = '10'             #
            alg = algorithm #sys.argv[1]
            log= '1'
            velocityUSR = '0'
            velocityOBJ = '5'
            decaimentoTaxaRx = protoParam # O QUE EH ISSO?
            quedaTaxaRx = protoParam #O QUE EH ISSO?
            fastIA = '0'
            limFastIA = '0'
            condCanal = condition #sys.argv[2]
            if algorithm == '2' or algorithm == '3' or algorithm=='4':
                nAdjacents = str(self.ADJ)
            else:
                nAdjacents = '0'
            angle = str(self.calcUserAngle(user))
            bs_array = str(self.antennaArray[0])
            ue_array = str(user.antennaArray[0])
            arqname = 'lixeirao'#/dev/null'#' initial-access-'+alg+'-'+condCanal+'-'+mediaErroGPS+'-'+seed


            #command = ('./initial-access'+Pt+' '+dist+npontos+' '+seed+arqname+NF+TN+BW+div+move+minSNR+Tper+Tcanal+limite+tipoErro
            command = [Pt,dist,npontos,seed,arqname,NF,TN,BW,div,move,minSNR,Tper,Tcanal,limite,tipoErro,
                      mediaErroGPS,desvErroGPS,alg,log,velocityUSR,velocityOBJ,protoID,decaimentoTaxaRx,quedaTaxaRx,fastIA,limFastIA,
                      condCanal,condCanal,nAdjacents, angle,bs_array,ue_array]
            #print(command)
            try:
                result = check_output(['./initial-access']+command)
            except:
                print("Execution failed:")#, e, file=sys.stderr)

            result = result.decode('utf-8').split()
            #print(result)
            if algorithm == '0' : nSlotsIA = int(result[result.index('tIA')+1]) - 1
            else : nSlotsIA = int(result[result.index('tIA')+1])
            nominalCapacity = np.float64(result[result.index('Cnominal')+1])
            effectiveCapacity = np.float64(result[result.index('Cefetiva')+1])
            nominalSNR =np.float64(result[result.index('totalSNR')+1]) #10*np.log10(np.float64(result[result.index('totalSNR')+1])) #np.power(2,nominalCapacity,dtype=np.float64)-1.0)
            beamNet = int(float(result[result.index('BSbeam')+1])*self.numberBeams/360)
            beamUser = int(float(result[result.index('USRbeam')+1])*user.numberBeams/360)
            #print('SS Blocks to Initial Access:',nSlotsIA)
            #print('Nominal Channel Capacity:', nominalCapacity)
        #self.inRangeUsers=[]
        #return [nSlotsIA, nominalCapacity, beamNet, beamUser]
        #return [nSlotsIA, effectiveCapacity, beamNet, beamUser]
        return [nSlotsIA, nominalSNR, beamNet, beamUser]


    def associationRequest(self,user):
        algorithm = self.ALG #sys.argv[1]
        condition = self.COND #sys.argv[2]
        nAdjacents = self.ADJ

        print('================================================================')
        self.inRangeUsers.append(user)

        #The search is exhaustive, so the search is a little different
        if algorithm == '0':
            reciprocity = self.REC #
            ExhaustiveSearch(self, user, condition, reciprocity)

        #The search is not exhaustive
        else:
            if algorithm == '2':
                self.env.process(EnhancedGeolocation(self, user, condition, nAdjacents))
               
            elif algorithm == '3':
                self.env.process(IterativeGeolocation(self, user, condition, nAdjacents))

            elif algorithm == '4':
                self.env.process(ModIterativeGeolocation(self, user, condition, nAdjacents))

        '''
            if (int(self.env.now) + defs.LTE_RTT) < ((self.ssbIndex+1)*defs.BURST_PERIOD):
                #In this occasion, the message containig the location had the time
                #to travel through the LTE control channel before the next SS Burst
                
                print('\033[92mCondition: %f %f\033[0m' % (int(self.env.now) + defs.LTE_RTT, (self.ssbIndex+1)*defs.BURST_PERIOD))
                IAtime = IterativeSearch(self,condition,2)

            else:
                print('\033[91mCondition: %f %f \033[0m' % (int(self.env.now) + defs.LTE_RTT, (self.ssbIndex+1)*defs.BURST_PERIOD))
                IAtime = IterativeSearch(self,condition,2)
            print('IA finished in:',IAtime,'at',self.env.now+IAtime)
        '''
        print('================================================================')




class User(object):
    def __init__(self, radius, antennaArray):
        self.x = radius
        self.y = radius
        self.id = 0

        self.sinr = float('inf')
        self.iatime = 0# []
        self.powerOnTime = 0

        self.antennaArray = antennaArray
        self.antennaGain = antennaArray[0]*antennaArray[1]
        self.numberBeams = antennaArray[0]+antennaArray[1]
        '''
        while self.x**2 + self.y**2 > radius or SPACE[int(self.x+radius)][int(self.y+radius)]==1:
            self.x = np.random.uniform(-radius, radius)
            self.y = np.random.uniform(-radius, radius)
        '''
        angle = np.random.uniform(0,2*np.pi)
        self.x = radius*np.cos(angle)
        self.y = radius*np.sin(angle)
        SPACE[int(self.x+radius)][int(self.y+radius)]=1

    def setIAtime(self, time):
        self.iatime = time - self.powerOntime

    def setPowerOnTime(self, time):
        self.powerOntime = time

    def setSINR(self, sinr):
        self.sinr = sinr



class Scenario(object):
    def __init__(self, env, net):
        self.onlineUsers = []
        self.offlineUsers = []
        self.env = env
        self.network = net
        

    def userArrival(self, rate, radius, callback=None):
        """
        Add a new user to the array of users following a poisson distribtuion
        """
        counter = 1
        while True:
            arrival = np.random.poisson(rate)
            yield self.env.timeout(arrival)
            self.onlineUsers.append(User(radius,[2,2]))
            self.onlineUsers[-1].id = counter
            self.onlineUsers[-1].setPowerOnTime(self.env.now)
            print("there are %d users at %d" %(len(self.onlineUsers), self.env.now))
            if callback:
                callback(self.onlineUsers[-1])
            counter += 1


    def userSkip(self, averageUsers, rate):
        while True:
            if len(self.onlineUsers) >= averageUsers:
                #skip = stats.erlang.rvs(rate)
                skip = np.random.poisson(rate)
                yield self.env.timeout(skip)
                droppingUser = np.random.choice(self.network.associatedUsers)
                SPACE[int(droppingUser.x+defs.ENV_RADIUS)][int(droppingUser.y+defs.ENV_RADIUS)]=0
                self.onlineUsers.remove(droppingUser)
                self.offlineUsers.append(droppingUser)
                print("there are %d users at %d" %(len(self.onlineUsers),self.env.now))
                self.network.associatedUsers.remove(droppingUser)
            else:
                skip = np.random.poisson(rate)
                yield self.env.timeout(skip)

    def initializeUsers(self, arrivalRate, skipRate, nUsers):
        self.env.process(self.userArrival(arrivalRate,defs.ENV_RADIUS, self.network.associationRequest))
        self.env.process(self.userSkip(nUsers,skipRate))
