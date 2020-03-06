import simpy as sp
from scipy import stats
import numpy as np
from subprocess import call, check_output
import sys

import simutime as st
import definitions as defs


def EnhancedGeolocation(network, user, condition, nAdjacents, nSlotsIA=0, rachFlag=False):


    if nSlotsIA == 0 and not rachFlag:
        yield network.env.timeout(defs.LTE_RTT)
        print("- Starting Initial Access with Enhanced Geolocation Algorithm.")
        nSlotsIA, sinr, beamNet, beamUser = network.initialAccess('2', condition)
        nSlotsIA -= 1
        user.setSINR(sinr)
        print('- SNR:', sinr)
        print('- IA slots needed:', nSlotsIA)


    slotsPerPhase = user.numberBeams * (2*nAdjacents + 1)

    if nSlotsIA % slotsPerPhase == 0:
        currentPhaseSlots = slotsPerPhase
    else:
        currentPhaseSlots = nSlotsIA % slotsPerPhase 
    
    burstStartTime = network.ssbIndex*defs.BURST_PERIOD
    burstEndTime = burstStartTime+defs.BURST_DURATION

    if not rachFlag:
        #During a Burst Set
        if (network.env.now >= burstStartTime) and (network.env.now < burstEndTime):
            print('id: %d - User Joined the network during a Burst Set.'%(user.id))
            #It's a SSB
            if network.ssbIndex % defs.RATIO != 0:
                print('id: %d - Current Burst Set is a SS Burst.'%(user.id))
                ssblock = int(round(((network.env.now - burstStartTime)/network.numerology['ofdmSymbolDuration']),0))
                remainingSSBlocks = int(network.numerology['ssblockMapping'][ssblock:].count(1)/4) #ssblocklength 4 symbols

                if currentPhaseSlots <= remainingSSBlocks and network.availableSlots >= currentPhaseSlots:
                    print('id: %d - SS Blocks were sufficient to complete a Phase of Initial Access.'%(user.id))
                    
                    nextRachTime = burstStartTime + (defs.RATIO - network.ssbIndex%defs.RATIO)*defs.BURST_PERIOD
                    nSlotsIA -= currentPhaseSlots
                    network.availableSlots -= currentPhaseSlots
                    yield network.env.timeout(nextRachTime - network.env.now)
                    network.env.process(EnhancedGeolocation(network, user, condition, nAdjacents, nSlotsIA, True))

                else:
                    print('id: %d - SS Blocks were not sufficient to complete Initial Access.'%(user.id))
                    
                    #The resulting SNR was not enough to satistfy the algorithm that, so it will try again
                    nextBurstSet = burstStartTime + defs.BURST_PERIOD
                    if network.availableSlots < currentPhaseSlots:
                        nSlotsIA -= network.availableSlots
                        network.availableSlots = 0
                    else:
                        nSlotsIA -= remainingSSBlocks
                        network.availableSlots -= remainingSSBlocks

                    yield network.env.timeout(nextBurstSet - network.env.now)
                    network.env.process(EnhancedGeolocation(network, user, condition, nAdjacents, nSlotsIA, False))

            # It's a RACH Opportunity
            else:
                print('id: %d - Current Burst Set is a RACH Opportunity.'%(user.id))
                nextBurstSet = burstStartTime + defs.BURST_PERIOD

                yield network.env.timeout(nextBurstSet - network.env.now)
                network.env.process(EnhancedGeolocation(network, user, condition, nAdjacents, nSlotsIA, False))

        #After a Burst Set
        else:
            nextBurstSet = burstStartTime + defs.BURST_PERIOD
            print('id: %d - User Joined the network after a Burst Set. Will wait untill %d' % (user.id,nextBurstSet))

            yield network.env.timeout(nextBurstSet - network.env.now)
            network.env.process(EnhancedGeolocation(network, user, condition, nAdjacents, nSlotsIA, False))


    else:
        print('id: %d - Current Burst Set is a RACH Opportunity and will give feedback.'%(user.id))

        #Will repeat the process after feedback
        if nSlotsIA > 0:
            nextBurstSet = burstStartTime + defs.BURST_PERIOD
            
            print('id: %d - Started to give feedback another phase will start at %d' % (user.id,nextBurstSet))
            yield network.env.timeout(nextBurstSet - network.env.now)
            network.env.process(EnhancedGeolocation(network, user, condition, nAdjacents, nSlotsIA, False))

        #Beam Sweeping succeed, just need the last feedback
        else:
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
            network.inRangeUsers.remove(user)
            network.associatedUsers.append(user)



#======================================================================================================================

def IterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA=0, feedback=0):

    if nSlotsIA == 0:
        yield network.env.timeout(defs.LTE_RTT)
        print("- Starting Initial Access with Iterative Geolocation Algorithm.")
        nSlotsIA, sinr, beamNet, beamUser = network.initialAccess('3', condition)
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

                if firstPhaseSlots <= remainingSSBlocks and network.availableSlots >= firstPhaseSlots:
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
                            network.env.process(IterativeGeolocation(network, user, condition, nAdjacents, 0, 2))#secondPhaseSlots, 2))

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
                    if network.availableSlots < firstPhaseSlots:
                        nSlotsIA -= network.availableSlots
                        network.availableSlots = 0
                    else:
                        nSlotsIA -= firstPhaseSlots - remainingSSBlocks

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
            network.inRangeUsers.remove(user)
            network.associatedUsers.append(user)




def ModIterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA=0, feedback=0):

    if nSlotsIA == 0 and feedback ==0:
        user.setPowerOnTime(network.env.now)
        yield network.env.timeout(defs.LTE_RTT)
        print("- Starting Initial Access with Modified Iterative Geolocation Algorithm.")
        nSlotsIA, sinr, beamNet, beamUser = network.initialAccess('3', condition)
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

    if not firstPhaseTotal:
        firstPhaseSlots = (nSlotsIA - secondPhaseSlots)%firstPhaseSlots

    if secondPhaseFlag:
        ### The variable is fistPhaseSlots but actually it is second phase!
        fistPhaseSlots = secondPhaseSlots
        firstPhaseTotal = True


    burstStartTime = network.ssbIndex*defs.BURST_PERIOD
    burstEndTime = burstStartTime+defs.BURST_DURATION

    if feedback == 0:
        #During a Burst Set
        if (network.env.now >= burstStartTime) and (network.env.now < burstEndTime):
            print('id: %d - User Joined the network during a Burst Set.'%(user.id))

            #It's a SSB
            if network.ssbIndex % defs.RATIO != 0:
                print('id: %d - Current Burst Set is a SS Burst. Now: %d'%(user.id,network.env.now))
                #How many SS Blocks had happened until now?
                ssblock = int(round(((network.env.now - burstStartTime)/network.numerology['ofdmSymbolDuration']),0))
                remainingSSBlocks = int(network.numerology['ssblockMapping'][ssblock:].count(1)/4) #ssblocklength 4 symbols

                if firstPhaseSlots <= remainingSSBlocks and network.availableSlots >= firstPhaseSlots:
                    if nFirstPhase == 0 or (nFirstPhase == 1 and firstPhaseTotal):
                        
                        #It will sweep for firstPhaseSlots or less slots and the give feedback of the first phase
                        #nextRachTime = burstStartTime + (defs.RATIO - network.ssbIndex%defs.RATIO)*defs.BURST_PERIOD
                        
                        if not secondPhaseFlag:
                            sweeptime = network.numerology['ssblockMapping'][:ssblock+firstPhaseSlots+1].count(1)*network.numerology['ofdmSymbolDuration']
                            yield network.env.timeout(sweeptime)
                            #network.availableSlots -= firstPhaseSlots
                            print('id: %d - SS Blocks were sufficient to complete First Phase of Initial Access. Now: %d'%(user.id,network.env.now))
                        else:
                            sweeptime = network.numerology['ssblockMapping'][ssblock:ssblock+secondPhaseSlots+1].count(1)*network.numerology['ofdmSymbolDuration']
                            yield network.env.timeout(sweeptime)
                            #network.availableSlots -= firstPhaseSlots
                            print('id: %d - SS Blocks were sufficient to complete Second Phase of Initial Access.Now: %d'%(user.id,network.env.now))

                        #yield network.env.timeout(nextRachTime - network.env.now)
                        #Will wait untill the feedback received at the control channel 
                        if not secondPhaseFlag:
                            yield network.env.timeout(defs.LTE_RTT)
                            network.availableSlots -= firstPhaseSlots
                            network.env.process(ModIterativeGeolocation(network, user, condition, nAdjacents, secondPhaseSlots, 1))
                        else:
                            #yield network.env.timeout(defs.LTE_RTT)
                            #I Will keep the last feedback as a RACH to provide Uplink Synchronization
                            nextRachTime = burstStartTime + (defs.RATIO - network.ssbIndex%defs.RATIO)*defs.BURST_PERIOD
                            yield network.env.timeout(nextRachTime - network.env.now)
                            network.availableSlots -= firstPhaseSlots
                            network.env.process(ModIterativeGeolocation(network, user, condition, nAdjacents, 0, 2))

                    else:
                        print('id: %d - It will need another beam sweeping.'%(user.id))
                        
                        #The resulting SNR was not enough to satistfy the algorithm that, so it will try again
                        nextBurstSet = burstStartTime + defs.BURST_PERIOD
                        nSlotsIA -= firstPhaseSlots
                        
                        yield network.env.timeout(nextBurstSet - network.env.now)
                        #Next try will take place after feedback and the next burst set starts
                        #yield network.env.timeout(defs.LTE_RTT + (nextBurstSet - network.env.now))
                        #network.env.process(ModIterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA, False))
                        network.availableSlots -= firstPhaseSlots
                        network.env.process(ModIterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA))
                else:
                    #The SSB were not enough to complete a first phase of sweeping
                    print('id: %d - SS Blocks were not sufficient to complete Initial Access.'%(user.id))
                    if network.availableSlots < firstPhaseSlots:
                        nSlotsIA -= network.availableSlots
                    else:
                        nSlotsIA -= firstPhaseSlots - remainingSSBlocks

                    network.availableSlots = 0
                    nextBurstSet = burstStartTime + defs.BURST_PERIOD
                    
                    #it will wait untill the next Burst Set and sweeping continues going on
                    yield network.env.timeout(nextBurstSet - network.env.now)
                    #network.env.process(ModIterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA, False))
                    network.env.process(ModIterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA))

            #It's a RACH
            else:
                print('id: %d - Current Burst Set is a RACH Opportunity.'%(user.id))
                nextBurstSet = burstStartTime + defs.BURST_PERIOD
                
                #Ok, wait the next Burst Set
                yield network.env.timeout(nextBurstSet - network.env.now)
                #network.env.process(ModIterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA, False))
                network.env.process(ModIterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA))

        #Before/After a Burst Set
        else:
            nextBurstSet = burstStartTime + defs.BURST_PERIOD
            print('id: %d - User Joined the network after a Burst Set. Will wait untill %d' % (user.id,nextBurstSet))
            
            #Ok, wait the next Burst Set
            yield network.env.timeout(nextBurstSet - network.env.now)
            #network.env.process(ModIterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA, False))
            network.env.process(ModIterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA))


    else:
        #print('id: %d - Current Burst Set is a RACH Opportunity and will give feedback.'%(user.id))
        print('id: %d - User finished a phase. Time to send feedback.'%(user.id))
        if feedback == 1:# and not secondPhasePart:
            '''
            nextBurstSet = burstStartTime + defs.BURST_PERIOD
            print('id: %d - Started to give feedback of the first phase, will start second phase at %d' % (user.id,nextBurstSet))
            yield network.env.timeout(nextBurstSet - network.env.now)
            '''
            print('id: %d - User already sent the feedback at the control channel. Calling Second Phase at %d. Now: %d'%(user.id,0,network.env.now))
            network.env.process(ModIterativeGeolocation(network, user, condition, nAdjacents, nSlotsIA, 0))

        elif feedback == 2:
            #'''
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
            #'''

            #I will keep the last feedback as a RACH to provide Synchronization at the Uplink
            #Wait the feedback reception at the control channel
            #print('id: %d - Initial Access process completed at %d' %(user.id, network.env.now))
            #user.setIAtime(network.env.now)
            network.inRangeUsers.remove(user)
            network.associatedUsers.append(user)
