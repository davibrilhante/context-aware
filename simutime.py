class seconds(float):
    def __init__(self, amount):
        self.amount = amount
    '''
    def year(self):
        return self.amount/(365*24*60*60)
    def month(self): 
        return self.amount/(30*24*60*60)
    def week(self): 
        return self.amount/(7*24*60*60)
    def day(self): 
        return self.amount/(24*60*60)
    '''
    def hour(self): 
        return self.amount/60*60
    def minute(self): 
        return self.amount/60
    def milli(self): 
        return self.amount*1e3
    def micro(self): 
        return self.amount*1e6
    def nano(self): 
        return self.amount*1e9

class milliseconds(float):
    def __init__(self, amount):
        self.amount = amount
    def minute(self):
        return self.amount/(60*1e3)
    def seconds(self): 
        return self.amount/1e3
    def micro(self): 
        return self.amount*1e3
    def nano(self): 
        return self.amount*1e6


class microseconds(float):
    def __init__(self, amount):
        self.amount = amount
    def minute(self):
        return self.amount/(60*1e6)
    def seconds(self): 
        return self.amount/1e6
    def milli(self): 
        return self.amount/1e3
    def nano(self): 
        return self.amount*1e3


class nanoseconds(float):
    def __init__(self, amount):
        self.amount = amount
    def minute(self):
        return self.amount/(60*1e9)
    def seconds(self): 
        return self.amount/1e9
    def milli(self): 
        return self.amount/1e6
    def micro(self): 
        return self.amount/1e3

def divide(a,b):
    if type(a) == type(b):
        return a/b
    else:
        1
