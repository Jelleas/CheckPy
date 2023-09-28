## checkpy

A Python tool for running tests on Python source files. Intended to be
used by students whom are taking courses from [Programming Lab at the UvA](https://www.proglab.nl).

Check out <https://github.com/spcourse/tests> for examples of tests.

### Installation

    pip install checkpy

To download tests, run checkPy with ``-d`` as follows:

    checkpy -d YOUR_GITHUB_TESTS_URL

For instance:

    checkpy -d spcourse/tests

Here spcourse/tests points to <https://github.com/spcourse/tests>. You can also use the full url. This tests repository contains a test for `hello.py`. Here is how to run it:

    $ echo 'print("hello world")' > hello.py
    $ checkpy hello
    Testing: hello.py
    :( prints "Hello, world!"
        assert 'hello world\n' == 'Hello, world!\n'
        - hello world
        ? ^
        + Hello, world!
        ? ^    +      +
    :) prints exactly 1 line of output

### Usage

    usage: checkpy [-h] [-module MODULE] [-download GITHUBLINK] [-register LOCALLINK] [-update] [-list] [-clean] [--dev]
                    [--silent] [--json] [--gh-auth GH_AUTH]
                    [files ...]

    checkPy: a python testing framework for education. You are running Python version 3.10.6 and checkpy version 2.0.0.

    positional arguments:
    files                 names of files to be tested

    options:
    -h, --help            show this help message and exit
    -module MODULE        provide a module name or path to run all tests from the module, or target a module for a
                            specific test
    -download GITHUBLINK  download tests from a Github repository and exit
    -register LOCALLINK   register a local folder that contains tests and exit
    -update               update all downloaded tests and exit
    -list                 list all download locations and exit
    -clean                remove all tests from the tests folder and exit
    --dev                 get extra information to support the development of tests
    --silent              do not print test results to stdout
    --json                return output as json, implies silent
    --gh-auth GH_AUTH     username:personal_access_token for authentication with GitHub. Only used to increase  GitHub api's rate limit.

To test a single file call:

     checkpy YOUR_FILE_NAME

### An example

Tests in checkpy are functions with assertions. For instance:

```Py
from checkpy import *

@test()
def printsHello():
    """prints Hello, world!"""
    assert outputOf() == "Hello, world!\n"
```

checkpy's `test` decorator marks the function below as a test. The docstring is a short description of the test for the student. This test does just one thing, assert that the output of the student's code matches the expected output exactly. checkpy leverages pytest's assertion rewriting to autmatically create assertion messages. For instance, a student might see the following when running this test:

    $ checkpy hello
    Testing: hello.py
    :( prints Hello, world!
        assert 'hello world\n' == 'Hello, world!\n'
        - hello world
        ? ^
        + Hello, world!
        ? ^    +      +

### Writing tests

Tests are discovered by filename. If you want to test a file called ``hello.py``, the corresponding test must be named ``helloTest.py``. These tests must be placed in a folder called `tests`. For instance: `tests/helloTest.py`. Tests are distributed via GitHub repositories, but for development purposes tests can also be registered locally via the `-r` flag. For instance:

    mkdir tests
    touch tests/helloTest.py
    checkpy -r tests/helloTest.py

Once registered, checkpy will start looking in that directory for tests. Now we need a test. A test minimally consists of the following:

```Py
from checkpy import *

@test()
def printsHello():
    """prints Hello, world!"""
    assert outputOf() == "Hello, world!\n"
```

A function marked as a test through checkpy's test decorator. The docstring is a short, generally one-line, description of the test for the student. Then at least one assert.

> Quick tip, use only binary expressions in assertions and keep them relatively simple for students to understand. If a binary expression is not possible, or you do not want to spoil the output, raise your own assertionError instead: ```raise AssertionError("Your program did not output the answer to the ultimate question of life, the universe, and everything")```.

While developing, you can run checkpy with the `--dev` flag to get verbose error messages and full tracebacks. So here we might do:

    $ checkpy --dev hello                   
    Testing: hello.py
    :( prints "Hello, world!"
    assert 'hello world\n' == 'Hello, world!\n'
        - hello world
        ? ^
        + Hello, world!
        ? ^    +      +
    :) prints exactly 1 line of output

Check out <https://github.com/spcourse/tests> for many examples of checkpy tests.

### Short examples

#### Dependencies between tests

```Py
@test()
def exactHello():
    """prints \"Hello, world!\""""
    assert outputOf() == "Hello, world!\n"

@failed(exactHello)
def oneLine():
    """prints exactly 1 line of output"""
    assert outputOf().count("\n") == 1

@passed(exactHello)
def allGood():
    """Good job, everything is correct! You are ready to hand in."""
```

#### Test functions

```Py
@test()
def testSquare():
    """square(2) returns 4"""
    assert getFunction("square")(4) == 4
```

#### Give hints

```Py
@test()
def testSquare():
    """square(2) returns 4"""
    assert getFunction("square")(4) == 4, "did you remember to round your output?"
```

#### Handle randomness with pytest's `approx`

```Py
@test()
def testThrowDice():
    """throw() returns 7 on average"""
    throw = getFunction("throw")
    avg = sum(throw() for i in range(1000)) / 1000 
    assert avg == approx(7, abs=0.5)
```

#### Ban language constructs

```Py
import ast

@test()
def testSquare():
    """square(2) returns 4"""
    assert ast.While not in static.AbstractSyntaxTree()
    assert getFunction("square")(4) == 4
```

#### Check types

```Py
@test()
def testFibonacci():
    """fibonacci(10) returns the first ten fibonacci numbers"""
    fibonacci = getFunction("fibonacci")
    assert fibonacci(10) == Type(list[int])
    assert fibonacci(10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

#### Configure which files should be present

> Calling `only`, `include`, `exclude`, `require` or `download` has checkpy create a temporary directory to which the specified files are copied/downloaded. The tests then run in that directory.

```Py
only("sentiment.py")
download("pos_words.txt", "https://github.com/spcourse/text/raw/main/en/sentiment/pos_words.txt")
download("neg_words.txt", "https://github.com/spcourse/text/raw/main/en/sentiment/neg_words.txt")

@test()
def testPositiveSentiment():
    """recognises a positive sentence"""
    ...
```

#### Change the timeout

```Py
@test(timeout=60)
def exactHello():
    """prints \"Hello, world!\""""
    assert outputOf() == "Hello, world!\n"
```

#### Short declarative tests

> This is a new style of tests for simple repetative use cases. Be sure to check out <https://github.com/spcourse/tests> for many more examples. For example [sentimentTest.py](https://github.com/spcourse/tests/blob/676cf5f0d2b0fbc82c7580a76b4359af273b0ca7/tests/text/sentimentTest.py)

```Py
correctForPos = test()(declarative
    .function("sentiment_of_text")
    .params("text")
    .returnType(int)
    .call("Coronet has the best lines of all day cruisers.")
    .returns(1)
    .description("recognises a positive sentence")
)
```

### Distributing tests

checkpy downloads tests directly from Github repos. The requirement is that a folder called ``tests`` exists within the repo that contains only tests and folders (which checkpy treats as modules). There must also be at least one release in the Github repo. checkpy will automatically target the latest release. To download tests call checkpy with the optional ``-d`` argument and pass your github repo url. checkpy will automatically keep tests up to date by checking for any new releases on GitHub.


### Testing checkpy

    python3 run_tests.py
