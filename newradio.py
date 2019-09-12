import simpy as sp
import numpy as np

def burstSet(burstDuration, burstPeriod, env):
    counter = 1
    while True:
        if (counter % 3) != 0:
            print('A new burst set is starting at %d' % env.now)
            yield env.timeout(burstDuration)
            print('The burst set has finished at %d' % env.now)
            yield env.timeout(burstPeriod - burstDuration)
        else:
            yield env.timeout(burstPeriod)
        counter += 1

def rachOpportunity(rachDuration, rachPeriod, env):
    while True:
        yield env.timeout(rachPeriod)
        print('A new rach opportunity is starting at %d' % env.now)
        yield env.timeout(rachDuration)
        print('The rach opportunity  has finished at %d' % env.now)
        yield env.timeout(rachPeriod - rachDuration)

def erlangSampler(rate, k):
    return np.random.gamma(k, rate)/np.math.factorial(k-1)

def userArrival(nUsers, rate, counter, env):
    while True:
        arrival = np.random.poisson(100)
        yield env.timeout(arrival)
        counter.put(counter.get()+1)
        print('There are %d users at %d' % (counter.get(), env.now))
        
        
def userSkip(nUsers, rate, counter, env):
    while True:
        n = counter.get()
        print(n)
        skip = erlangSampler(rate,nUsers)
        yield env.timeout(skip)
        counter.put(n-1)
        print('There are %d users at %d' % (counter.get(), env.now))
        

if __name__ == "__main__":
    nUsers = 10
    env = sp.Environment()
    activeUsers = sp.Store(env)
    env.process(burstSet(5,20,env))
    env.process(rachOpportunity(5,40,env))
    env.process(userArrival(nUsers,100,activeUsers,env))
    env.process(userSkip(nUsers,100,activeUsers,env))
    env.run(until=10000)
