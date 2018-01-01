import sys
from functools import wraps

_caches = []


class _Cache(dict):
	"""A dict() subclass that appends a self-reference to _caches"""
	def __init__(self, *args, **kwargs):
		super(_Cache, self).__init__(*args, **kwargs)
		_caches.append(self)


def cache(*keys):
	"""cache decorator

	Caches input and output of a function. If arguments are passed to
	the decorator, take those as key for the cache. Otherwise use the
	function arguments and sys.argv as key.

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


def clearAllCaches():
	for cache in _caches:
		cache.clear()
