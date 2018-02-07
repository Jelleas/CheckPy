Introduction to CheckPy
===================================

.. toctree::
     :maxdepth: 2
     :caption: Contents:

Installation
-------------------

::

    pip install checkpy


Writing and running your first test
-----------------------------------

First create a new directory to store your tests somewhere on your computer.
Then navigate to that directory, and create a new file called ``helloTest.py``.
CheckPy discovers tests for a particular source file (i.e. ``hello.py``) by looking
for a test file starting with a corresponding name (``hello``) and ending with ``test.py``.
So CheckPy uses ``helloTest.py`` to test ``hello.py``.

Now open up ``helloTest.py`` and insert the following code:

.. code-block:: python

    import checkpy.tests as t
    import checkpy.lib as lib
    import checkpy.assertlib as asserts

    @t.test(0)
    def exactlyHelloWorld(test):
        def testMethod():
            output = lib.outputOf(test.fileName)
            return asserts.exact(output.strip(), "Hello, world!")

        test.test = testMethod
        test.description = lambda : "prints exactly: Hello, world!"

Next, create a file called ``hello.py`` somewhere on your computer. Insert the
following snippet of code in ``hello.py``:

.. code-block:: python

    print("Hello, world!")

Now there's only one thing left to do. We need to tell CheckPy where the tests are
located. You can do this by calling CheckPy with the `-register` flag and by providing an
absolute path to the directory ``helloTest.py`` is located in. Say ``helloTest.py``
is located in ``\Users\foo\bar\tests\`` then call CheckPy like so:

::

    checkpy -register \Users\foo\bar\tests\

Alright, we're there. We got a test (``helloTest.py``), a Python file we want to test (``hello.py``),
and we've told CheckPy where to look for tests. Now navigate over to the
directory that contains ``hello.py`` and call CheckPy as follows:

::

    checkpy hello


How to write tests in CheckPy
-----------------------------

Tests in CheckPy are instances of ``checkpy.tests.Test``. These ``Test`` instances have several
abstract methods that you can implement or rather, overwrite by binding a new method.
These methods are executed when CheckPy runs a test. For instance you have the
``description`` method which is called to produce a description for the test, the ``timeout``
method which is called to determine the maximum alotted time for this test, and
ofcourse the ``test`` method which is called to actually perform the test.

Lets start with the necessities. CheckPy requires you to overwrite two methods from every
``Test`` instance. These methods are ``test`` and ``description``. The ``description`` method
should produce the description, that can be just a string, for the user to see. In our
hello-world example we used this ``description`` method:

.. code-block:: python

    test.description = lambda : "prints exactly: Hello, world!"

Depending on whether the test fails or passes, the user sees this string in red or green
respectively. The other method we have to overwrite, the ``test`` method, should return
True of False depending on whether the tests passes or fails. You are free to implement
this method in any which way you want. CheckPy just offers some useful tools to make
your testing life easier. Again, looking back at our hello-world example, we used this
``test`` method:

.. code-block:: python

    def testMethod():
        output = lib.outputOf(test.fileName)
        return asserts.exact(output.strip(), "Hello, world!")

    test.test = testMethod

So what's going on here? Python doesn't support multi statement lambda functions. This means that
if you want to use multiple statements, you have to resort back to named functions, i.e.
``testMethod()``, and then bind this named function to the respective method of the ``Test``
instance. You can put the above test method in a single statement lambda function, but
readability will suffer from it. Especially once we move on to some more complex test methods.

Now there are just 2 lines of code in this ``testMethod``. First we take the output of
something called ``test.fileName``. ``test.fileName`` just refers to the name of the file
the user wants to test, CheckPy will automatically set this for you. ``lib.outputOf`` is
a function that gives you all the print-output of a python file. Thus what this line of code
does is simply run the file that the user wants to test, and then return the print output as
a string.

The line ``return asserts.exact(output.strip(), "Hello, world!")`` is equivalent to
``return output.strip() == "Hello, world!"``. The ``checkpy.assertlib`` module, that is renamed
to ``asserts`` here, simply offers a collection of functions to perform assertions. These
functions do nothing more than return ``True`` or ``False``.
