from collections import defaultdict, deque
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Iterable, List, Tuple

from neotime import DateTime, Duration, Time
from prov.identifier import QualifiedName
from prov.model import (PROV_N_MAP, Identifier, Literal, ProvActivity,
                        ProvAgent, ProvBundle, ProvDocument, ProvElement,
                        ProvEntity, ProvRelation)
from py2neo import ClientError, Graph, GraphService
from py2neo.data import Node, Relationship

# Default label for each node that is imported by prov2neo
# Also used as a placeholder for nodes without formal node definitions
PROV2NEO_NODE = "prov2neo:node"

NODE_LABELS = {
    ProvActivity: "prov:Activity",
    ProvAgent: "prov:Agent",
    ProvBundle: "prov:Bundle",
    ProvEntity: "prov:Entity",
}


def encode_attributes(attributes: List[Tuple[Any, Any]]):
    """Encode attribute key, value tuple list.

    Convert datetime objects to NeoTime objects.
    Convert qualified names to strings."""
    enc_attrs = defaultdict(list)
    for key, value in attributes:
        if isinstance(key, QualifiedName):
            key = encode_qualified_name(key)
        if isinstance(value, QualifiedName):
            value = encode_qualified_name(value)
        elif isinstance(value, date):
            value = DateTime.from_native(value)
        elif isinstance(value, datetime):
            value = DateTime.from_native(value)
        elif isinstance(value, time):
            value = Time.from_native(value)
        elif isinstance(value, timedelta):
            value = Duration(seconds=value.total_seconds())
        elif isinstance(value, Literal):
            # TODO: Do we want to save the PROV-N Representation in Neo4j?
            value = value.provn_representation()
        elif isinstance(value, Identifier):
            # TODO: Do we want to save a string or the PROV-N Representation in Neo4j?
            value = str(value)
        enc_attrs[key].append(value)

    for key, values in enc_attrs.items():
        if len(values) == 1:
            enc_attrs[key] = values[0]
            continue
        enc_attrs[key] = values
    return enc_attrs


def encode_qualified_name(q_name: QualifiedName):
    """String encode QualifiedName *q_name*."""
    # provn repr adds single quotes, remove them by [1:-1]
    return q_name.provn_representation()[1:-1]


class Importer:
    """Import provenance graphs to neo4j."""

    def __init__(self):
        self.graph_db = None
        self.node_dict = {}
        self.edge_list = []
        self.BATCH_SIZE = 200

    def connect(self, address: str, user: str, password: str, name: str, scheme: str):
        """Establishes connection to neo4j instance.

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
        # enforce TLS for protocols that require it
        secure = scheme not in ["bolt", "http"]
        graph_service = GraphService(
            address=address, scheme=scheme, user=user, password=password, secure=secure
        )
        # check if db exists already, if not try to create it
        if name not in graph_service:
            try:
                system = graph_service.system_graph
                system.run(f"CREATE DATABASE {name} IF NOT EXISTS;")
            except ClientError as e:
                print("WARNING: ", e)
        self.graph_db = graph_service[name]
        self.add_constraints(self.graph_db)

    def add_constraints(self, graph_db: Graph):
        """Add uniqueness constraints to the property key 'id' for all basic PROV types."""
        if graph_db is None:
            return
        for label in NODE_LABELS.values():
            if "id" not in graph_db.schema.get_uniqueness_constraints(label):
                graph_db.schema.create_uniqueness_constraint(label, "id")

    def import_graph(self, graph: ProvDocument):
        """Import a PROV graph to neo4j.

        Run transactions of size *self.BATCH_SIZE*"""
        if self.graph_db is None:
            return
        self.node_dict, self.edge_list = self.convert_nodes(graph)
        self.edge_list.extend(self.convert_edges(graph))
        self.exec_txs(self.node_dict.values())
        self.exec_txs(self.edge_list)

    @staticmethod
    def chunks(it: Iterable[Any], step: int):
        """Return *step* sized chunks of iterable *it*."""
        lst = list(it)
        for start in range(0, len(lst), step):
            stop = start + step
            yield lst[start:stop]

    def exec_txs(self, nodes_or_rels: Iterable[Any]):
        """Push nodes and relationships to neo4j db using batched transactions."""
        for batch in self.chunks(nodes_or_rels, step=self.BATCH_SIZE):
            tx = self.graph_db.begin()
            for item in batch:
                if isinstance(item, Node):
                    item.add_label(PROV2NEO_NODE)
                tx.merge(item, primary_label=PROV2NEO_NODE, primary_key="id")
            tx.commit()

    @staticmethod
    def bfs_walker(graph: ProvDocument):
        """Walk through provenance *graph* by bfs.

        Yield discovered nodes (ProvElement) and their corresponding
        parent bundle id. The queue is initialised with the bundles
        and elements contained within *graph*'s uppermost layer.

        The queue consists of tuples (A, B) where A is a bundle identifier and B is either:
            . an iterable of ProvElement's or
            . an iterable of ProvBundle's
        """
        queue = deque([(None, graph.get_records(ProvElement)), (None, graph.bundles)])
        while queue:
            parent_bundle_id, elements = queue.popleft()
            for elem in elements:
                if isinstance(elem, ProvBundle):
                    bundle_id = encode_qualified_name(elem.identifier)
                    queue.append((bundle_id, elem.get_records(ProvElement)))
                    queue.append((bundle_id, elem.bundles))
                yield parent_bundle_id, elem

    def convert_nodes(self, graph: ProvDocument):
        """Convert all PROV nodes contained in *graph* to py2neo.Node's.

        Explore the graph using bfs, creating or updating nodes along the way.
        Supports multi-valued properties.
        """
        node_dict, relationships = {}, []

        for bundle_id, node in self.bfs_walker(graph):
            node_id = encode_qualified_name(node.identifier)

            if node_id not in node_dict:
                # node does not exist yet
                # create node and add it to node dictionary
                if isinstance(node, ProvBundle):
                    new_node = Node("prov:Bundle", **{"id": node_id, "prov:type": "prov:Bundle"})
                else:
                    new_node = self.create_node(node)
                node_dict[node_id] = new_node
            else:
                # node exists already
                existing = node_dict[node_id]
                if isinstance(node, ProvBundle):
                    update = Node("prov:Bundle", **{"id": node_id, "prov:type": "prov:Bundle"})
                else:
                    update = self.create_node(node)
                # update node labels and attributes
                node_dict[node_id] = self.update_node(existing, update)

            if bundle_id is not None:
                # create preliminary bundle node
                bundle = Node(
                    "prov:Bundle", **{"id": bundle_id, "prov:type": "prov:Bundle"}
                )
                if bundle_id not in node_dict:
                    # bundle node does not exist yet
                    # add bundle node to node dictionary
                    node_dict[bundle_id] = bundle
                else:
                    # bundle node does exist already
                    # update bundle node labels and attributes
                    existing = node_dict[bundle_id]
                    node_dict[bundle_id] = self.update_node(existing, bundle)
                # create relationship between bundle and node
                source, target = node_dict[node_id], node_dict[bundle_id]
                relationships.append(Relationship(source, "bundledIn", target))
        return node_dict, relationships

    @staticmethod
    def create_node(node: ProvElement):
        """Create a py2neo.Node from a prov.model.ProvElement."""
        node_id = encode_qualified_name(node.identifier)
        node_label = NODE_LABELS[type(node)]

        attributes = encode_attributes(node.attributes)
        attributes["id"] = node_id

        if "prov:type" in attributes:
            labels = attributes["prov:type"]
            labels = labels if isinstance(labels, list) else [labels]
            labels.append(node_label)
            attributes["prov:type"] = list(set(labels))
        else:
            attributes["prov:type"] = node_label

        labels = attributes["prov:type"]
        labels = labels if isinstance(labels, list) else [labels]
        return Node(*labels, **attributes)

    @staticmethod
    def update_node(node_a: Node, node_b: Node):
        """Update labels and attributes of node_a with those of node_b."""
        missing_labels = set(node_b.labels) - set(node_a.labels)
        # add missing labels
        for label in missing_labels:
            node_a.add_label(label)

        for key, values in node_b.items():
            if key in node_a:
                a_values = node_a[key]
                a_values = a_values if isinstance(a_values, list) else [a_values]

                b_values = node_b[key]
                b_values = b_values if isinstance(b_values, list) else [b_values]

                a_values.extend(b_values)
                a_values = list(set(a_values))
                node_a[key] = a_values[0] if len(a_values) == 1 else a_values
            else:
                node_a[key] = values
        return node_a

    def convert_edges(self, graph: ProvDocument):
        """Convert prov relations to neo4j relationships/edges."""
        graph = graph.flattened()
        edges = []
        for relation in graph.get_records(ProvRelation):
            (_, source_id), (_, target_id) = relation.formal_attributes[:2]
            attributes = [*relation.formal_attributes[2:], *relation.extra_attributes]
            relation_type = PROV_N_MAP[relation.get_type()]

            if isinstance(target_id, QualifiedName):
                # map to {Node} - Relation - {Node}
                enc_source_id = encode_qualified_name(source_id)
                enc_target_id = encode_qualified_name(target_id)
                source = self.get_node(enc_source_id)
                target = self.get_node(enc_target_id)
                enc_attributes = encode_attributes(attributes)
                relationship = Relationship(
                    source, relation_type, target, **enc_attributes
                )
                edges.append(relationship)
            else:
                # map to Node{Key: Value}
                enc_source_id = encode_qualified_name(source_id)
                source = self.get_node(enc_source_id)
                enc_attributes = encode_attributes([(relation_type, target_id)])
                update = Node(PROV2NEO_NODE, **enc_attributes)
                self.node_dict[enc_source_id] = self.update_node(source, update)
        return edges

    def get_node(self, node_id: str):
        """Get a node by it's string encoded id from *self.node_dict*.

        If the node doesn't exist, it will be created and added to *self.node_dict*."""
        default = Node(PROV2NEO_NODE, **{"id": node_id})
        if node_id not in self.node_dict:
            self.node_dict[node_id] = default
            return default
        return self.node_dict[node_id]
