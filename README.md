### CodeGraph - static code analyzator, that create a diagram with your code structure.

![badge1](https://img.shields.io/pypi/v/codegraph) ![badge2](https://img.shields.io/pypi/l/codegraph) ![badge3](https://img.shields.io/pypi/pyversions/codegraph)![workflow](https://github.com/xnuinside/codegraph/actions/workflows/main.yml/badge.svg)

Tool that create a digram with your code structure to show dependencies between code entities (methods, modules, classes and etc).
Main advantage of CodeGraph, that is does not execute the code itself. You not need to activate any environments or install dependencies to analyse the target code. 
It is based only on lex and syntax parse, so it not need to install all your code dependencies.


### Install codegraph
```console
  
    pip install codegraph

```

### Analyze your code

codegraph - name of command line tool for CodeGrapg

```console

    codegraph /path/to/your_python_code
    # path must be absolute

    # or for one file

    codegraph /path/to/your_python_code

```

your_python_code - module with your python code

For example, if I put codegraph in my user home directory path will be:

    codegraph /Users/myuser/codegraph/codegraph

Pass '-o' flag if you want only print dependencies in console and don't want graph visualisation

    codegraph /path/to/your_python_code -o

If you want to change view and play with graph output - you can check 'vizualyzer.py'
and play with matplotlib and networkX settings.

### Colors meanings 
In default view - **red line** show dependencies between entities in different modules.
**Green** - links between objects/functions inside same module.

![Graph visualisation](https://github.com/xnuinside/codegraph/blob/main/docs/img/graph_visualisation.png "Graph visualisation")

![ Code with not used module](https://github.com/xnuinside/codegraph/blob/main/docs/img/code_with_trash_module.png "Code with not used module")

![Code there all modules linked together](https://github.com/xnuinside/codegraph/blob/main/docs/img/normal_code.png "Code there all modules linked together")

### TODO

    1. Create normal readme
    2. Add tests
    3. Work on visual part of Graph (now it is not very user friendly)
    4. Add support to variables (names) as entities
    5. Split usage & inheritance as a different cases

## Changelog
**v0.1.0**
### Improvements

1. Command line tool name changed from 'cg' to 'codegraph'.
2. Updated versions of dependencies
3. Minimal supported python version up to 3.8
4. Added some unit & functional tests
