import argparse
import os
import sys

from prov.model import ProvDocument

from .core import Importer


def main():
    "Command line script entry point."
    parser = argparse.ArgumentParser("prov2neo", description="Import W3C PROV graphs to neo4j.")
    parser.add_argument("-f", "--format", help="input prov format", choices=["provn", "json", "rdf", "xml"], default="json")
    parser.add_argument("-i", "--input", help="input file, for stdin use '.'", required=True)
    parser.add_argument("-H", "--host", help="neo4j instance host")
    parser.add_argument("-u", "--username", help="neo4j instance username")
    parser.add_argument("-p", "--password", help="neo4j instance password")
    parser.add_argument("-n", "--name", help="Neo4j database name", default=None)

    args = parser.parse_args()
    graph, infile = None, None
    if args.input == ".":
        infile = sys.stdin
    elif os.path.exists(args.input):
        infile = args.input
    
    graph = ProvDocument.deserialize(source=infile, format=args.format).flattened().unified()

    auth = {
        "host":     f"{args.host}",
        "user":     f"{args.username}",
        "password": f"{args.password}"
    }

    imp = Importer()
    imp.connect(**auth)
    imp.import_graph(graph)


if __name__ == "__main__":
    main()


