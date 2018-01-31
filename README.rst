CheckPy
=======

A Python tool for running tests on Python source files. Intended to be
used by students whom are taking courses in the `Minor
Programming <http://www.mprog.nl/>`__ at the
`UvA <http://www.uva.nl/>`__.

`CheckPy docs <http://checkpy.readthedocs.io/>`__

Installation
------------

::

     pip install checkpy

Besides installing checkPy, you might want to download some tests along with it. Simply run checkPy with the ``-d`` arg as follows:

::

    checkpy -d YOUR_GITHUB_TESTS_URL

Usage
-----

::

    usage: __main__.py [-h] [-module MODULE] [-download GITHUBLINK] [-update]
                       [-list] [-clean] [-dev]
                       [file]

    checkPy: a python testing framework for education. You are running Python
    version 3.6.2 and checkpy version 0.3.21.

    positional arguments:
      file                  name of file to be tested

    optional arguments:
      -h, --help            show this help message and exit
      -module MODULE        provide a module name or path to run all tests from
                            the module, or target a module for a specific test
      -download GITHUBLINK  download tests from a Github repository and exit
      -update               update all downloaded tests and exit
      -list                 list all download locations and exit
      -clean                remove all tests from the tests folder and exit
      --dev                 get extra information to support the development of
                            tests

To simply test a single file, call:

::

     checkpy YOUR_FILE_NAME

If you are unsure whether multiple tests exist with the same name, you can target a specific test by specifying its module:

::

     checkpy YOUR_FILE_NAME -m YOUR_MODULE_NAME

If you want to test all files from a module within your current working directory, then this is the command for you:

::

     checkpy -m YOUR_MODULE_NAME

Features
--------

-  Support for ordering of tests
-  Execution of tests can be made dependable on the outcome of other
   tests
-  The test designer need not concern herself with exception handling
   and printing
-  The full scope of Python is available when designing tests
-  Full control over displayed information
-  Support for importing modules without executing scripts that are not
   wrapped by ``if __name__ == "__main__"``
-  Support for overriding functions from imports in order to for
   instance prevent blocking function calls
-  Support for grouping tests in modules,
   allowing the user to target tests from a specific module or run all tests in a module with a single command.
-  No infinite loops, automatically kills tests after a user defined timeout.
-  Tests are kept up to date as checkpy will periodically look for updates from the downloaded test repos.


An example
----------

Tests in checkPy are collections of abstract methods that you as a test
designer need to implement. A test may look something like the
following:

.. code-block:: python

    0| import checkpy.test as t
    1| import checkpy.assertlib as assertlib
    2| import checkpy.lib as lib
    3| @t.failed(exact)
    4| @t.test(1)
    5| def contains(test):
    6|     test.test = lambda : assertlib.contains(lib.outputOf(test.fileName), "100")
    7|     test.description = lambda : "contains 100 in the output"
    8|     test.fail = lambda info : "the correct answer (100) cannot be found in the output"

From top to bottom:

-  The decorator ``failed`` on line 3 defines a precondition. The test
   ``exact`` must have failed for the following tests to execute.
-  The decorator ``test`` on line 4 prescribes that the following method
   creates a test with order number ``1``. Tests are executed in order,
   lowest first.
-  The method definition on line 5 describes the name of the test
   (``contains``), and takes in an instance of ``Test`` found in
   ``test.py``. This instance is provided by the decorator ``test`` on
   the previous line.
-  On line 6 the ``test`` method is bound to a lambda which describes
   the test that is to be executed. In this case asserting that the
   print output of ``test.fileName`` contains the number ``100``.
   ``test.fileName`` refers to the to be tested
   source file. Besides resulting in a boolean indicating passing or
   failing the test, the test method may also return a message. This
   message can be used in other methods to provide valuable information
   to the user. In this case however, no message is provided.
-  On line 7 the ``description`` method is bound to a lambda which when
   called produces a string message describing the intent of the test.
-  On line 8 the ``fail`` method is bound to a lambda. This method is
   used to provide information that should be shown to the user in case
   the test fails. The method takes in a
   message (``info``) which comes from the second returned value of the
   ``test`` method. This message can be used to relay information found during
   execution of the test to the user.

Writing tests
-------------

Test methods are discovered in checkPy by filename. If you want to test
a file called ``foo.py``, the corresponding test must be named ``fooTest.py``.
checkPy assumes that all methods in the test file are tests, as such one
should not use the ``from ... import ...`` statement when importing
modules.

A test minimally consists of the following:

.. code-block:: python

    import checkpy.test as t
    import checkpy.assertlib as assertlib
    import checkpy.lib as lib
    @t.test(0)
    def someTest(test):
      test.test = lambda : False
      test.description = lambda : "some description"

Here the method ``someTest`` is marked as test by the decorator
``test``. The abstract methods ``test`` and ``description`` are
implemented as these are the only methods that necessarily require
implementation. For more information on tests and their abstract methods
you should refer to ``test.py``. Note that besides defining the ``Test``
class and its abstract methods, ``test.py`` also provides several
decorators for introducing test dependencies such as ``failed``.

When providing a concrete implementation for the test method one should
take a closer look at ``lib.py`` and ``assertlib.py``. ``lib.py``
provides a collection of useful functions to help implement tests. Most
notably ``getFunction`` and ``outputOf``. These provide the tester with
a function from the source file and the complete print output
respectively. Calling ``getFunction`` has checkpy import the to be
tested code and retrieves only said function from the resulting module.
``assertlib.py`` provides a collection of assertions that one may find useful when
implementing tests.

For inspiration inspect some existing collections like the tests for `progNS <https://github.com/Jelleas/progNS2016Tests>`__, `progIK <https://github.com/Jelleas/progIKTests>`__, `Semester of Code <https://github.com/Jelleas/progbeta2017tests>`__ or `progBG <https://github.com/Jelleas/progBG2017Tests>`__.


Distributing tests
------------------

CheckPy can download tests directly from Github repos.
The requirement is that a folder called ``tests`` exists within the repo that contains only tests and folders (which checkpy treats as modules).
There must also be at least one release in the Github repo. Checkpy will automatically target the latest release.
Simply call checkPy with the optional ``-d`` argument and pass your github repo url.
Tests will then be automatically downloaded and installed.


Testing CheckPy
---------------

::

    python2 run_tests.py
    python3 run_tests.py
