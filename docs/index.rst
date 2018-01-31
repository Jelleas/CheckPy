Welcome to CheckPy's documentation!
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


CheckPy
=======

A customizable education oriented tester for Python.
Developed for courses in the
`Minor Programming <http://www.mprog.nl/>`__ at the `UvA <http://www.uva.nl/>`__.

Installation
------------

::

     pip install checkpy

Usage
-----

::

    usage: checkpy [-h] [-module MODULE] [-download GITHUBLINK]
                   [-register LOCALLINK] [-update] [-list] [-clean] [--dev]
                   [file]

    checkPy: a python testing framework for education. You are running Python
    version 3.6.2 and checkpy version 0.4.0.

    positional arguments:
      file                  name of file to be tested

    optional arguments:
      -h, --help            show this help message and exit
      -module MODULE        provide a module name or path to run all tests from
                            the module, or target a module for a specific test
      -download GITHUBLINK  download tests from a Github repository and exit
      -register LOCALLINK   register a local folder that contains tests and exit
      -update               update all downloaded tests and exit
      -list                 list all download locations and exit
      -clean                remove all tests from the tests folder and exit
      --dev                 get extra information to support the development of
                            tests


Features
--------

-  Customizable output, you choose what the users see.
-  Support for blackbox and whitebox testing.
-  The full scope of Python is available when designing tests.
-  Automatic test distribution, CheckPy will keep its tests up to date by periodically checking for new tests.
-  No infinite loops! CheckPy kills tests after a predefined timeout.
