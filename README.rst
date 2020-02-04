CodeGraph
=========

|badge1| |badge2| |badge3|

.. |badge1| image:: https://img.shields.io/pypi/v/codegraph 
.. |badge2| image:: https://img.shields.io/pypi/l/codegraph
.. |badge3| image:: https://img.shields.io/pypi/pyversions/codegraph
   
Tool that create a graph of code to show dependencies between code entities (methods, classes and etc).
CodeGraph does not execute code, it is based only on lex and syntax parse, so it not need to install
all your code dependencies.

Usage:

    pip install codegraph

    cg /path/to/your_python_code
    # path must be absolute

your_python_code - module with your python code

For example, if I put codegraph in my user home directory path will be:

    cg /Users/myuser/codegraph/codegraph

Pass '-o' flag if you want only print dependencies in console and don't want graph visualisation

    cg /path/to/your_python_code -o

If you want to change view and play with graph output - you can check 'vizualyzer.py'
and play with matplotlib and networkX settings.

In default view - red line show dependencies between entities in different modules. Green - entities in module.

.. image:: codegraph/docs/img/graph_visualisation.png
  :width: 250
  :alt: Graph visualisation

.. image:: codegraph/docs/img/code_with_trash_module.png
  :width: 250
  :alt: Code with not used module
  
.. image:: codegraph/docs/img/normal_code.png
  :width: 250
  :alt: Code there all modules linked together

TODO:
*****
    1. Create normal readme
    2. Add tests
    3. Add possibility to work with any code based (not depend on Python language only)
    4. Work on visual part of Graph (now it is not very user friendly)
    5. Add support to variables (names) as entities

Contributing:
    Open PR with improvements that you want to add

    If you have any questions - write me xnuinside@gmail.com
