from fabric.api import local, run, cd, sudo, put
from fabric.decorators import hosts

import os


def clean():
    local('find . -name "*.pyc" -delete')
    local('rm -rf alfred.log dist build *.egg-info')


# TODO: change to package
@hosts('pi@raspbmc')
def install():
    run('test -e alfred || git clone https://github.com/eagleamon/alfred.git')
    with(cd('alfred')):
        sudo('python setup.py develop')
        sudo('pip install -r requirements.txt')


def build():
    clean()
    local('python setup.py sdist')


def deps():
    print "Todo"


#@hosts('hal', 'pi@raspbmc')
def publish():
    f = os.listdir('dist')[-1]
    put('dist/%s' % f, '/tmp/%s' % f)
    sudo('pip install --no-deps -U /tmp/%s' % f)
    sudo('touch /var/log/alfred.log')
    sudo('restart alfred')
    sudo('uname -a')


def run(where='test'):
    if where == 'test':
        local('python -m alfred --db_host hal --db_name test -d')
    elif where == 'prod':
        local('python -m alfred --db_host hal -d')
    elif where == 'work':
        local('python -m alfred --db_host lutvms017 --db_name test -d')


def test(toTest=''):
    " Passes argument like -> fab test:tests/items.py "
    local('nosetests --with-watch %s' % toTest)
