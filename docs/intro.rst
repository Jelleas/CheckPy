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
            output = lib.outputOf(
                test.fileName,
                overwriteAttributes = [("__name__", "__main__")]
            )
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
