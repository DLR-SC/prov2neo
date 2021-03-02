from prov.model import ProvDocument
from py2neo import ClientError, GraphService, Subgraph

from prov2neo.decode import decode_graph
from prov2neo.encode import (
    NODE_LABELS,
    PROV2NEO_ID,
    PROV2NEO_NODE,
    encode_graph
)


class Client:
    """prov2neo client used to connect to a neo4j instance, import and export PROV graphs.

    Supports:
        - PROV graph import [PROV -> Neo4j]
        - PROV graph export [Neo4j -> PROV]
    """
    def __init__(self):
        self.graph_db = None

    def connect(self, address: str, user: str, password: str, name: str, scheme: str) -> None:
        """Establishes connection to a neo4j instance.

        Parameters
        ----------
        address : str
            The address of the neo4j server in the following format:
            <host>:<port>
        user : str
            The username used to authenticate the user connecting to the neo4j
            instance.
        password : str
            The password used to authenticate the user connecting to the neo4j
            instance.
        name : str
            The name of the database that the connection is supposed to be
            established to. If the server contains no database of this name,
            a new one is created. Creating databases is only possible for
            enterprise neo4j versions 4.0 and above.
        scheme : str
            The name of the connection protocol that should be used for the
            database connection. Valid protocols/URI schemes are:
            ["bolt", "bolt+s", "bolt+ssc", "http", "https", "http+s", "http+ssc"].
        """
        enforce_tls = scheme not in ["bolt", "http"]
        graph_service = GraphService(
            address=address,
            scheme=scheme,
            user=user,
            password=password,
            secure=enforce_tls
        )
        if name not in graph_service:
            try:
                system = graph_service.system_graph
                system.run(f"CREATE DATABASE {name} IF NOT EXISTS;")
            except ClientError as e:
                print(f"ClientError occured in: {self.connect.__name__}")
                print(f"Error Message: {e}")

        self.graph_db = graph_service[name]
        self.add_uniqueness_constraints()

    def add_uniqueness_constraints(self) -> None:
        """Add uniqueness constraints to the property key 'id' for all basic PROV types.

        We consider ProvActivity, ProvAgent, ProvEntity, ProvBundle to be basic PROV types.

        Parameters
        ----------
        """
        if self.graph_db is None:
            return
        for label in NODE_LABELS.values():
            if "id" not in self.graph_db.schema.get_uniqueness_constraints(label):
                self.graph_db.schema.create_uniqueness_constraint(label, "id")

    def import_graph(self, graph: ProvDocument) -> None:
        """Import a PROV graph to a named neo4j graph database.

        Parameters
        ----------
        graph : ProvDocument
            The PROV graph to import into neo4j.
        """
        if self.graph_db is None:
            return

        # encode graph as py2neo Subgraph
        encoded_graph = encode_graph(graph)

        tx = self.graph_db.begin()
        # node identifier acts as primary key for merge
        primary_key = PROV2NEO_ID
        # 'prov2neo:node' acts as primary label for merge
        primary_label = PROV2NEO_NODE[1]

        # merge all nodes & edges into self.graph_db
        # merge updates already existing nodes
        # and creates new ones if necessary
        tx.merge(encoded_graph, primary_label=primary_label, primary_key=primary_key)
        tx.commit()

    def export_graph(self):
        """Export a PROV graph from a named neo4j graph database.

        Parameters
        ----------
        """
        raise NotImplementedError
