import simpy as sp
from scipy import stats
import numpy as np
from subprocess import call, check_output
import sys
import simutime as st
import definitions as defs


def ExhaustiveSearch(network, condition, reciprocity):
    nSlotsIA, nominalCapacity, beamNet, beamUser= network.initialAccess('0', condition)

    if reciprocity == 0:
        ExhaustiveNonReciprocity(network, condition, nSlotsIA, False)
    elif reciprocity == 1:
        ExhaustivePartialReciprocity(network, condition, nSlotsIA, False)
    elif reciprocity == 2:
        ExhaustiveFullReciprocity(network, condition, nSlotsIA, beamNet, False)
    else:
        print('Not a valid reciprocity option were passed.')
        sys.exit()


def ExhaustiveNonReciprocity(network, condition, IAslots, rachFlag):
    burstStartTime = network.ssbIndex*defs.BURST_PERIOD
    burstEndTime = burstStartTime+defs.BURST_DURATION
    if not rachFlag:
        #During a Burst Set
        if (network.env.now >= burstStartTime) and (network.env.now < burstEndTime):

            #It's a SSB 
            if network.ssbIndex % defs.RATIO != 0:
                ssblock = int(round(((network.env.now - burstStartTime)/network.numerology['ofdmSymbolDuration']),0))
                remainingSSBlocks = int(network.numerology['ssblockMapping'][ssblock:].count(1)/4) #ssblocklength 4 symbols

                if IAslots <= remainingSSBlocks:
                    #It just need to complete the RACH
                    nextRachTime = burstStartTime + (network.ssbIndex%defs.RATIO)*defs.BURST_PERIOD
                    #Will wait untill next RACH Opportunity, IAslots == 0 means
                    #that it will try again the 
                    yield network.env.timeout(nextRachTime - network.env.now)
                    IAtime = ExhaustiveNonReciprocity(network, condition, 0, True)

                else:
                    #The SSB were not enough
                    slots = IAslots - remainingSSBlocks
                    nextSSB = burstStartTime + defs.BURST_PERIOD
                    #it will wait untill the next Burst Set and sweeping continues going on
                    yield network.env.timeout(nextSSB - network.env.now)
                    IAtime = ExhaustiveNonReciprocity(network, condition, slots, False)

            #It's a RACH
            else:
                nextBurstSet = burstStartTime + defs.BURST_PERIOD
                #Ok, wait the next Burst Set
                yield network.env.timeout(nextBurstSet - network.env.now)
                IAtime = ExhaustiveNonReciprocity(network, condition, IAslots,False)

        #Before/After a Burst Set
        else:
            nextBurstSet = burstStartTime + defs.BURST_PERIOD
            yield network.env.timeout(nextBurstSet - network.env.now)
            IAtime = ExhaustiveNonReciprocity(network, condition, IAslots, False)

    #Now it needs a RACH opportunity
    # We are not considering RACH collision yet :(
    else:
        #Lets do a initial access and see how many slots the RACH will take
        if IAslots == 0:
            #IAslots, nominalCapacity, beamNet, beamUser= network.initialAccess('0', condition)
            IAslots = network.antennaBeams * network.inRangeUsers[-1].antennaBeams
        
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
            return count*4*network.numerology['ofdmSymbolDuration']

        #it will need more than one RACH Opportunity
        else:
            slots = IAslots - network.numerology['ssblocks']
            nextRach = burstStartTime + defs.RACH_PERIOD
            yield network.env.timeout(nextRach - network.env.now)
            IAtime = ExhaustiveNonReciprocity(network, condition, slots, True)

    return IAtime + (network.env.now - burstStartTime)


def ExhaustivePartialReciprocity(network, condition, IASlots, rachFlag):
    burstStartTime = network.ssbIndex*defs.BURST_PERIOD
    burstEndTime = burstStartTime+defs.BURST_DURATION
    if not rachFlag:
        #During a Burst Set
        if (network.env.now >= burstStartTime) and (network.env.now < burstEndTime):

            #It's a SSB 
            if network.ssbIndex % defs.RATIO != 0:
                ssblock = int(round(((network.env.now - burstStartTime)/network.numerology['ofdmSymbolDuration']),0))
                remainingSSBlocks = int(network.numerology['ssblockMapping'][ssblock:].count(1)/4) #ssblocklength 4 symbols

                if IAslots <= remainingSSBlocks:
                    #It just need to complete the RACH
                    nextRachTime = burstStartTime + (network.ssbIndex%defs.RATIO)*defs.BURST_PERIOD
                    #Will wait untill next RACH Opportunity, IAslots == 0 means
                    #that it will try again the 
                    yield network.env.timeout(nextRachTime - network.env.now)
                    IAtime = ExhaustiveNonReciprocity(network, condition, 0, True)

                else:
                    #The SSB were not enough
                    slots = IAslots - remainingSSBlocks
                    nextSSB = burstStartTime + defs.BURST_PERIOD
                    #it will wait untill the next Burst Set and sweeping continues going on
                    yield network.env.timeout(nextSSB - network.env.now)
                    IAtime = ExhaustiveNonReciprocity(network, condition, slots, False)

            #It's a RACH
            else:
                nextBurstSet = burstStartTime + defs.BURST_PERIOD
                #Ok, wait the next Burst Set
                yield network.env.timeout(nextBurstSet - network.env.now)
                IAtime = ExhaustiveNonReciprocity(network, condition, IAslots,False)

        #Before/After a Burst Set
        else:
            nextBurstSet = burstStartTime + defs.BURST_PERIOD
            yield network.env.timeout(nextBurstSet - network.env.now)
            IAtime = ExhaustiveNonReciprocity(network, condition, IAslots, False)

    #Now it needs a RACH opportunity
    # We are not considering RACH collision yet :(
    else:
        #Lets do a initial access and see how many slots the RACH will take
        if IAslots == 0:
            IAslots = network.antennaBeams
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
            return count*4*network.numerology['ofdmSymbolDuration']

        #it will need more than one RACH Opportunity
        else:
            slots = IAslots - network.numerology['ssblocks']
            nextRach = burstStartTime + defs.RACH_PERIOD
            yield network.env.timeout(nextRach - network.env.now)
            IAtime = ExhaustiveNonReciprocity(network, condition, slots, True)
    return IAtime + (network.env.now - burstStartTime)



def ExhaustiveFullReciprocity(network, condition, IASlots, beamNet, rachFlag):
    burstStartTime = network.ssbIndex*defs.BURST_PERIOD
    burstEndTime = burstStartTime+defs.BURST_DURATION
    if not rachFlag:
        #During a Burst Set
        if (network.env.now >= burstStartTime) and (network.env.now < burstEndTime):

            #It's a SSB 
            if network.ssbIndex % defs.RATIO != 0:
                ssblock = int(round(((network.env.now - burstStartTime)/network.numerology['ofdmSymbolDuration']),0))
                remainingSSBlocks = int(network.numerology['ssblockMapping'][ssblock:].count(1)/4) #ssblocklength 4 symbols

                if IAslots <= remainingSSBlocks:
                    #It just need to complete the RACH
                    nextRachTime = burstStartTime + (network.ssbIndex%defs.RATIO)*defs.BURST_PERIOD
                    #Will wait untill next RACH Opportunity, IAslots == 0 means
                    #that it will try again the 
                    yield network.env.timeout(nextRachTime - network.env.now)
                    IAtime = ExhaustiveNonReciprocity(network, condition, 0, beamNet, True)

                else:
                    #The SSB were not enough
                    slots = IAslots - remainingSSBlocks
                    nextSSB = burstStartTime + defs.BURST_PERIOD
                    #it will wait untill the next Burst Set and sweeping continues going on
                    yield network.env.timeout(nextSSB - network.env.now)
                    IAtime = ExhaustiveNonReciprocity(network, condition, slots, beamNet, False)

            #It's a RACH
            else:
                nextBurstSet = burstStartTime + defs.BURST_PERIOD
                #Ok, wait the next Burst Set
                yield network.env.timeout(nextBurstSet - network.env.now)
                IAtime = ExhaustiveNonReciprocity(network, condition, IAslots, beamNet, False)

        #Before/After a Burst Set
        else:
            nextBurstSet = burstStartTime + defs.BURST_PERIOD
            yield network.env.timeout(nextBurstSet - network.env.now)
            IAtime = ExhaustiveNonReciprocity(network, condition, IAslots, beamNet, False)

    #Now it needs a RACH opportunity
    # We are not considering RACH collision yet :(
    # Also no treats the case which there are more antennas beams at BS side tha SS Blocks
    else:
        #It will be solved with only one RACH Opportunity
        if IAslots <= network.numerology['ssblocks']:
            count = 0
            ssb = 0
            for x in network.numerology['ssblockMapping']:
                count+=1
                if x==1:
                    ssb += 1
                if ssb == beamNet:
                    break
        
            #count the number of ssblocks untill complete the RACH and each ssblock has 4 ofdmsymbols
            return count*4*network.numerology['ofdmSymbolDuration']

    return IAtime + (network.env.now - burstStartTime)
