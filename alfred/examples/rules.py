from alfred.commands import *

if (Temp.value > 20)
    Chaudière.state=off

if (g('Temp').value > 20)
    g('Chaudiere').state = false
    g('chaudiere').statte(false)



providers in et out

items, state