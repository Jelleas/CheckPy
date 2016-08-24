# CheckPy
A Python tool for running tests on Python source files. 
Intended to be used by students whom are taking courses in the [Minor Programming](http://www.mprog.nl/) at the [UvA](http://www.uva.nl/).

## Usage
`python check <filename>`

Requires python 2.7

## Features

* Support for ordering of tests
* Execution of tests can be made dependable on the outcome of other tests
* The test designer need not concern herself with exception handling and printing
* The full scope of Python is available when designing tests
* Full control over displayed information
* Support for importing modules without executing scripts that are not wrapped by `if __name__ == "__main__"`
* Support for overriding functions from imports in order to for instance prevent blocking function calls

## An example
Tests in checkPy are collections of abstract methods that you as a test designer need to implement. A test may look something like the following:

```
0| @t.failed(exact)
1| @t.test(1)
2| def contains(test):
3|     test.test = lambda : assertlib.contains(lib.outputOf(_fileName), "100")
4|     test.description = lambda : "contains 100 in the output"
5|     test.success = lambda info : "the correct answer (100) can be found in the output"
6|     test.fail = lambda info : "the correct answer (100) cannot be found in the output"
```

From top to bottom:

* The decorator `failed` on line 0 defines a precondition. The test `exact` must have failed for the following tests to execute.
* The decorator `test` on line 1 prescribes that the following method creates a test with order number `1`. Tests are executed in order, lowest first.
* The method definition on line 2 describes the name of the test (`contains`), and takes in an instance of `Test` found in `test.py`. This instance is provided by the decorator `test` on the previous line.
* On line 3 the `test` method is bound to a lambda which describes the test that is to be executed. In this case asserting that the print output of `_fileName` contains the number `100`. `_fileName` is a magic variable that refers to the to be tested source file. Besides resulting in a boolean indicating passing or failing the test, the test method also returns a message. This message can be used in other methods to provide valuable information to the user. In this case however, it is left blank (`""`)
* On line 4 the `description` method is bound to a lambda which when called produces a string message describing the intent of the test.
* On line 5 the `success` method is bound to a lambda taking in a message (`info`) and returning a string which describes the information that should be shown to the user in case the test passes. The argument `info` comes from the second returned value of the `test` method, and can be used to relay information found during execution of the test to the user.
* On line 6 the `fail` method is bound to a lambda. This method is used to describe information that should be shown to the user in case the test fails. Its workings are the same as the `success` method on the previous line.

## Writing tests

Test methods are discovered in checkPy by filename.
If one wants to test a file `foo.py`, the corresponding test must be named `fooTest.py`. 
checkPy assumes that all methods in the test file are tests, as such one should not use the `from ... import ...` statement when importing modules.

A test minimally consists of the following:

```
import test as t
@t.test(0)
def someTest(test):
  test.test = lambda : False
  test.description = lambda : "some description"
```

Here the method `someTest` is marked as test by the decorator `test`. 
The abstract methods `test` and `description` are implemented as these are the only methods that necessarily require implementation. 
For more information on tests and their abstract methods you should refer to `test.py`. 
Note that besides defining the `Test` class and its abstract methods, `test.py` also provides several decorators for introducing test dependencies such as `failed`.

When providing a concrete implementation for the test method one should take a closer look at `lib.py` and `assertlib.py`.
`lib.py` provides a collection of useful functions to help implement tests. 
Most notably `getFunction` and `outputOf`. 
These provide the tester with a function from the source file and the complete print output respectively. 
Calling `getFunction` makes checkPy evaluate only import statements and code inside definitions of the to be tested file.
Effectively all other parts of code are wrapped by `if __name__ == "__main__"` and thus ignored.
`assertlib.py` provides a collection of assertions that one may find usefull when implementing tests.

For inspiration inspect the tests that are included with checkPy.
