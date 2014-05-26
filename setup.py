import os
from setuptools import setup, find_packages
from pip.req import parse_requirements as pr

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def reqs():
    return [str(i.req) for i in pr(os.path.join(os.path.dirname(__file__), 'requirements.txt'))]

import alfred

setup(
    name = "alfred",
    version = alfred.version,
    author = "Joseph Piron",
    author_email = "joseph.piron@gmail.com",
    description = ("An interpretation of OpenHab, Domogik, and other great domotic projects."),
    license = "BSD",
    keywords = "domotic, openhab, domogik, mqtt, event, bus",
    url = "http://github.com/eagleamon/alfred",
    packages=find_packages(),
    package_data={'alfred/webServer': ['alfred/webServer/webClient']},
    install_requires=reqs(),
    long_description=read('README.md'),
    data_files=[
        ('/etc/init', ['data/alfred.conf'])
    ],
    include_package_data=True,
    classifiers=[
        "Development Status :: 2 - PreAlpha",
        "Topic :: Home Automation",
        "License :: OSI Approved :: BSD License",
    ],
)
