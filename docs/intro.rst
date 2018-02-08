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


Writing simple tests in CheckPy
--------------------------------

Tests in CheckPy are instances of ``checkpy.tests.Test``. These ``Test`` instances have several
abstract methods that you can implement or rather, overwrite by binding a new method.
These methods are executed when CheckPy runs a test. For instance you have the
``description`` method which is called to produce a description for the test, the ``timeout``
method which is called to determine the maximum alotted time for this test, and
ofcourse the ``test`` method which is called to actually perform the test. This
``Test`` instance is automatically provided to you when you decorate a function with
the ``checkpy.tests.test`` decorator. In our hello-world example this looked something like:

.. code-block:: python

    @t.test(0)
    def exactlyHelloWorld(test):

Here the ``t.test`` decorator (``t`` is short for ``checkpy.tests``) decorates
the function ``exactlyHelloWorld``. This causes CheckPy to treat ``exactlyHelloWorld``
as a `test creator` function. That when called produces an instance of ``Test``.
The ``t.test`` decorator accepts an argument that is used to determine the order
in which the result of the test is shown to the screen (lowest first). The decorator
then passes an instance of ``Test`` to the decorated function (``exactlyHelloWorld``).
It is up to ``exactlyHelloWorld`` to overwrite some or all abstract methods of that one
instance of ``Test`` that it receives.

Lets start with the necessities. CheckPy requires you to overwrite two methods from every
``Test`` instance. These methods are ``test`` and ``description``. The ``description`` method
should produce the description, that can be just a string, for the user to see. In our
hello-world example we used this ``description`` method:

.. code-block:: python

    test.description = lambda : "prints exactly: Hello, world!"

Depending on whether the test fails or passes, the user sees this string in red or green
respectively. The other method we have to overwrite, the ``test`` method, should return
``True`` or ``False`` depending on whether the tests passes or fails. You are free to implement
this method in any which way you want. CheckPy just offers some useful tools to make
your testing life easier. Again, looking back at our hello-world example, we used this
``test`` method:

.. code-block:: python

    def testMethod():
        output = lib.outputOf(test.fileName)
        return asserts.exact(output.strip(), "Hello, world!")

    test.test = testMethod

So what's going on here? Python doesn't support multi statement lambda functions. This means that
if you want to use multiple statements, you have to resort to named functions, i.e.
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

That's all there is to it. You simply write a function and decorate it with the `test` decorator.
Overwrite a couple of methods of ``Test``, and you're good to go.

Testing functions
-----------------

Let's make life a little more exciting. CheckPy can do a lot more besides simply running a Python file
and looking at print output. Specifically CheckPy lets you import said Python file
as a module and do all sort of things with it and to it. Lets focus on Functions for now.

For an assignment on (biological) virus simulations, we asked students to do the following:

Write a function ``generateVirus(length)``.
This function should accept one argument ``length``, that is an integer representing the length of the virus.
The function should return a virus, that is a string of random nucleotides (``'A'``, ``'T'``, ``'G'`` or ``'C'``).

This is just a small part of a bigger assignment that ultimately moves towards a simulation
of viruses in a patient. We can use CheckPy to test several aspects of this assignment.
For instance to test whether only the nucleotides ATGC occurred we wrote the following:

.. code-block:: python

    @t.test(10)
    def onlyATGC(test):
    	def testMethod():
    		generateVirus = lib.getFunction("generateVirus", test.fileName)
    		pairs = "".join(generateVirus(10) for _ in range(1000))
    		return asserts.containsOnly(pairs, "AGTC")

    	test.test = testMethod
    	test.description = lambda : "generateVirus() produces viruses consisting only of A, T, G and C"

To test whether the function actually exists and accepted just one argument, we wrote the following:

.. code-block:: python

    @t.test(0)
    def isDefined(test):
      def testMethod():
        generateVirus = lib.getFunction("generateVirus", test.fileName)
        return len(generateVirus.arguments) == 1

      test.test = testMethod
      test.description = lambda : "generateVirus is defined and accepts just one argument"
