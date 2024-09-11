from log.logtypes import asRun, retry, log, humanifyActionName
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

def test_humanifyActionName():
    an = "20221222T155624.415Z PT27S sched p0d7hbl0"
    humanifiedActionName = humanifyActionName(an)
    assert  humanifiedActionName == "2022-12-22T15:56:24.415Z PT27S sched p0d7hbl0"

def test_humanifyActionName_not_standard_action_name():
    an = "Merry Christmas PT27S sched p0d7hbl0"
    humanifiedActionName = humanifyActionName(an)
    assert  humanifiedActionName == "Merry Christmas PT27S sched p0d7hbl0"

def test_humanifyActionName_not_present():
    humanifiedActionName = humanifyActionName(None)
    assert  humanifiedActionName is None