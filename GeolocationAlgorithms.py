import simpy as sp
from scipy import stats
import numpy as np
from subprocess import call, check_output
import sys

import simutime as st
import definitions as defs


def EnhancedGeolocation(network, user, condition, nAdjacents, nSlotsIA, rachFlag=False):
    yield network.env.timeout(defs.LTE_RTT)


    if nSlotsIA == 0:
        nSlotsIA, sinr, beamNet, beamUser = network.initialAccess('1', condition)

        user.setSINR(sinr)

    print("- Starting Initial Access with Enhanced Geolocation Algorithm.")
    print('- IA slots needed:', nSlotsIA)



#======================================================================================================================

def IterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA=0, feedback=0):
    yield network.env.timeout(defs.LTE_RTT)

    if nSlotsIA == 0:
        print("- Starting Initial Access with Enhanced Geolocation Algorithm.")
        nSlotsIA, sinr, beamNet, beamUser = network.initialAccess('2', condition)
        nSlotsIA -= 1

        user.setSINR(sinr)

        print('- IA slots needed:', nSlotsIA)


    firstPhaseSlots = (2*nAdjacents + 1)*user.numberBeams
    secondPhaseSlots = 2*user.numberBeams
    nFirstPhase = int((nSlotsIA - secondPhaseSlots)/firstPhaseSlots)
    
    ### This indicates if the first phase was completed or not at the former SSB
    firstPhaseTotal = False
    if ((nSlotsIA - secondPhaseSlots)%firstPhaseSlots) == 0 and (nSlotsIA - secondPhaseSlots)>0:
        firstPhaseTotal = True

    #Indicates a second phase which will be completed in one burst set
    secondPhaseFlag = False
    if nSlotsIA % secondPhaseSlots == 0 and int(nSlotsIA/secondPhaseSlots) == 1 and  feedback != 2:
        secondPhaseFlag = True
    '''
    #Indicates a truncated second phase
    secondPhasePart = False
    if nSlotsIA % secondPhaseSlots != 0 and int(nSlotsIA/secondPhaseSlots) == 0:
        secondPhasePart = True
    '''

    if not firstPhaseTotal:
        firstPhaseSlots = (nSlotsIA - secondPhaseSlots)%firstPhaseSlots

    if secondPhaseFlag:
        ### The variable is fistPhaseSlots but actually it is second phase!
        fistPhaseSlots = secondPhaseSlots
        firstPhaseTotal = True

    '''
    if secondPhasePart:
        ### The variable is fistPhaseSlots but actually it is second phase!
        fistPhaseSlots = nSlotsIA % secondPhasePart
        firstPhaseTotal = True
    '''

    burstStartTime = network.ssbIndex*defs.BURST_PERIOD
    burstEndTime = burstStartTime+defs.BURST_DURATION

    if feedback == 0:
        #During a Burst Set
        if (network.env.now >= burstStartTime) and (network.env.now < burstEndTime):
            print('id: %d - User Joined the network during a Burst Set.'%(user.id))

            #It's a SSB
            if network.ssbIndex % defs.RATIO != 0:
                print('id: %d - Current Burst Set is a SS Burst.'%(user.id))
                ssblock = int(round(((network.env.now - burstStartTime)/network.numerology['ofdmSymbolDuration']),0))
                remainingSSBlocks = int(network.numerology['ssblockMapping'][ssblock:].count(1)/4) #ssblocklength 4 symbols

                if firstPhaseSlots <= remainingSSBlocks:
                    if nFirstPhase == 0 or (nFirstPhase == 1 and firstPhaseTotal):
                        
                        #It will sweep for firstPhaseSlots or less slots and the give feedback of the first phase
                        nextRachTime = burstStartTime + (defs.RATIO - network.ssbIndex%defs.RATIO)*defs.BURST_PERIOD
                        
                        if not secondPhaseFlag:
                            print('id: %d - SS Blocks were sufficient to complete First Phase of Initial Access.'%(user.id))
                        else:
                            print('id: %d - SS Blocks were sufficient to complete Second Phase of Initial Access.'%(user.id))

                        #Will wait untill next RACH Opportunity to give the feedback
                        yield network.env.timeout(nextRachTime - network.env.now)
                        if not secondPhaseFlag:
                            network.env.process(IterativeGeolocation(network, user, condition, nAdjacents, secondPhaseSlots, 1))
                        else:
                            network.env.process(IterativeGeolocation(network, user, condition, nAdjacents, secondPhaseSlots, 2))

                    else:
                        print('id: %d - It will need another beam sweeping.'%(user.id))
                        
                        #The resulting SNR was not enough to satistfy the algorithm that, so it will try again
                        nextBurstSet = burstStartTime + defs.BURST_PERIOD
                        nSlotsIA -= firstPhaseSlots
                        
                        yield network.env.timeout(nextBurstSet - network.env.now)
                        network.env.process(IterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA, False))
                else:
                    #The SSB were not enough to complete a first phase of sweeping
                    print('id: %d - SS Blocks were not sufficient to complete Initial Access.'%(user.id))
                    
                    nSlotsIA = firstPhaseSlots - remainingSSBlocks
                    nextBurstSet = burstStartTime + defs.BURST_PERIOD
                    
                    #it will wait untill the next Burst Set and sweeping continues going on
                    yield network.env.timeout(nextBurstSet - network.env.now)
                    network.env.process(IterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA, False))

            #It's a RACH
            else:
                print('id: %d - Current Burst Set is a RACH Opportunity.'%(user.id))
                nextBurstSet = burstStartTime + defs.BURST_PERIOD
                
                #Ok, wait the next Burst Set
                yield network.env.timeout(nextBurstSet - network.env.now)
                network.env.process(IterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA, False))

        #Before/After a Burst Set
        else:
            nextBurstSet = burstStartTime + defs.BURST_PERIOD
            print('id: %d - User Joined the network after a Burst Set. Will wait untill %d' % (user.id,nextBurstSet))
            
            #Ok, wait the next Burst Set
            yield network.env.timeout(nextBurstSet - network.env.now)
            network.env.process(IterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA, False))


    else:
        print('id: %d - Current Burst Set is a RACH Opportunity and will give feedback.'%(user.id))
        if feedback == 1:# and not secondPhasePart:
            nextBurstSet = burstStartTime + defs.BURST_PERIOD
            
            print('id: %d - Started to give feedback of the first phase, will start second phase at %d' % (user.id,nextBurstSet))
            yield network.env.timeout(nextBurstSet - network.env.now)
            network.env.process(IterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA, 0))

        elif feedback == 2:
            feedbackSlot = network.inRangeUsers.index(user)
            count = 0
            ssb = 0
            for x in network.numerology['ssblockMapping']:
                count+=1
                if x==1:
                    ssb += 1
                if ssb == feedbackSlot:
                    break

            #count the number of ssblocks untill complete the RACH and each ssblock has 4 ofdmsymbols
            print('id: %d - Initial Access process completed at %d' %(user.id, network.env.now+(count*4*network.numerology['ofdmSymbolDuration'])))
            user.setIAtime(network.env.now + count*4*network.numerology['ofdmSymbolDuration'])
