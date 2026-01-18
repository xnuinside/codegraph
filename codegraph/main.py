""" main module of testsdiffer for console (cli) usage"""

import logging
import pprint
import sys
from argparse import Namespace

import click

from codegraph import __version__, core

logger = logging.getLogger(__name__)

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
@click.option("--file-path", help="File path to start dependency search from")
@click.option("--distance", type=int, help="Distance to search for dependencies")
@click.option(
    "--matplotlib",
    is_flag=True,
    help="Use matplotlib visualization instead of interactive D3.js (default)",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output path for D3.js HTML file (default: ./codegraph.html)",
)
def cli(paths, object_only, file_path, distance, matplotlib, output):
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

    args = Namespace(
        paths=paths,
        object_only=object_only,
        file_path=file_path,
        distance=distance,
        matplotlib=matplotlib,
        output=output,
    )
    main(args)


def main(args):
    code_graph = core.CodeGraph(args)
    usage_graph = code_graph.usage_graph()
    entity_metadata = code_graph.get_entity_metadata()

    if args.file_path and args.distance:
        dependencies = code_graph.get_dependencies(args.file_path, args.distance)
        click.echo(f"Dependencies for {args.file_path}:")
        for distance, files in dependencies.items():
            click.echo(f"  Distance {distance}: {', '.join(files)}")
    elif args.object_only:
        pprint.pprint(usage_graph)
    else:
        import codegraph.vizualyzer as vz

        if args.matplotlib:
            vz.draw_graph_matplotlib(usage_graph)
        else:
            vz.draw_graph(usage_graph, entity_metadata=entity_metadata, output_path=args.output)


if __name__ == "__main__":
    cli()
