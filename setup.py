import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "alfred",
    version = "0.0.1",
    author = "Joseph Piron",
    author_email = "joseph.piron@gmail.com",
    description = ("An interpretation of OpenHab, Domogik, and other great domotic projects."),
    license = "BSD",
    keywords = "domotic, openhab, domogik, mqtt, event, bus",
    url = "http://github.com/eagleamon/alfred",
    packages=find_packages(),
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 2 - PreAlpha",
       	"Topic :: Home Automation",
        "License :: OSI Approved :: BSD License",
    ],
)