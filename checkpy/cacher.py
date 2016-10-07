_caches = []

class Cache(object):
	def __init__(self):
		self._caches = {}
		_caches.append(self)

	def put(self, identifier, key, value):
		if identifier not in self._caches:
			self._caches[identifier] = {}

		self._caches[identifier][key] = value

	def get(self, identifier, key):
		return self._caches.get(identifier, {}).get(key, None) 

	def delete(self, identifier, key):
		if identifier not in self._caches:
			return False
		if key not in self._caches[identifier]:
			return False
		del self._caches[identifier][key]
		return True

	def clear(self):
		self._caches.clear()

def clearAllCaches():
	for cache in _caches:
		cache.clear()