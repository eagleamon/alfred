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


def run(where='test', client='dist'):
    client = '--client-path ./client/app' if client == 'app' else ''
    cmd = 'python -m alfred -d %s --db_host ' % client

    if where == 'test':
        local(cmd + 'hal --db_name test')
    elif where == 'prod':
        local(cmd + 'hal')
    elif where == 'work':
        local(cmd + 'lutvms017 --db_name test')


def test(toTest=''):
    " Passes argument like -> fab test:tests/items.py "
    local('nosetests --with-watch %s' % toTest)
