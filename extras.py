#!/usr/bin/env python

import random

def roll(msg):
    try:
        total, report = process(msg)
        report = "%s = %d" % (report, total)
    except ValueError:
        report = "%s is not a valid input, please try again." % msg
    print report
    
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
    elif 'd' in msg:
        x, y = msg.split('d')
        rolls = [random.randint(1,int(y)) for i in xrange(int(x))]
        report += '(' + ', '.join((str(roll) for roll in rolls)) + ')'
        total += sum(rolls)
    else:
        total += int(msg)
        report += msg.strip(' ')
    return total, report