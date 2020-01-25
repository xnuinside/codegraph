CodeGraph
=========

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



![Code Graph - Code with not used module](/docs/img/code_with_trash_module.png?raw=true "Code with not used module")
![Code Graph - Code there all modules linked together](/docs/img/normal_code.png?raw=true "Code with modules that linked together")

TODO:
    1. Create normal readme
    2. Add tests
    3. Add possibility to work with any code based (not depend on Python language only)
    4. Work on visual part of Graph (now it is not very user friendly)
    5. Add support to variables (names) as entities

Contributing:
    Open PR with improvements that you want to add

    If you have any questions - write me xnuinside@gmail.com