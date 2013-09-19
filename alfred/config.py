"""
Seems to be better than using singletons, so let's try it :)

Db has to be setup first to be used
"""

inTest = False
db = None

def get(name):
	if inTest != True:
		assert db != None, "db is not setup"
	return db.config.find_one().get(name)