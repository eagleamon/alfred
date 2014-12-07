defaultConfig = {
    "living.lights": [
        "living.light.right",
        "living.light.left"
    ]
}

def setup(alfred):
    config = alfred.get_config(__name__)

    for group in config:
        alfred.bus.on('commands/#', on_commands)

def on_commands(topic, msg):
    config = alfred.get_config(__name__)
    groupName = topic.split('/')[1]

    if groupName in config:
        for item in config[groupName]:
            alfred.send_command(item, msg)

    # TODO: regex and not only item name :)
