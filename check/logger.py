import assertlib

class _Logger(object):
	def __init__(self):
		self._items = set()

	def log(self, item):
		self._items.add(item)

	@property
	def items(self):
		return self._items

_logger = _Logger()

def logBuiltinDatastructures(mod, datastructures):
	for ds in datastructures:
		class Proxy(ds):
			_ds = ds
			def __init__(self, *args, **kwargs):
				_logger.log(self._ds)		
				self._ds.__init__(self, *args, **kwargs)

			def __getitem__(self, arg):
				_logger.log("hi")
				self._ds.__getitem__(self, arg)
		mod.__builtins__[ds.__name__] = Proxy

logBuiltinDatastructures(assertlib, [list, tuple, dict])

type([]).__getitem__ = lambda arg : 0

assertlib.test()
print _logger.items