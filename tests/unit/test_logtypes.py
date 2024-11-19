from log.logtypes import asRun, retry, log
from medialivehelpers.action import Action
from isodate import parse_datetime, parse_duration

def test_early():
    t = parse_datetime("2021-06-21T00:00:00Z")
    a = Action('Initial Channel Input', t + parse_duration('PT10S') )
    log('', t, a, 'log')

def test_late():
    t = parse_datetime("2021-06-21T00:00:00Z")
    a = Action('Initial Channel Input', t - parse_duration('PT10S'))
    log('', t, a, 'log')

def test_ontime():
    t = parse_datetime("2021-06-21T00:00:00Z")
    a = Action('Initial Channel Input', t)
    log('', t, a, 'log')

def test_asRun():
    t = parse_datetime("2021-06-21T00:00:00Z")
    a = Action('Initial Channel Input', t + parse_duration('PT10S') )
    asRun('', t, a)

def test_retry():
    t = parse_datetime("2021-06-21T00:00:00Z")
    a = Action('Initial Channel Input', t)
    retry('', t, a)