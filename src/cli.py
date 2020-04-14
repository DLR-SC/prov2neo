import argparse
import os
import sys

from prov.model import ProvDocument

from p2n import import_graph


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

    if os.path.exists(args.input):
        infile = args.input
        graph = ProvDocument.deserialize(source=infile, format=args.format)
    elif not args.input:
        infile = sys.stdin
        graph = ProvDocument.deserialize(source=infile, format=args.format)
    auth = {"host": f"{args.host}", "username": f"{args.username}", "password": f"{args.password}"}
    import_graph(auth, graph)


if __name__ == "__main__":
    main()
