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
@click.option("--file-path", help="File path to start dependency search from")
@click.option("--distance", type=int, help="Distance to search for dependencies")
def cli(paths, object_only, file_path, distance):
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

    args = {
        "paths": paths,
        "object_only": object_only,
        "file_path": file_path,
        "distance": distance,
    }
    main(args)


def main(args):
    code_graph = core.CodeGraph(args)
    usage_graph = code_graph.usage_graph()

    if args.get("file_path") and args.get("distance"):
        dependencies = code_graph.get_dependencies(args["file_path"], args["distance"])
        print(f"Dependencies for {args['file_path']}:")
        for distance, files in dependencies.items():
            print(f"  Distance {distance}: {', '.join(files)}")
    else:
        pprint.pprint(usage_graph)
        if not args["object_only"]:
            import codegraph.vizualyzer as vz

            vz.draw_graph(usage_graph)


if __name__ == "__main__":
    cli()
