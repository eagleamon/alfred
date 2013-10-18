from fabric.api import local

def clean():
	local('find . -name "*.pyc" -delete')