import simpy as sp
from scipy import stats
import numpy as np
from subprocess import call, check_output
import sys
import simutime as st
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-a','--alg', help='IA Algorithm to be performed', default='0')
parser.add_argument('-c','--cond',help='Channel condition: 1 (LOS), 2 (NLOS) or 3 (random)',default='1')
parser.add_argument('-m','--mean', help='mean of GPS error', default='10')
parser.add_argument('-s','--seed', help='random number generators seed', default='1')

args = parser.parse_args()
ALG = args.alg
COND = args.cond
MEAN = args.mean
SEED = args.seed

if ALG == '4':
    

np.random.seed(int(SEED))

'''
Global definitions 
'''
SSBLOCK_LENGTH = 4 #in OFDM Symbols
FRAME_DURATION = st.milliseconds(10).micro()
SUBFRAME_DURATION = st.milliseconds(1).micro()
BURST_DURATION = st.milliseconds(5).micro()
BURST_PERIOD = st.milliseconds(20).micro()
RACH_PERIOD = st.milliseconds(80).micro()
SIM_DURATION = st.seconds(10).micro()
LTE_RTT = st.milliseconds(1).micro()
ENV_RADIUS = 50 #meters
SPACE=[[0 for j in range(2*ENV_RADIUS+1)] for i in range(2*ENV_RADIUS+1)]


def numerology(subcarrierSpacing, ssburstLength=None):
    """
    Defines the time numerology based on the frame structure of 5G NR
    Needs the the subcarrier spacing in kHz, e.g. 15 means 15 kHz
    Thes possible subcarrier spacings are 15, 30, 60, 120 and 240
    """
    numerol = {
        'ofdmSymbolDuration':0,
        'slotDuration':SUBFRAME_DURATION,
        'minRB':20,
        'maxRB':275,
        'ssblocks':4,
        'ssBurstSlots':0, #BURST_PERIOD/numerol['slotDuration'],
        'ssblockMapping':0 #[0 for i in range(14*numerol['ssBurstSlots'])]
    }

    if subcarrierSpacing == 15:
        numerol['ofdmSymbolDuration'] = SUBFRAME_DURATION/14
        numerol['ssBurstSlots'] = BURST_PERIOD/numerol['slotDuration'],
        if ssburstLength == 4 or ssburstLength==None:
            numerol['ssblocks']=4
            numerol['ssblockMapping'] = ([0,0]+[1 for i in range(4)]+[0,0]+[1 for i in range(4)]+[0,0])*2 + [0 for i in range((numerol['ssBurstSlots']-2)*14)]
        elif ssburstLength == 8: 
            numerol['ssblocks'] = 8
            numerol['ssblockMapping'] = ([0,0]+[1 for i in range(4)]+[0,0]+[1 for i in range(4)]+[0,0])*4 + [0 for i in range(14)]
        return numerol

    elif subcarrierSpacing == 30:
        numerol['slotDuration'] = SUBFRAME_DURATION/2
        numerol['ofdmSymbolDuration'] = numerol['slotDuration']/14
        numerol['ssBurstSlots'] = BURST_PERIOD/numerol['slotDuration'],
        if ssburstLength == 4 or ssburstLength==None:
            numerol['ssblocks'] = 4
            numerol['ssblockMapping'] = ([0 for i in range(4)]+[1 for i in range(4)]*2)*2+[0 for i in range(4)] +[0 for i in range((numerol['ssBurstSlots']-2)*14)]
        elif ssburstLength == 8:
            numerol['ssblocks'] = 8
            numerol['ssblockMapping'] = ([0,0]+[1 for i in range(4)]+[0,0]+[1 for i in range(4)]+[0,0])*4 + [0 for i in range((numerol['ssBurstSlots']-4)*14)]
        return numerol

    elif subcarrierSpacing == 60:
        numerol['slotDuration'] = SUBFRAME_DURATION/4
        numerol['ofdmSymbolDuration'] = numerol['slotDuration']/14
        numerol['ssBurstSlots'] = BURST_PERIOD/numerol['slotDuration'],
        numerol['ssblocks'] = 8
        numerol['ssblockMapping'] = []
        return numerol

    elif subcarrierSpacing == 120:
        numerol['slotDuration'] = SUBFRAME_DURATION/8
        numerol['ofdmSymbolDuration'] = numerol['slotDuration']/14
        numerol['ssBurstSlots'] = BURST_PERIOD/numerol['slotDuration'],
        numerol['ssblocks'] = 64
        numerol['ssblockMapping'] = ((([0 for i in range(4)]+[1 for i in range(8)])*2+[0 for i in range(4)])*4+[0 for i in range(14)]*2)*4
        return numerol

    elif subcarrierSpacing == 240:
        numerol['slotDuration'] = SUBFRAME_DURATION/16
        numerol['ofdmSymbolDuration'] = numerol['slotDuration']/14
        numerol['ssBurstSlots'] = BURST_PERIOD/numerol['slotDuration'],
        numerol['ssblocks']= 64
        numerol['ssblockMapping'] = ((([0 for i in range(8)]+[1 for i in range(16)])*2+[0 for i in range(8)])*4+[0 for i in range(14)]*4)*2+[0 for i in range(14)]*32
        return numerol
    else:
        print("Not a valid subcarrier spacing passed!")
        return -1

def ExhaustiveNonReciprocity(network,condition):
    nSlotsIA, nominalCapacity, beamNet, beamUser= network.initialAccess('0', condition)
    print('SS Blocks to Initial Access:',nSlotsIA)
    print('Nominal Channel Capacity:', nominalCapacity)

    ratio = (RACH_PERIOD/BURST_PERIOD)
    #UE joins the network during the nearest SSB
    if (network.env.now >= network.ssbIndex*BURST_PERIOD) and (network.env.now < (network.ssbIndex*BURST_PERIOD)+BURST_DURATION):
        #Nearest SSB is really a SSB
        if network.ssbIndex % ratio != 0:
            print('\033[94m'+"UE joined the network during a SSB"+'\033[0m')
            print('\033[92m'+"Condition: ",int(network.env.now), (network.ssbIndex)*BURST_PERIOD,'\033[0m')
            ssblock = int(round(((network.env.now - network.ssbIndex*BURST_PERIOD)/network.numerology['ofdmSymbolDuration']),0))
            remainingSSBlocks = int(network.numerology['ssblockMapping'][ssblock:].count(1)/4) #ssblocklength 4 symbols
            if remainingSSBlocks >= nSlotsIA:
                IAtime = (network.ssbIndex+(ratio-network.ssbIndex%ratio))*BURST_PERIOD + BURST_DURATION - network.env.now
            else:
                remainingSlots = (nSlotsIA - remainingSSBlocks)
                needSSB = np.ceil(remainingSlots/network.numerology['ssblocks'])
                print(remainingSlots, needSSB)
                IAtime = (network.ssbIndex*BURST_PERIOD + BURST_DURATION - network.env.now)\
                            + (ratio - (network.ssbIndex % ratio))*BURST_PERIOD #+ BURST_DURATION
                if needSSB > (ratio - (network.ssbIndex % ratio) - 1):
                    for i in range(int(np.ceil(needSSB/(ratio-1)))):
                        IAtime += BURST_PERIOD*ratio
        #Nearest SSB actually is a RACH Opportunity - OK
        else:
            ssBurstsTaken = nSlotsIA/network.numerology['ssblocks']
            print('\033[94m'+"UE joined the network during a RACH"+'\033[0m')
            print('\033[92m'+"It will wait until the next SSB in",(network.ssbIndex+1)*BURST_PERIOD,'\033[0m')
            #         |-------- TIME UNTIL THE RACHE END --------|   |-----NEXT BURSTS-----|  |--NEXT RACH--|
            IAtime = (network.ssbIndex+1)*BURST_PERIOD - network.env.now + (ratio-1)*BURST_PERIOD + BURST_DURATION
            if ssBurstsTaken > (ratio-(network.ssbIndex%ratio)-1):
                for i in range(int(np.ceil(ssBurstsTaken/(ratio-1)))):
                    IAtime += ratio*(BURST_PERIOD)

    
    #UE joins the network after/before the nearest BURST
    else:
        ssBurstsTaken = nSlotsIA/network.numerology['ssblocks']
        if network.ssbIndex % ratio == 0:
            print('\033[94m'+"UE joined the network after a RACH"+'\033[0m',network.ssbIndex)
            print('\033[92m'+"It will wait until the next SSB in",(network.ssbIndex+1)*BURST_PERIOD,'\033[0m')
            IAtime = (network.ssbIndex+1)*BURST_PERIOD - network.env.now + (ratio-1)*BURST_PERIOD + BURST_DURATION
            if ssBurstsTaken > (ratio-(network.ssbIndex%ratio)-1):
                for i in range(int(np.ceil(ssBurstsTaken/(ratio-1)))):
                    IAtime += ratio*(BURST_PERIOD)
            
        elif (network.ssbIndex+1) % ratio == 0:
            print('\033[91m'+"UE joined the network after a SSB"+'\033[0m', network.ssbIndex)
            print('\033[91m'+"Nearest SSB is a RACH Opportunity! It will wait until",(network.ssbIndex+2)*BURST_PERIOD,'\033[0m')
            IAtime = (network.ssbIndex+2)*BURST_PERIOD - network.env.now + (ratio-1)*BURST_PERIOD + BURST_DURATION
            if ssBurstsTaken > (ratio-(network.ssbIndex%ratio)-1):
                for i in range(int(np.ceil(ssBurstsTaken/(ratio-1)))):
                    IAtime += ratio*(BURST_PERIOD)
            
        else:
            print('\033[91m'+"UE joined the network after a SSB"+'\033[0m', network.ssbIndex)
            print('\033[92m'+"It will wait until the next SSB in",(network.ssbIndex+1)*BURST_PERIOD,'\033[0m')
            IAtime = (network.ssbIndex+1)*BURST_PERIOD - network.env.now + (ratio-(network.ssbIndex%ratio)-1)*BURST_PERIOD + BURST_DURATION
            if ssBurstsTaken > (ratio-(network.ssbIndex%ratio)-1):
                for i in range(int(np.ceil(ssBurstsTaken/(ratio-1)))):
                    IAtime += ratio*(BURST_PERIOD)

    return IAtime


def ExhaustivePartialReciprocity(network, condition):
    '''
    In partial reciprocity the network sweeps its antennas beams meanwhile the 
    user stays sending RACH preamble
    '''
    nSlotsIA, nominalCapacity, beamNet, beamUser= network.initialAccess('0', condition)
    print('SS Blocks to Initial Access:',nSlotsIA)
    print('Nominal Channel Capacity:', nominalCapacity)

    ratio = (RACH_PERIOD/BURST_PERIOD)
    #UE joins the network during the nearest SSB
    if (network.env.now >= network.ssbIndex*BURST_PERIOD) and (network.env.now < (network.ssbIndex*BURST_PERIOD)+BURST_DURATION):
        #Nearest SSB is really a SSB
        if network.ssbIndex % ratio != 0:
            print('\033[94m'+"UE joined the network during a SSB"+'\033[0m')
            print('\033[92m'+"Condition: ",int(network.env.now), (network.ssbIndex)*BURST_PERIOD,'\033[0m')
            ssblock = int(round(((network.env.now - network.ssbIndex*BURST_PERIOD)/network.numerology['ofdmSymbolDuration']),0))
            remainingSSBlocks = int(network.numerology['ssblockMapping'][ssblock:].count(1)/4) #ssblocklength 4 symbols
            if remainingSSBlocks >= nSlotsIA:
                IAtime = (network.ssbIndex+(ratio-network.ssbIndex%ratio-1))*BURST_PERIOD - network.env.now
                #IAtime += 
            else:
                remainingSlots = (nSlotsIA - remainingSSBlocks)
                needSSB = np.ceil(remainingSlots/network.numerology['ssblocks'])
                print(remainingSlots, needSSB)
                IAtime = (network.ssbIndex*BURST_PERIOD + BURST_DURATION - network.env.now)\
                            + (ratio - (network.ssbIndex % ratio))*BURST_PERIOD #+ BURST_DURATION
                if needSSB > (ratio - (network.ssbIndex % ratio) - 1):
                    for i in range(int(np.ceil(needSSB/(ratio-1)))):
                        IAtime += BURST_PERIOD*ratio
        #Nearest SSB actually is a RACH Opportunity - OK
        else:
            ssBurstsTaken = nSlotsIA/network.numerology['ssblocks']
            print('\033[94m'+"UE joined the network during a RACH"+'\033[0m')
            print('\033[92m'+"It will wait until the next SSB in",(network.ssbIndex+1)*BURST_PERIOD,'\033[0m')
            #         |-------- TIME UNTIL THE RACHE END --------|   |-----NEXT BURSTS-----|  |--NEXT RACH--|
            IAtime = (network.ssbIndex+1)*BURST_PERIOD - network.env.now + (ratio-1)*BURST_PERIOD + BURST_DURATION
            if ssBurstsTaken > (ratio-(network.ssbIndex%ratio)-1):
                for i in range(int(np.ceil(ssBurstsTaken/(ratio-1)))):
                    IAtime += ratio*(BURST_PERIOD)

    
    #UE joins the network after/before the nearest BURST
    else:
        ssBurstsTaken = nSlotsIA/network.numerology['ssblocks']
        if network.ssbIndex % ratio == 0:
            print('\033[94m'+"UE joined the network after a RACH"+'\033[0m',network.ssbIndex)
            print('\033[92m'+"It will wait until the next SSB in",(network.ssbIndex+1)*BURST_PERIOD,'\033[0m')
            IAtime = (network.ssbIndex+1)*BURST_PERIOD - network.env.now + (ratio-1)*BURST_PERIOD + BURST_DURATION
            if ssBurstsTaken > (ratio-(network.ssbIndex%ratio)-1):
                for i in range(int(np.ceil(ssBurstsTaken/(ratio-1)))):
                    IAtime += ratio*(BURST_PERIOD)
            
        elif (network.ssbIndex+1) % ratio == 0:
            print('\033[91m'+"UE joined the network after a SSB"+'\033[0m', network.ssbIndex)
            print('\033[91m'+"Nearest SSB is a RACH Opportunity! It will wait until",(network.ssbIndex+2)*BURST_PERIOD,'\033[0m')
            IAtime = (network.ssbIndex+2)*BURST_PERIOD - network.env.now + (ratio-1)*BURST_PERIOD + BURST_DURATION
            if ssBurstsTaken > (ratio-(network.ssbIndex%ratio)-1):
                for i in range(int(np.ceil(ssBurstsTaken/(ratio-1)))):
                    IAtime += ratio*(BURST_PERIOD)
            
        else:
            print('\033[91m'+"UE joined the network after a SSB"+'\033[0m', network.ssbIndex)
            print('\033[92m'+"It will wait until the next SSB in",(network.ssbIndex+1)*BURST_PERIOD,'\033[0m')
            IAtime = (network.ssbIndex+1)*BURST_PERIOD - network.env.now + (ratio-(network.ssbIndex%ratio)-1)*BURST_PERIOD + BURST_DURATION
            if ssBurstsTaken > (ratio-(network.ssbIndex%ratio)-1):
                for i in range(int(np.ceil(ssBurstsTaken/(ratio-1)))):
                    IAtime += ratio*(BURST_PERIOD)

    return IAtime


def ExhaustiveFullReciprocity(network, condition):
    nSlotsIA, nominalCapacity, beamNet, beamUser= network.initialAccess('0', condition)

def IterativeSearch(network, condition, nAdjacents):
    nSlotsIA, nominalCapacity, beamNet, beamUser= network.initialAccess('4', condition)
    print('SS Blocks to Initial Access:',nSlotsIA)
    print('Nominal Channel Capacity:', nominalCapacity)
    '''
    The total number of beamforming slots is equal to

    (N_adj + 1)*NBEAMS_UE + 2*NBEAMS_UE

    Where the first factor corresponds to IA Algorithm first phase and the second
    phase, that is fixed, respectively corresponds to algorithms second phase.
    '''
    firstPhaseSlots = (nAdjacents+1)*network.inRangeUsers[-1].numberBeams 
    secondPhaseSlots = 2*network.inRangeUsers[-1].numberBeams
    nFirstPhase = int((nSlotsIA - secondPhaseSlots)/firstPhaseSlots)
    
    ratio = (RACH_PERIOD/BURST_PERIOD)
    #UE joins the network during a burst set
    if (network.env.now >= network.ssbIndex*BURST_PERIOD) and (network.env.now < (network.ssbIndex*BURST_PERIOD)+BURST_DURATION):
        #The nearest burst set is a SSB
        if network.ssbIndex % ratio != 0:
            print('\033[94m'+"UE joined the network during a SSB"+'\033[0m')
            print('\033[92m'+"Condition: ",int(network.env.now), (network.ssbIndex)*BURST_PERIOD,'\033[0m')
            ssblock = int(round(((network.env.now - network.ssbIndex*BURST_PERIOD)/network.numerology['ofdmSymbolDuration']),0))
            remainingSSBlocks = int(network.numerology['ssblockMapping'][ssblock:].count(1)/4) #ssblocklength 4 symbols
            #if remainingSSBlocks >= nSlotsIA:
            if remainingSSBlocks >= firstPhaseSlots:
                #Success in realizing the first IA phase?
                #        |--------AMOUNT OF SSBs UNTIL NEXT RACH---------|              |--RACH PERIOD--|
                IAtime = (network.ssbIndex+(ratio-network.ssbIndex%ratio))*BURST_PERIOD + BURST_DURATION - network.env.now
                if nFirstPhase > 1:
                    #Failed in realizing the first IA phase? How many times?
                    IAtime += (nFirstPhase - 2)*RACH_PERIOD
                #Adding second phase duration
                IAtime += RACH_PERIOD
            # The current SSB is not sufficient to support all the slots
            else:
                #The number of beams not tried yet
                remainingSlots = firstPhaseSlots - remainingSSBlocks
                #Number of burst sets needed to finish the first phase
                needSSB = np.ceil(remainingSlots/network.numerology['ssblocks'])
                if (network.ssbIndex%ratio) > needSSB:
                    #        |--------AMOUNT OF SSBs UNTIL NEXT RACH---------|              |--RACH PERIOD--|
                    IAtime = (network.ssbIndex+(ratio-network.ssbIndex%ratio))*BURST_PERIOD + BURST_DURATION - network.env.now
                else:
                    #        |-----END OF CURRENT SSB-----| |--RACH PERIOD--||-NEXT SSB AND RACH|
                    IAtime = network.ssbIndex*BURST_PERIOD + BURST_DURATION  +  RACH_PERIOD  - network.env.now
                if nFirstPhase>1:
                    #If the first phase has failed
                    IAtime += (nFirstPhase - 2)*RACH_PERIOD
                #Adding second phase duration
                IAtime += RACH_PERIOD

        #The nearest burst set is actually a RACH
        else:
            ssBurstsTaken = nSlotsIA/network.numerology['ssblocks']
            print('\033[94m'+"UE joined the network during a RACH"+'\033[0m')
            print('\033[92m'+"It will wait until the next SSB in",(network.ssbIndex+1)*BURST_PERIOD,'\033[0m')
            #        |-----TIME UNTIL NEXT SSB-------||--FIRST PHASE--|
            IAtime = (network.ssbIndex+1)*BURST_PERIOD + RACH_PERIOD - network.env.now
            if nFirstPhase > 1:
                #Failed in realizing the first IA phase? How many times?
                IAtime += (nFirstPhase - 2)*RACH_PERIOD
            #Adding second phase duration
            IAtime += RACH_PERIOD

    #UE joins the network just after/before the nearest BURST
    else:
        # Number of burst sets needed to finish the first phase
        ssBurstsTaken = firstPhaseSlots/network.numerology['ssblocks']
        if network.ssbIndex % ratio == 0:
            print('\033[94m'+"UE joined the network after a RACH"+'\033[0m',network.ssbIndex)
            print('\033[92m'+"It will wait until the next SSB in",(network.ssbIndex+1)*BURST_PERIOD,'\033[0m')
            IAtime = (network.ssbIndex+1)*BURST_PERIOD - network.env.now + (ratio-1)*BURST_PERIOD + BURST_DURATION
            #Check if it will need more than one burst set
            if ssBurstsTaken > (ratio-(network.ssbIndex%ratio)-1):
                for i in range(int(np.ceil(ssBurstsTaken/(ratio-1)))):
                    IAtime += ratio*(BURST_PERIOD)

        elif (network.ssbIndex+1) % ratio == 0:
            print('\033[91m'+"UE joined the network after a SSB"+'\033[0m', network.ssbIndex)
            print('\033[91m'+"Nearest SSB is a RACH Opportunity! It will wait until",(network.ssbIndex+2)*BURST_PERIOD,'\033[0m')
            IAtime = (network.ssbIndex+2)*BURST_PERIOD - network.env.now + (ratio-1)*BURST_PERIOD + BURST_DURATION
            if ssBurstsTaken > (ratio-(network.ssbIndex%ratio)-1):
                for i in range(int(np.ceil(ssBurstsTaken/(ratio-1)))):
                    IAtime += ratio*(BURST_PERIOD)

        else:
            print('\033[91m'+"UE joined the network after a SSB"+'\033[0m', network.ssbIndex)
            print('\033[92m'+"It will wait until the next SSB in",(network.ssbIndex+1)*BURST_PERIOD,'\033[0m')
            IAtime = (network.ssbIndex+1)*BURST_PERIOD - network.env.now + (ratio-(network.ssbIndex%ratio)-1)*BURST_PERIOD + BURST_DURATION
            if ssBurstsTaken > (ratio-(network.ssbIndex%ratio)-1):
                for i in range(int(np.ceil(ssBurstsTaken/(ratio-1)))):
                    IAtime += ratio*(BURST_PERIOD)

        if nFirstPhase > 1:
            #Failed in realizing the first IA phase? How many times?
            IAtime += (nFirstPhase - 2)*RACH_PERIOD
        #Adding second phase duration
        IAtime += RACH_PERIOD

    return IAtime

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
        SPACE[ENV_RADIUS-1][ENV_RADIUS-1]=1
        self.subcarrierSpacing = 120
        self.numerology = numerology(self.subcarrierSpacing)

    def setSubcarrierSpacing(self, subcarrierSpacing, burstSetLength=None):
        self.numerology = numerology(subcarrierSpacing, burstSetLength)
        

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
            if (self.frameIndex % (rachPeriod/FRAME_DURATION) != 0) and (self.frameIndex != 1):
                print('A new burst set is starting at %d and it is the %d ss burst in %d frame' % (self.env.now, self.ssbIndex, self.frameIndex))
                yield self.env.timeout(burstDuration)
                print('The burst set has finished at %d' % self.env.now)
                yield self.env.timeout(burstPeriod - burstDuration)
            else:
                yield self.env.timeout(burstPeriod)

    def updateFrame(self):
        #self.frameIndex+=1
        while True:
            print('Frame:',self.frameIndex,'in',self.env.now)
            self.frameIndex+=1
            yield self.env.timeout(FRAME_DURATION)
            if self.frameIndex % (BURST_PERIOD/FRAME_DURATION) == 0:
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
                print('A new rach opportunity is starting at %d and it is the %d ss burst in %d frame' % (self.env.now, self.ssbIndex, self.frameIndex))
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
            Pt = '30'                      #Transmission Power
            dist = str(self.calcUserDist(user)) #Distanica Usuario x base
            npontos = '1' #' 50'
            seed = SEED #sys.argv[4]
            NF = '5'                       #Noise Figure
            TN = '-174'                    #Thermal Noise
            BW = '400000000' #1000000000   #Bandwidth
            div = '4'                      #antenna array divisor of wavelength
            move = '75000'                 #Time to keep a path
            minSNR = '-5'                  #Minimal signal to detection
            Tper = '1'                     #
            Tcanal = '1'                   #
            protoID = '1'                  #Protocol Type: 1 - Fixed Interval (static scenario) | 2 - Reactive
            protoParam = '500'             #In protocol type 1 - Period of IA
            limite = protoParam             #Simulation Time
            tipoErro = '1'                 #GPS Error Type: 1 - Normal Distribution | 2 - Uniform Distribution 
            mediaErroGPS = MEAN #sys.argv[3]      #
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
            angle = str(self.calcUserAngle(user))
            bs_array = str(self.antennaArray[0])
            ue_array = str(user.antennaArray[0])
            arqname = 'lixeirao'#/dev/null'#' initial-access-'+alg+'-'+condCanal+'-'+mediaErroGPS+'-'+seed
            

            #command = ('./initial-access'+Pt+' '+dist+npontos+' '+seed+arqname+NF+TN+BW+div+move+minSNR+Tper+Tcanal+limite+tipoErro
            command = [Pt,dist,npontos,seed,arqname,NF,TN,BW,div,move,minSNR,Tper,Tcanal,limite,tipoErro,
                      mediaErroGPS,desvErroGPS,alg,log,velocityUSR,velocityOBJ,protoID,decaimentoTaxaRx,quedaTaxaRx,fastIA,limFastIA,
                      condCanal,condCanal,angle,bs_array,ue_array]
            #print(command)
            try:
                result = check_output(['./initial-access']+command)
            except:
                print("Execution failed:")#, e, file=sys.stderr)
            
            result = result.decode('utf-8').split()
            #print(result)
            if algorithm == '0' : nSlotsIA = int(result[result.index('tIA')+1]) - 1
            else : nSlotsIA = int(result[result.index('tIA')+1])
            nominalCapacity = float(result[result.index('Cnominal')+1])
            beamNet = int(float(result[result.index('BSbeam')+1])*self.numberBeams/360)
            beamUser = int(float(result[result.index('USRbeam')+1])*user.numberBeams/360)
            #print('SS Blocks to Initial Access:',nSlotsIA)
            #print('Nominal Channel Capacity:', nominalCapacity)
        #self.inRangeUsers=[]
        return [nSlotsIA, nominalCapacity, beamNet, beamUser]
            

    def associationRequest(self,user):
        algorithm = ALG #sys.argv[1]
        condition = COND #sys.argv[2]
        reciprocity = '0' #

        print('================================================================')
        self.inRangeUsers.append(user)

        #The search is exhaustive, so the search is a little different
        if algorithm == '0':
            if reciprocity == '0': 
                IAtime = ExhaustiveNonReciprocity(self, condition)
            elif reciprocity == '1': 
                IAtime = ExhaustivePartialReciprocity(self, condition)
            elif reciprocity == '2': 
                IAtime = ExhaustiveFullReciprocity(self, condition)
            
            print('IA finished in:',IAtime,'at',self.env.now+IAtime)

        #The search is not exhaustive
        else:
            if (int(self.env.now) + LTE_RTT) < ((self.ssbIndex+1)*BURST_PERIOD):
                '''
                In this occasion, the message containig the location had the time
                to travel through the LTE control channel before the next SS Burst
                '''
                print('\033[92mCondition: %f %f\033[0m' % (int(self.env.now) + LTE_RTT, (self.ssbIndex+1)*BURST_PERIOD))
                #self.inRangeUsers.append(user)
                #self.initialAccess(algorithm, condition)
                IterativeSearch(self,condition,3)
            else:
                print('\033[91mCondition: %f %f \033[0m' % (int(self.env.now) + LTE_RTT, (self.ssbIndex+1)*BURST_PERIOD))
                #self.inRangeUsers.append(user)
                #self.initialAccess(algorithm, condition)
                IterativeSearch(self,condition,3)
        print('================================================================')

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
    arrivalRate = st.seconds(0.1).micro() 
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
