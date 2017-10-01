def testModule(moduleName):
	"""
	Test all files from module
	"""
	import checkpy.caches as caches
	caches.clearAllCaches()
	import checkpy.tester as tester
	import checkpy.downloader as downloader
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
	import checkpy.caches as caches
	caches.clearAllCaches()
	import checkpy.tester as tester
	import checkpy.downloader as downloader
	downloader.updateSilently()
	result = tester.test(fileName)
	try:
		if __IPYTHON__:
			import matplotlib.pyplot
			matplotlib.pyplot.close("all")
	except:
		pass
	return result

from checkpy.downloader import download, update