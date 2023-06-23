import sys
from functools import wraps

_caches = []

class _Cache(dict):
	"""A dict() subclass that appends a self-reference to _caches"""
	def __init__(self, *args, **kwargs):
		super(_Cache, self).__init__(*args, **kwargs)
		_caches.append(self)

_testCache = _Cache()


def cache(*keys):
	"""cache decorator

	Caches input and output of a function. If arguments are passed to
	the decorator, take those as key for the cache. Otherwise use the
	function arguments and sys.argv as key.

	sys.argv is used here because of user-written code like this:

	import sys
	my_variable = sys.argv[1]
	def my_function():
		print(my_variable)

	Depending on the state of sys.argv during execution of the module,
	the outcome of my_function() changes.
	"""
	def cacheWrapper(func):
		localCache = _Cache()

		@wraps(func)
		def cachedFuncWrapper(*args, **kwargs):
			if keys:
				key = str(keys)
			else:
				key = str(args) + str(kwargs) + str(sys.argv)
			if key not in localCache:
				localCache[key] = func(*args, **kwargs)
			return localCache[key]
		return cachedFuncWrapper

	return cacheWrapper


def cacheTestFunction(testFunction):
	@wraps(testFunction)
	def cachedTestFunction(*args, **kwargs):
		key = testFunction.__name__
		if key not in _testCache:
			_testCache[key] = testFunction(*args, **kwargs)
		return _testCache[key]
	return cachedTestFunction


def getCachedTest(testFunction):
	key = testFunction.__name__
	return _testCache[key]


def clearAllCaches():
	for cache in _caches:
		cache.clear()
	_testCache.clear()
