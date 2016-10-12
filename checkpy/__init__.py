def testModule(moduleName):
	"""
	Test all files from module
	"""
	import caches
	caches.clearAllCaches()
	import tester
	tester.testModule(moduleName)
	try:
		if __IPYTHON__:
			import matplotlib.pyplot
			matplotlib.pyplot.close("all")
	except:
		pass

def test(fileName):
	"""
	Run tests for a single file
	"""
	import caches
	caches.clearAllCaches()
	import tester
	tester.test(fileName)
	try:
		if __IPYTHON__:
			import matplotlib.pyplot
			matplotlib.pyplot.close("all")
	except:
		pass

from downloader import download