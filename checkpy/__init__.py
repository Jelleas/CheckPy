def testModule(moduleName):
	"""
	Test all files from module
	"""
	import caches
	caches.clearAllCaches()
	import tester
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
	import caches
	caches.clearAllCaches()
	import tester
	result = tester.test(fileName)
	try:
		if __IPYTHON__:
			import matplotlib.pyplot
			matplotlib.pyplot.close("all")
	except:
		pass
	return result

from downloader import download, update