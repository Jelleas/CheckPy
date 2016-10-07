_caches = []

class Cache(object):
	def __init__(self):
		self._cache = {}
		_caches.append(self)

	def put(self, key, value):
		self._cache[key] = value

	def get(self, key):
		return self._cache.get(key, None)
		
	def delete(self, key):
		if key not in self._cache:
			return False
		del self._cache[key]
		return True

	def clear(self):
		self._cache.clear()

def clearAllCaches():
	for cache in _caches:
		cache.clear()