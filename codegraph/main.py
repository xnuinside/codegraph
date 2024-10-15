""" main module of testsdiffer for console (cli) usage"""

import pprint
import sys

import click

from codegraph import __version__, core

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, message="CodeGraph version %(version)s")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "-o",
    "--object-only",
    is_flag=True,
    help="Don't visualize code dependencies as graph",
)
def cli(paths, object_only):
    """
    Tool that creates a graph of code to show dependencies between code entities (methods, classes, etc.).
    CodeGraph does not execute code, it is based only on lex and syntax parsing.

    PATHS: Provide path(s) to code base
    """
    if not paths:
        click.echo(
            "Error: No paths provided. Please specify at least one path to the code base.",
            err=True,
        )
        sys.exit(1)

    args = {"paths": paths, "object_only": object_only}
    main(args)


def main(args):
    usage_graph = core.CodeGraph(args).usage_graph()
    pprint.pprint(usage_graph)
    if not args["object_only"]:
        # to make more quick work if not needed to visualize
        import codegraph.vizualyzer as vz

        vz.draw_graph(usage_graph)


if __name__ == "__main__":
    cli()
