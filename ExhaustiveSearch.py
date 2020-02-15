import simpy as sp
from scipy import stats
import numpy as np
from subprocess import call, check_output
import sys

import simutime as st
import definitions as defs
#from components import Network



def ExhaustiveNonReciprocity(network, user, condition, IAslots, rachFlag):
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

                if IAslots <= remainingSSBlocks:
                    #It just need to complete the RACH
                    print('id: %d - SS Blocks were sufficient to complete Initial Access.'%(user.id))
                    nextRachTime = burstStartTime + (defs.RATIO - network.ssbIndex%defs.RATIO)*defs.BURST_PERIOD
                    #Will wait untill next RACH Opportunity, IAslots == 0 means
                    #that it will try again the 
                    yield network.env.timeout(nextRachTime - network.env.now)
                    network.env.process(ExhaustiveNonReciprocity(network, user, condition, 0, True))

                else:
                    #The SSB were not enough
                    print('id: %d - SS Blocks were not sufficient to complete Initial Access.'%(user.id))
                    slots = IAslots - remainingSSBlocks
                    nextSSB = burstStartTime + defs.BURST_PERIOD
                    #it will wait untill the next Burst Set and sweeping continues going on
                    yield network.env.timeout(nextSSB - network.env.now)
                    network.env.process(ExhaustiveNonReciprocity(network, user, condition, slots, False))

            #It's a RACH
            else:
                print('id: %d - Current Burst Set is a RACH Opportunity.'%(user.id))
                nextBurstSet = burstStartTime + defs.BURST_PERIOD
                #Ok, wait the next Burst Set
                yield network.env.timeout(nextBurstSet - network.env.now)
                network.env.process(ExhaustiveNonReciprocity(network, user, condition, IAslots,False))

        #Before/After a Burst Set
        else:
            nextBurstSet = burstStartTime + defs.BURST_PERIOD
            print('id: %d - User Joined the network after a Burst Set. Will wait untill %d' % (user.id,nextBurstSet))
            yield network.env.timeout(nextBurstSet - network.env.now)
            print(network.env.now)
            network.env.process(ExhaustiveNonReciprocity(network, user, condition, IAslots, False))

    #Now it needs a RACH opportunity
    # We are not considering RACH collision yet :(
    else:
        print('id: %d - Starting RACH process at %d' %(user.id, network.env.now))
        #Lets do a initial access and see how many slots the RACH will take
        if IAslots == 0:
            #IAslots, nominalCapacity, beamNet, beamUser= network.initialAccess('0', condition)
            IAslots = network.numberBeams * user.numberBeams
        
        #It will be solved with only one RACH Opportunity
        if IAslots <= network.numerology['ssblocks']:
            count = 0
            ssb = 0
            for x in network.numerology['ssblockMapping']:
                count+=1
                if x==1:
                    ssb += 1
                if ssb == IAslots:
                    break
        
            #count the number of ssblocks untill complete the RACH and each ssblock has 4 ofdmsymbols
            print('id: %d - RACH process completed at %d' %(user.id, network.env.now+(count*4*network.numerology['ofdmSymbolDuration'])))
            user.setIAtime(network.env.now + count*4*network.numerology['ofdmSymbolDuration'])

        #it will need more than one RACH Opportunity
        else:
            slots = IAslots - network.numerology['ssblocks']
            nextRach = burstStartTime + defs.RACH_PERIOD
            yield network.env.timeout(nextRach - network.env.now)
            network.env.process(ExhaustiveNonReciprocity(network, user, condition, slots, True))






def ExhaustivePartialReciprocity(network, user, condition, IAslots, rachFlag):
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

                if IAslots <= remainingSSBlocks:
                    #It just need to complete the RACH
                    print('id: %d - SS Blocks were sufficient to complete Initial Access.'%(user.id))
                    nextRachTime = burstStartTime + (defs.RATIO - network.ssbIndex%defs.RATIO)*defs.BURST_PERIOD
                    #Will wait untill next RACH Opportunity, IAslots == 0 means
                    #that it will try again the 
                    yield network.env.timeout(nextRachTime - network.env.now)
                    network.env.process(ExhaustivePartialReciprocity(network, user, condition, 0, True))

                else:
                    #The SSB were not enough
                    print('id: %d - SS Blocks were not sufficient to complete Initial Access.'%(user.id))
                    slots = IAslots - remainingSSBlocks
                    nextSSB = burstStartTime + defs.BURST_PERIOD
                    #it will wait untill the next Burst Set and sweeping continues going on
                    yield network.env.timeout(nextSSB - network.env.now)
                    network.env.process(ExhaustivePartialReciprocity(network, user, condition, slots, False))

            #It's a RACH
            else:
                print('id: %d - Current Burst Set is a RACH Opportunity.'%(user.id))
                nextBurstSet = burstStartTime + defs.BURST_PERIOD
                #Ok, wait the next Burst Set
                yield network.env.timeout(nextBurstSet - network.env.now)
                network.env.process(ExhaustivePartialReciprocity(network, user, condition, IAslots,False))

        #Before/After a Burst Set
        else:
            nextBurstSet = burstStartTime + defs.BURST_PERIOD
            print('id: %d - User Joined the network after a Burst Set. Will wait untill %d' % (user.id,nextBurstSet))
            yield network.env.timeout(nextBurstSet - network.env.now)
            print(network.env.now)
            network.env.process(ExhaustivePartialReciprocity(network, user, condition, IAslots, False))

    #Now it needs a RACH opportunity
    # We are not considering RACH collision yet :(
    else:
        print('id: %d - Starting RACH process at %d' %(user.id, network.env.now))
        #Lets do a initial access and see how many slots the RACH will take
        if IAslots == 0:
            #IAslots, nominalCapacity, beamNet, beamUser= network.initialAccess('0', condition)
            IAslots = network.numberBeams
        
        #It will be solved with only one RACH Opportunity
        if IAslots <= network.numerology['ssblocks']:
            count = 0
            ssb = 0
            for x in network.numerology['ssblockMapping']:
                count+=1
                if x==1:
                    ssb += 1
                if ssb == IAslots:
                    break
        
            #count the number of ssblocks untill complete the RACH and each ssblock has 4 ofdmsymbols
            print('id: %d - RACH process completed at %d' %(user.id, network.env.now+(count*4*network.numerology['ofdmSymbolDuration'])))
            user.setIAtime(network.env.now + count*4*network.numerology['ofdmSymbolDuration'])

        #it will need more than one RACH Opportunity
        else:
            slots = IAslots - network.numerology['ssblocks']
            nextRach = burstStartTime + defs.RACH_PERIOD
            yield network.env.timeout(nextRach - network.env.now)
            network.env.process(ExhaustivePartialReciprocity(network, user, condition, slots, True))





def ExhaustiveFullReciprocity(network, user, condition, IAslots, rachFlag):
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

                if IAslots <= remainingSSBlocks:
                    #It just need to complete the RACH
                    print('id: %d - SS Blocks were sufficient to complete Initial Access.'%(user.id))
                    nextRachTime = burstStartTime + (defs.RATIO - network.ssbIndex%defs.RATIO)*defs.BURST_PERIOD
                    #Will wait untill next RACH Opportunity, IAslots == 0 means
                    #that it will try again the 
                    rachSlot = network.inRangeUsers.index(user)
                    yield network.env.timeout(nextRachTime - network.env.now)
                    network.env.process(ExhaustiveFullReciprocity(network, user, condition, rachSlot, True))

                else:
                    #The SSB were not enough
                    print('id: %d - SS Blocks were not sufficient to complete Initial Access.'%(user.id))
                    slots = IAslots - remainingSSBlocks
                    nextSSB = burstStartTime + defs.BURST_PERIOD
                    #it will wait untill the next Burst Set and sweeping continues going on
                    yield network.env.timeout(nextSSB - network.env.now)
                    network.env.process(ExhaustiveFullReciprocity(network, user, condition, slots, False))

            #It's a RACH
            else:
                print('id: %d - Current Burst Set is a RACH Opportunity.'%(user.id))
                nextBurstSet = burstStartTime + defs.BURST_PERIOD
                #Ok, wait the next Burst Set
                yield network.env.timeout(nextBurstSet - network.env.now)
                network.env.process(ExhaustiveFullReciprocity(network, user, condition, IAslots,False))

        #Before/After a Burst Set
        else:
            nextBurstSet = burstStartTime + defs.BURST_PERIOD
            print('id: %d - User Joined the network after a Burst Set. Will wait untill %d' % (user.id,nextBurstSet))
            yield network.env.timeout(nextBurstSet - network.env.now)
            print(network.env.now)
            network.env.process(ExhaustiveFullReciprocity(network, user, condition, IAslots, False))

    #Now it needs a RACH opportunity
    # We are not considering RACH collision yet :(
    # This also does not treats the case which there are more antennas beams at BS side than SS Blocks
    else:
        print('id: %d - Starting RACH process at %d' %(user.id, network.env.now))
        #It will be solved with only one RACH Opportunity
        if IAslots <= network.numerology['ssblocks']:
            count = 0
            ssb = 0
            for x in network.numerology['ssblockMapping']:
                count+=1
                if x==1:
                    ssb += 1
                if ssb == IAslots:
                    break
        
            #count the number of ssblocks untill complete the RACH and each ssblock has 4 ofdmsymbols
            print('id: %d - RACH process completed at %d' %(user.id, network.env.now+(count*4*network.numerology['ofdmSymbolDuration'])))
            user.setIAtime(network.env.now + count*4*network.numerology['ofdmSymbolDuration'])
            network.inRangeUsers.remove(user)
            network.associatedUsers.append(user)




def ExhaustiveSearch(network, user, condition, reciprocity):
    #nSlotsIA, nominalCapacity, beamNet, beamUser = network.initialAccess('0', condition)
    nSlotsIA, sinr, beamNet, beamUser = network.initialAccess('0', condition)
    user.setSINR(sinr)
    now = network.env.now

    IAtime = 0

    print("- Starting Initial Access Exhaustive Search.")
    print('- IA slots needed:', nSlotsIA)

    if reciprocity == 0:
        print("- Non Reciprocity chosen.")
        network.env.process(ExhaustiveNonReciprocity(network, user, condition, nSlotsIA, False))
    elif reciprocity == 1:
        print("- Partial Reciprocity chosen.")
        network.env.process(ExhaustivePartialReciprocity(network, user, condition, nSlotsIA, False))
    elif reciprocity == 2:
        print("- Full Reciprocity chosen.")
        network.env.process(ExhaustiveFullReciprocity(network, user, condition, nSlotsIA, False))
    else:
        print('- Not a valid reciprocity option were passed.')
        sys.exit()
    #return 0#user.iatime
