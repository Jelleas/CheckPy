import os
from .downloader import download, update

def testModule(moduleName):
	"""
	Test all files from module
	"""
	from . import caches
	caches.clearAllCaches()
	from . import tester
	from . import downloader
	downloader.updateSilently()
	results = tester.testModule(moduleName)
	try:
		if __IPYTHON__:
			import matplotlib.pyplot
			matplotlib.pyplot.close("all")
	except:
		pass
	return results

def test(fileName):
	"""
	Run tests for a single file
	"""
	from . import caches
	caches.clearAllCaches()
	from . import tester
	from . import downloader
	downloader.updateSilently()
	result = tester.test(fileName)
	try:
		if __IPYTHON__:
			import matplotlib.pyplot
			matplotlib.pyplot.close("all")
	except:
		pass
	return result
