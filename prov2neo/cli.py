import click

from prov2neo import __version__
from prov2neo import exceptions as exc
from prov2neo.client import SUPPORTED_SCHEMES, Client
from prov2neo.utils import read_doc, write_doc


@click.group(chain=True)
@click.version_option(version=__version__, prog_name="prov2neo")
@click.pass_context
def main(ctx: click.Context):
    """Connect to a neo4j instance and import/export provenance documents."""
    ctx.obj = Client()


@main.command()
@click.option("-a", "--address", required=True, type=str, help="Neo4j address.")
@click.option("-u", "--user", required=True, type=str, help="Neo4j account username.")
@click.option(
    "-p", "--password", required=True, type=str, help="Neo4j account password."
)
@click.option(
    "-n",
    "--dbname",
    default="neo4j",
    show_default=True,
    type=str,
    help="Neo4j database name.",
)
@click.option(
    "-s",
    "--scheme",
    default="bolt",
    show_default=True,
    type=click.Choice(SUPPORTED_SCHEMES),
    help="Connection scheme.",
)
@click.pass_obj
@exc.on_database_error(
    hint=f"Check if your neo4j version supports the creation of new databases."
    f"(The community edition does not!)",
)
@exc.on_client_error(msg="Client side error")
@exc.on_connection_error(
    hint="Check if you specified the correct database address, username and password."
)
@exc.on_value_error(hint="Check if you specified a supported connection scheme.")
def connect(
    client: Client,
    address: str,
    user: str,
    password: str,
    dbname: str,
    scheme: str,
):
    """Connect to a neo4j instance."""
    client.connect(
        address=address,
        user=user,
        password=password,
        dbname=dbname,
        scheme=scheme,
    )


@main.command("import")
@click.option(
    "-i",
    "--input",
    multiple=True,
    required=True,
    type=click.Path(exists=True),
    help="PROV file[s] to import.",
)
@click.pass_obj
def import_doc(client: Client, input: list[str]):
    """Import a provenance document into neo4j."""
    if not client.is_connected:
        ctx = click.get_current_context()
        ctx.fail("Import failed: Not connected to a neo4j instance.")
    for fp in input:
        graph = read_doc(fp)
        client.import_doc(graph)


@main.command("export", deprecated=True)
@click.option("-o", "--output", type=click.Path(), help="File to export to.")
@click.option(
    "-f", "--format", type=click.Choice(["json", "xml", "rdf", "dot", "provn"])
)
@click.pass_obj
def export_doc(client: Client, output: str, format: str):
    """Export a provenance document from neo4j."""
    if not client.is_connected:
        ctx = click.get_current_context()
        ctx.fail("Export failed: Not connected to a neo4j instance.")
    # export in multiple formats...
    graph = client.export_doc()
    write_doc(graph, output, format)


if __name__ == "__main__":
    main()
