class Test(object):
    def run(self, fileName):
        try:
            hasPassed, info = self.test(fileName)
        except Exception as e:
            return TestResult(False, self.description(), self.exception(e))
        if hasPassed:
            return TestResult(True, self.description(), self.success(info))
        return TestResult(False, self.description(), self.fail(info))
    
    @staticmethod
    def test(fileName):
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

def test(testCreator):
    def testWrapper():
        test = Test()
        testCreator(test)
        return test
    return testWrapper

def failed(*precondTestCreators):
    def failedDecorator(testCreator):
        def testWrapper():
            test = testCreator()
            run = test.run
            test.run = lambda fileName : run(fileName) if not any(t().run(fileName).hasPassed for t in precondTestCreators) else None
            return test
        return testWrapper
    return failedDecorator

def passed(*precondTestCreators):
    def passedDecorator(testCreator):
        def testWrapper():
            test = testCreator()
            run = test.run
            test.run = lambda fileName : run(fileName) if all(t().run(fileName).hasPassed for t in precondTestCreators) else None
            return test
        return testWrapper
    return passedDecorator