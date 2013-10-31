# from alfred.persistence import getIncludingGroups


# def testInclusion():
#     testGroups = dict(sensors=['Temp', 'Hum'], others=['Hum'], mixed=['others'])
#     assert getIncludingGroups('Temp', testGroups) == set(('sensors', 'Temp'))
#     assert getIncludingGroups('Var', testGroups) == set(['Var'])
#     assert getIncludingGroups('Hum', testGroups) == set(('Hum', 'sensors', 'others'))


# def testCplxInclusion():
#     testGroups = dict(sensors=['Temp', 'Hum'], others=['Hum'], mixed=['others'])
#     # A bit harder ... let's start with only child/parents relations
#     # assert getIncludingGroups('Hum', testGroups) == set(['sensors', 'others', 'mixed', 'Hum'])


