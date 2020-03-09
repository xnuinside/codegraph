""" main module of testsdiffer for console  (cli) usage"""
import os
import pprint

import clifier

from codegraph import __version__
from codegraph import core

CLI_CFG_NAME = "conf/cli.yml"


def cli():
    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), CLI_CFG_NAME)
    _cli = clifier.Clifier(config_path, prog_version=__version__)
    parser = _cli.create_parser()
    args = parser.parse_args()
    main(args)


def main(args):
    usage_graph = core.CodeGraph(args).usage_graph()
    pprint.pprint(usage_graph)
    if not args.object_only:
        # to make more quick work if not needed to visualize
        import codegraph.vizualyzer as vz
        vz.draw_graph(usage_graph)
