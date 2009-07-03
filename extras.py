#!/usr/bin/env python

import random
import math

def roll(msg):
    try:
        total, report = process(msg)
        report, valid = "%s = %d" % (report, total), True
    except ValueError:
        report, valid = "%s is not a valid input, please try again." % msg, False
    return report, valid
    
def process(msg):
    report = ''
    total = 0
    if '+' in msg:
        pt, msg = msg.rsplit('+', 1)
        pttot, ptreport = process(pt)
        msgtot, msgreport = process(msg)
        total = pttot + msgtot
        report = ptreport + ' + ' + msgreport
    elif '-' in msg:
        pt, msg = msg.rsplit('-', 1)
        pttot, ptreport = process(pt)
        msgtot, msgreport = process(msg)
        total = pttot - msgtot
        report = ptreport + ' - ' + msgreport
    elif 'd' in msg.lower():
        if '1dawesome' in msg.lower():
            report += 'AWESOME!'
        else:
            x, y = msg.lower().split('d')
            rolls = []
            intx = int(x)
            if intx >= 2**10:    
                mean = (intx * (int(y)+1)) / 2
                total = int(random.normalvariate(mean,
                                        math.sqrt(intx * (int(y)**2 - 1)/12.0)))
                report = '(%d)' % total
            else:
                rolls = [random.randint(1,int(y)) for i in xrange(intx)]
                if int(x) < 10:
                    report += '(' + ', '.join((str(roll) for roll in rolls)) + ')'
                else:
                    report += '(%d)' % sum(rolls)
                total += sum(rolls)
    else:
        total += int(msg)
        report += msg.strip(' ')
    return total, report