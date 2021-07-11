import argparse
import os
import sys

from py2neo import ClientError, DatabaseError
from prov.model import ProvDocument

from prov2neo.client import Client, ConnectionError


def create_parser():
    """Create the command line interface argument parser.

    Params:
    -------
    """
    parser = argparse.ArgumentParser("prov2neo",
                                     description="Import W3C PROV documents to Neo4j.")
    parser.add_argument("-f", "--format",
                        help="input PROV format",
                        choices=["provn", "json", "rdf", "xml"],
                        default="json",)
    parser.add_argument("-i", "--input",
                        help="input files, use '.' for stdin",
                        nargs="+", default=None)
    parser.add_argument("-a", "--address",
                        help="Neo4j address")
    parser.add_argument("-u", "--username",
                        help="Neo4j username")
    parser.add_argument("-p", "--password",
                        help="Neo4j password")
    parser.add_argument("-n", "--name",
                        help="Neo4j target database name", default="neo4j")
    parser.add_argument("-s", "--scheme",
                        help="connection scheme to use when connecting to Neo4j",
                        choices=["bolt", "bolt+s", "bolt+ssc",
                                 "http", "https", "http+s", "http+ssc"],
                        default="bolt+s")
    return parser


def deserialize(file_path, fmt):
    """Deserialize a provenance graph from a file."""
    return ProvDocument.deserialize(source=file_path, format=fmt)


def create_and_connect_client(args):
    """Create a `prov2neo` client and connect it to a neo4j instance."""
    client = Client()
    client.connect(args.address, args.username, args.password, args.name, args.scheme)
    return client


def main():
    """Command line script entry point.

    Retrieve command line arguments and proceed from there.
    When no input is given or the paths to the input files
    are faulty, the program prints the --help message
    and exits.

    If the paths to the input file are valid the files are
    deserialized into a prov.model.ProvDocuments.
    A prov2neo.client.Client is created and a connection to
    a neo4j instance is established before importing the
    ProvDocument/ProvDocuments into the neo4j instance.

    Params:
    -------
    """
    parser = create_parser()
    args = parser.parse_args()

    if not args.input:
        print(parser.format_help())
        return

    # remove duplicates
    args.input = list(set(args.input))

    # do not read from stdin, when importing multiple graphs
    if len(args.input) > 1 and "." in args.input:
        args.input = [fp for fp in args.input if fp != "."]

    try:
        client = create_and_connect_client(args)
    except DatabaseError as e:
        print(f"{str(e)}")
        print("Hint: Check if your Neo4j version supports the creation of new databases. (The Community Edition does not!)")
        return
    except ClientError as e:
        print(f"{str(e)}")
        return
    except ConnectionError as e:
        print(f"{str(e)}")
        print("Hint: Check if you specified the correct database address, username and password.")
        return
    except ValueError as e:
        print(f"{str(e)}")
        print("Hint: Check if you specified a supported connection scheme.")
        return

    if args.input == ["."]:
        try:
            graph = deserialize(sys.stdin, args.format)
        except:
            print(f"Failed to deserialize from stdin.")
            return
        client.import_graph(graph)
    else:
        # check for valid file paths before deserialization/import
        for fp in args.input:
            if not os.path.exists(fp):
                print(f"File {fp} not found. Invalid path?")
                return
        # deserialize and import one file at a time
        for fp in args.input:
            try:
                graph = deserialize(fp, args.format)
            except:
                print(f"Failed to deserialize {fp}.")
                return
            client.import_graph(graph)


if __name__ == "__main__":
    main()
