class Time:
    def __init__(self):
        self.type = None
        self.amount = 0

    def seconds(self, amount):
        if self.type == 'year':
            self.amount = amount*365*24*60*60
        elif self.type == 'month':
            self.amount = amount*30*24*60*60
        elif self.type == 'week':
            self.amount = amount*7*24*60*60
        elif self.type == 'day':
            self.amount = amount*24*60*60
        elif self.type =='hour':
            self.amount = amount*60*60
        elif self.type =='minute':
            self.amount = amount*60
        elif self.type == None or self.type == 'seconds':
            self.amount = amount
        elif self.type =='milli':
            self.amount = amount/1e3
        elif self.type =='micro':
            self.amount = amount/1e6
        elif self.type =='nano':
            self.amount = amount/1e9
        self.type = 'seconds'

    def milliseconds(self, amount):
        if self.type =='minute':
            self.amount = amount*60*1e3
        elif self.type == 'seconds':
            self.amount = amount*1e3
        elif self.type =='milli' or self.type ==None:
            self.amount = amount
        elif self.type =='micro':
            self.amount = amount/1e3
        elif self.type =='nano':
            self.amount = amount/1e6
        self.type = 'milli'

    def microseconds(self, amount):
        if self.type =='minute':
            self.amount = amount*60*1e6
        elif self.type == 'seconds':
            self.amount = amount*1e6
        elif self.type =='milli':
            self.amount = amount*1e3
        elif self.type =='micro' or self.type ==None:
            self.amount = amount
        elif self.type =='nano':
            self.amount = amount/1e3
        self.type = 'micro'

    def microseconds(self, amount):
        if self.type =='minute':
            self.amount = amount*60*1e9
        elif self.type == 'seconds':
            self.amount = amount*1e9
        elif self.type =='milli':
            self.amount = amount*1e6
        elif self.type =='micro':
            self.amount = amount*1e3
        elif self.type =='nano' or self.type ==None:
            self.amount = amount
        self.type = 'nano'
