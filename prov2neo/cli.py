import argparse
import os
import sys

from prov.model import ProvDocument

from prov2neo.core import Importer


def main():
    "Command line script entry point."
    parser = argparse.ArgumentParser("prov2neo", description="Import W3C PROV graphs to neo4j.")
    parser.add_argument("-f", "--format", help="input prov format", choices=["provn", "json", "rdf", "xml"], default="json")
    parser.add_argument("-i", "--input", help="input file, for stdin use '.'", default=None)
    parser.add_argument("-a", "--address", help="neo4j instance address")
    parser.add_argument("-u", "--username", help="neo4j instance username")
    parser.add_argument("-p", "--password", help="neo4j instance password")
    parser.add_argument("-n", "--name", help="neo4j database name", default="neo4j")
    parser.add_argument(
        "-s", "--scheme", 
        help="connection scheme to use when connecting to neo4j", 
        choices=["bolt", "bolt+s", "bolt+ssc", "http", "https", "http+s", "http+ssc"],
        default="bolt+s")

    args = parser.parse_args()
    infile = None
    if args.input is None:
        # print help msg and exit if missing input source
        print(parser.format_help())
        return
    elif args.input == ".":
        # stdin as input source
        infile = sys.stdin
    elif os.path.exists(args.input):
        # filepath as input source
        infile = args.input
    
    deserialized_infile = ProvDocument.deserialize(source=infile, format=args.format).flattened()

    importer = Importer()
    auth = {
        "address":  f"{args.address}",
        "user":     f"{args.username}",
        "password": f"{args.password}",
        "name":     f"{args.name}",
        "scheme":   f"{args.scheme}"
    }
    importer.connect(**auth)
    importer.import_graph(deserialized_infile)


if __name__ == "__main__":
    main()


