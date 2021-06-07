import argparse
import os
import sys

from prov.model import ProvDocument

from prov2neo.client import Client


def create_parser():
    """Create the command line interface argument parser.

    Params:
    -------
    """
    parser = argparse.ArgumentParser("prov2neo",
                                     description="Import W3C PROV graphs to Neo4j.")
    parser.add_argument("-f", "--format",
                        help="input PROV format",
                        choices=["provn", "json", "rdf", "xml"],
                        default="json",)
    parser.add_argument("-i", "--input",
                        help="input file, '.' for stdin",
                        default=None)
    parser.add_argument("-a", "--address",
                        help="Neo4j instance address")
    parser.add_argument("-u", "--username",
                        help="Neo4j instance username")
    parser.add_argument("-p", "--password",
                        help="Neo4j instance password")
    parser.add_argument("-n", "--name",
                        help="Neo4j database name", default="neo4j")
    parser.add_argument("-s", "--scheme",
                        help="connection scheme to use when connecting to Neo4j",
                        choices=["bolt", "bolt+s", "bolt+ssc",
                                 "http", "https", "http+s", "http+ssc"],
                        default="bolt+s")
    return parser


def main():
    """Command line script entry point.

    Retrieve command line arguments and proceed from there.
    When no input is given or the path to the input file
    is faulty, the program prints the --help message
    and exits.

    If the path to the input file is valid the file is
    deserialized into a prov.model.ProvDocument.
    A prov2neo.client.Client is created and a connection to
    a neo4j instance is established before importing the
    ProvDocument into the neo4j instance.

    Params:
    -------
    """
    parser = create_parser()
    args = parser.parse_args()

    # print help and exit if no input file is given
    if args.input is None:
        print(parser.format_help())
        return

    # set stdin as input file
    if args.input == ".":
        in_fp = sys.stdin

    # check if input file path exists
    if os.path.exists(args.input):
        in_fp = args.input
    # if not, print help and exit
    else:
        print("Invalid file path {args.input}")
        print(parser.format_help())
        return

    # try to deserialize the PROV graph from the input file
    try:
        graph = ProvDocument.deserialize(source=in_fp, format=args.format)
    # if exception occurs print its message followed by help then exit
    except Exception as e:
        print(e)
        print(parser.format_help())
        return

    # create a prov2neo client
    client = Client()
    # connect to the neo4j instance
    client.connect(
        address=args.address,
        user=args.username,
        password=args.password,
        name=args.name,
        scheme=args.scheme,
    )
    # import the PROV graph
    client.import_graph(graph)


if __name__ == "__main__":
    main()
