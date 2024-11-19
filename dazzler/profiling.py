from datetime import datetime

# Commands that can be used to top and tail code calls and see how long they are running.

def logStart(sid, functionName):
    start = datetime.now()
    print(f'{sid} profiling>{functionName} start 0')
    return start

def logEnd(sid, functionName, start):
    end = datetime.now()
    duration = end - start
    print(f'{sid} profiling>{functionName} end duration = {duration}')
    return end