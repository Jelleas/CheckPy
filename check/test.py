_cachedTests = {}

class Test(object):
    def __init__(self, priority):
        self._priority = priority
        self._cachedResult = None

    def __cmp__(self, other):
        return cmp(self._priority, other._priority)

    def run(self):
        if self._cachedResult:
            return self._cachedResult
        try:
            hasPassed, info = self.test()
        except Exception as e:
            self._cachedResult = TestResult(False, self.description(), self.exception(e))
            return self._cachedResult
        self._cachedResult = TestResult(hasPassed, self.description(), self.success(info) if hasPassed else self.fail(info))
        return self._cachedResult
    
    @staticmethod
    def test():
        raise NotImplementedError()
    
    @staticmethod
    def description():
        raise NotImplementedError()
    
    @staticmethod
    def success(info):
        return ""
    
    @staticmethod    
    def fail(info):
        return ""
        
    @staticmethod
    def exception(info):
        return "an exception occured: " + str(info)
        
        
class TestResult(object):
    def __init__(self, hasPassed, description, message):
        self._hasPassed = hasPassed
        self._description = description
        self._message = message
        
    @property
    def description(self):
        return self._description
    
    @property
    def message(self):
        return self._message
        
    @property
    def hasPassed(self):
        return self._hasPassed


def test(priority):
    def testDecorator(testCreator):
        def testWrapper():
            if testCreator in _cachedTests:
                return _cachedTests[testCreator]
            test = Test(priority)
            testCreator(test)
            _cachedTests[testCreator] = test
            return test
        return testWrapper
    return testDecorator


def failed(*precondTestCreators):
    def failedDecorator(testCreator):
        def testWrapper():
            test = testCreator()
            run = test.run
            test.run = lambda : run() if not any(t().run().hasPassed for t in precondTestCreators) else None
            return test
        return testWrapper
    return failedDecorator


def passed(*precondTestCreators):
    def passedDecorator(testCreator):
        def testWrapper():
            test = testCreator()
            run = test.run
            test.run = lambda : run() if all(t().run().hasPassed for t in precondTestCreators) else None
            return test
        return testWrapper
    return passedDecorator