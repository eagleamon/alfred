from random import random, choice


defaultConfig = {
    "main": {
        "refresh": 5
    },
    "second": {
        "refresh": 10
    }
}

def setup(alfred):
    config = alfred.get_config(__name__)
    for loop in config:
        alfred.schedule(
            __file__, update, loop, seconds=range(0, 61, config[loop]['refresh']))

def stop(alfred):
    alfred.deschedule(__file__)


def update(alfred, data):
    for item in alfred.activeItems['random']:
        if item.binding.split(':')[1] == data:
            if item.type == 'number':
                item.value = random()
            elif item.type == 'switch':
                item.value = choice((False, True))
            elif item.type == 'string':
                item.value = choice(("That's it", "Let's do it", "A while ago.."))

