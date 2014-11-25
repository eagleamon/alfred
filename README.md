Yep, it's ongoing ! :)

The idea is to create a system with a central .. something .. that collects values for every items by the mean of a general communication bus (networked -> MQTT) and thus allowing different instances to run on several machines while accessing the information from everywhere

A bit more: everything should be a module that each instance of alfred could instanciate or not to provide functionalities like bindings, xmpp module, webinterface etc

For the webserver, there should be module as well, for ex a module to interrogate database of movies in xbmc :)

## Architecture
- python -m alfred : starts the process
-

## Alfred
- Handles manager, signal heartbeat

## Manager
- handles items, plugins

## Config
- Each module has its own config section in general host config
{
name: 'macbook',
http:{},
boxcar:{},
mail:{},..
}
- config possible from file or from db
    - db handy to share across multiple instances
    - config easier for simple installation or debugging/development


## Items
- each alfred instances see all items but handles only defined ones
- when a property changed, -> mqtt messages, item owner changes and item saves in db
- items have a name, some bindings and some attributes (easier than defined )

## Topics

Description of all topics used here:
- config
- commands
- heartbeats
- items
- logs

## Cameras

## Plugins
- offer services (action to call)
- refresh items based on time (one timer for all or one thread for each ?)
- Must be un/installed/started/stopped through the instance web interface, not by messaging like items
- Exposed function takes an alfred instance as first argument, and whatever after

## Groups
-  are a plugin
- handles publishing of value on mqtt group topics based on message received from items
