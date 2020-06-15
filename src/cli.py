import argparse
import os
import sys

from prov.model import ProvDocument

from p2n import Importer


def parse_args():
    parser = argparse.ArgumentParser("prov2neo", description="Import W3C PROV graphs to neo4j.")
    parser.add_argument("-f", "--format", help="input prov format", choices=["provn", "json", "rdf", "xml"], default="json")
    parser.add_argument("-i", "--input", help="input destination, read from input if none given", default="")
    parser.add_argument("-H", "--host", help="neo4j instance host")
    parser.add_argument("-u", "--username", help="neo4j instance username")
    parser.add_argument("-p", "--password", help="neo4j instance password")
    return parser.parse_args()


def main():
    args = parse_args()
    graph, infile = None, None
    if os.path.exists(args.input):
        infile = args.input
    elif not args.input:
        infile = sys.stdin

    auth = {"host": f"{args.host}", "username": f"{args.username}", "password": f"{args.password}"}

    imp = Importer(auth)

    graph = ProvDocument.deserialize(source=infile, format=args.format)
    
    if graph.has_bundles():
        bundles = graph.bundles
        print(list(bundles)[0])
        imp.import_graph(list(bundles)[0])
    else:
        imp.import_graph(graph)


if __name__ == "__main__":
    main()


