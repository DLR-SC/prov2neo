from datetime import date, datetime, time, timedelta
from itertools import islice
from typing import Any, Dict, Iterable

from neotime import DateTime, Duration, Time
from prov.identifier import QualifiedName
from prov.model import (PROV_N_MAP, ProvActivity, ProvAgent, ProvDocument,
                        ProvElement, ProvEntity, ProvRelation)
from py2neo import Graph
from py2neo.data import Node, Relationship


def encode_attributes(attributes: Dict[Any, Any]):
    """Encode attribute dictionary.

    Convert datetime objects to NeoTime objects.
    Convert qualified names to strings."""
    enc_attrs = {}
    for key, value in attributes.items():
        if isinstance(key, QualifiedName):
            key = encode_qualified_name(key)
        if isinstance(value, QualifiedName):
            value = encode_qualified_name(value)
        elif isinstance(value, (date, datetime)):
            value = DateTime.from_iso_format(value.isoformat())
        elif isinstance(value, time):
            value = Time.from_iso_format(value.isoformat())
        elif isinstance(value, timedelta):
            value = Duration(seconds=value.total_seconds())
        enc_attrs[key] = value
    return enc_attrs


def encode_qualified_name(q_name: QualifiedName):
    """String encode QualifiedName *q_name*.

    Ignore namespace prefix if it does not exist."""
    prefix = f"{q_name.namespace.prefix}:" if q_name.namespace.prefix else ""
    return f"{prefix}{q_name.localpart}"


class Importer:
    """Import provenance graphs to neo4j."""
    def __init__(self):
        self.graph_db = None
        self.node_dict = {}
        self.edge_list = []
        self.BATCH_SIZE = 200

    def connect(self, host: str, user: str, password: str, name: str):
        """Establish connection to neo4j instance."""
        self.graph_db = Graph(host, user=user, password=password, name=name)
        self.graph_db.schema.create_uniqueness_constraint("Activity", "id")
        self.graph_db.schema.create_uniqueness_constraint("Agent", "id")
        self.graph_db.schema.create_uniqueness_constraint("Entity", "id")

    def import_graph(self, graph: ProvDocument):
        """Import a PROV graph to neo4j.

        Run transactions of size"""
        if self.graph_db is None:
            return
        self.node_dict = self._convert_nodes(graph)
        self.edge_list = self._convert_edges(graph)
        self._execute_batch_transactions(self.node_dict.values())
        self._execute_batch_transactions(self.edge_list)

    @staticmethod
    def chunks(it: Iterable[Any], size: int):
        """Return *n* sized chunks of iterable *it*."""
        it = iter(it)
        return iter(lambda: tuple(islice(it, size)), ())

    def _execute_batch_transactions(self, items: Iterable[Any]):
        """Execute transactions for all batches in *batches*."""
        for batch in self.chunks(items, self.BATCH_SIZE):
            tx = self.graph_db.begin()
            for item in batch:
                tx.create(item)
            tx.commit()

    def _convert_nodes(self, graph: ProvDocument):
        """Convert prov elements to neo4j nodes."""
        nodes = {}
        for element in graph.get_records(ProvElement):
            encoded_id = encode_qualified_name(element.identifier)
            attributes = encode_attributes(dict(element.attributes))
            attributes["id"] = encoded_id
            label = {
                ProvActivity: "Activity",
                ProvAgent: "Agent",
                ProvEntity: "Entity"
            }[type(element)]
            nodes[encoded_id] = Node(label, **attributes)
        return nodes

    def _convert_edges(self, graph: ProvDocument):
        """Convert prov relations to neo4j relationships/edges."""
        edges = []
        for relation in graph.get_records(ProvRelation):
            (_, source_id), (_, target_id), *attributes = relation.attributes
            relation_type = PROV_N_MAP[relation.get_type()]

            encoded_source_id = encode_qualified_name(source_id)
            encoded_target_id = encode_qualified_name(target_id)

            source = self.node_dict[encoded_source_id]
            target = self.node_dict[encoded_target_id]

            relationship = Relationship(source, relation_type, target)
            edges.append(relationship)
        return edges


if __name__ == "__main__":
    pass
