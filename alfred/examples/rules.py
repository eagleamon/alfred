from alfred.rules.commands import *

if (Temp.value > 20)
    Chaudière.state=off

if (g('Temp').value > 20)
    g('Chaudiere').state = false
    g('chaudiere').statte(false)