import os
import pathlib
from .downloader import download, update

file: pathlib.Path = None

def testModule(moduleName, debugMode = False, silentMode = False):
	"""
	Test all files from module
	"""
	from . import caches
	caches.clearAllCaches()
	from . import tester
	from . import downloader
	downloader.updateSilently()
	results = tester.testModule(moduleName, debugMode = debugMode, silentMode = silentMode)
	try:
		if __IPYTHON__:
			import matplotlib.pyplot
			matplotlib.pyplot.close("all")
	except:
		pass
	return results

def test(fileName, debugMode = False, silentMode = False):
	"""
	Run tests for a single file
	"""
	from . import caches
	caches.clearAllCaches()
	from . import tester
	from . import downloader
	downloader.updateSilently()
	result = tester.test(fileName, debugMode = debugMode, silentMode = silentMode)
	try:
		if __IPYTHON__:
			import matplotlib.pyplot
			matplotlib.pyplot.close("all")
	except:
		pass
	return result
