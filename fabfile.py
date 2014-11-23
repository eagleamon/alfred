from fabric.api import cd, sudo, put, env, hosts
from fabric.context_managers import prefix, shell_env
from contextlib import contextmanager

import os

env.pythonpath = '/Users/joseph/.virtualenvs/alfred/lib/python2.7/site-packages/'
env.hosts = ['hal', 'pi@raspbmc']


@contextmanager
def source_venv():
    with prefix('source ' + '/Users/joseph/.virtualenvs/alfred/bin/activate'):
        yield

def clean():
    local('find . -name "*.pyc" -delete')
    local('rm -rf alfred.log dist build *.egg-info')


# TODO: change to package
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

@hosts('localhost')
def run(env='dev'):
    if env == 'dev':
        client = "--client-path ./client/app"

    cmd = 'python -m alfred -d --db-host hal %s'
    # local(cmd % client)
    os.system(cmd % client) # Otherwise when quitting, background process may stay alive


def test(toTest=''):
    " Chose tests like -> fab test:tests/items.py "
    with source_venv(), shell_env(PYTHONPATH=env.pythonpath):
        local('nosetests %s --with-watch -v' % toTest)
