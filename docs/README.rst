
CodeGraph - static code analyzator, that create a diagram with your code structure.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. image:: https://img.shields.io/pypi/v/codegraph
   :target: https://img.shields.io/pypi/v/codegraph
   :alt: badge1
 
.. image:: https://img.shields.io/pypi/l/codegraph
   :target: https://img.shields.io/pypi/l/codegraph
   :alt: badge2
 
.. image:: https://img.shields.io/pypi/pyversions/codegraph
   :target: https://img.shields.io/pypi/pyversions/codegraph
   :alt: badge3

.. image:: https://github.com/xnuinside/codegraph/actions/workflows/main.yml/badge.svg
   :target: https://github.com/xnuinside/codegraph/actions/workflows/main.yml/badge.svg
   :alt: workflow


Tool that create a digram with your code structure to show dependencies between code entities (methods, modules, classes and etc).
Main advantage of CodeGraph, that is does not execute the code itself. You not need to activate any environments or install dependencies to analyse the target code. 
It is based only on lex and syntax parse, so it not need to install all your code dependencies.

Install codegraph
^^^^^^^^^^^^^^^^^

.. code-block:: console


       pip install codegraph

Analyze your code
^^^^^^^^^^^^^^^^^

codegraph - name of command line tool for CodeGrapg

.. code-block:: console


       codegraph /path/to/your_python_code
       # path must be absolute

       # or for one file

       codegraph /path/to/your_python_code

your_python_code - module with your python code

For example, if I put codegraph in my user home directory path will be:

.. code-block::

   codegraph /Users/myuser/codegraph/codegraph


Pass '-o' flag if you want only print dependencies in console and don't want graph visualisation

.. code-block::

   codegraph /path/to/your_python_code -o


If you want to change view and play with graph output - you can check 'vizualyzer.py'
and play with matplotlib and networkX settings.

Colors meanings
^^^^^^^^^^^^^^^

In default view - **red line** show dependencies between entities in different modules.
**Green** - links between objects/functions inside same module.


.. image:: /docs/img/graph_visualisation.png
   :target: /docs/img/graph_visualisation.png
   :alt: Graph visualisation



.. image:: /docs/img/code_with_trash_module.png
   :target: /docs/img/code_with_trash_module.png
   :alt:  Code with not used module



.. image:: /docs/img/normal_code.png
   :target: /docs/img/normal_code.png
   :alt: Code there all modules linked together


TODO
^^^^

.. code-block::

   1. Create normal readme
   2. Add tests
   3. Work on visual part of Graph (now it is not very user friendly)
   4. Add support to variables (names) as entities
   5. Split usage & inheritance as a different cases


Changelog
---------

**v0.1.0**

Improvements
^^^^^^^^^^^^


#. Command line tool name changed from 'cg' to 'codegraph'.
#. Updated versions of dependencies
#. Minimal supported python version up to 3.8
#. Added some unit & functional tests
