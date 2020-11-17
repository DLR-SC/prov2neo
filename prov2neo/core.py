from collections import deque, defaultdict
from datetime import date, datetime, time, timedelta
from itertools import islice
from typing import Any, Iterable, Union, Tuple, List, Dict

from neotime import DateTime, Duration, Time
from prov.identifier import QualifiedName
from prov.model import (
    PROV_N_MAP,
    ProvActivity,
    ProvAgent,
    ProvDocument,
    ProvBundle,
    ProvElement,
    ProvEntity,
    ProvRelation,
)
from py2neo import Graph, GraphService, ClientError
from py2neo.data import Node, Relationship


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
        elif isinstance(value, (date, datetime)):
            value = DateTime.from_iso_format(value.isoformat())
        elif isinstance(value, time):
            value = Time.from_iso_format(value.isoformat())
        elif isinstance(value, timedelta):
            value = Duration(seconds=value.total_seconds())
        enc_attrs[key].append(value)
    return {key: (vs[0] if len(vs) <= 1 else vs) for key, vs in enc_attrs.items()}


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

        if name not in graph_service:
            # check if db exists already, if not try to create it
            try:
                system = graph_service.system_graph
                system.run(f"CREATE DATABASE {name} IF NOT EXISTS;")
            except ClientError as e:
                print("WARNING: ", e)

        self.graph_db = graph_service[name]
        self.add_constraints()

    def add_constraints(self):
        """Add uniqueness constraints to the property key 'id' for all basic PROV types."""
        if self.graph_db is None:
            return
        for label in NODE_LABELS.values():
            property_key = "id"
            if property_key in self.graph_db.schema.get_uniqueness_constraints(label):
                continue  # constraint already exists, therefore skip this one
            self.graph_db.schema.create_uniqueness_constraint(label, property_key)

    def import_graph(self, graph: ProvDocument):
        """Import a PROV graph to neo4j.

        Run transactions of size *self.BATCH_SIZE*"""
        if self.graph_db is None:
            return
        self.node_dict, self.edge_list = self._convert_nodes(graph)
        self.edge_list.extend(self._convert_edges(graph))
        self._execute_batch_transactions(self.node_dict.values())
        self._execute_batch_transactions(self.edge_list)

    @staticmethod
    def chunks(it: Iterable[Any], size: int):
        """Return *size* sized chunks of iterable *it*."""
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
        """Convert prov elements to neo4j nodes.

        Explore prov graph layer by layer using bfs based order.
        Create nodes for each bundle and connect them to the nodes that they contain."""
        self.node_dict, relations = dict(), list()
        queue = deque([(None, graph.bundles), (None, graph.get_records(ProvElement))])
        while queue:
            prev_layer, curr_layer = queue.popleft()
            for element in curr_layer:
                node_id, node = self._create_or_update_node(element)
                self.node_dict[node_id] = node
                if prev_layer is not None:
                    target = self.node_dict[prev_layer]
                    relation_type = "bundledIn"
                    relations.append(Relationship(node, relation_type, target))
                if not isinstance(element, ProvBundle):
                    continue
                queue.append((node_id, element.bundles))
                queue.append((node_id, element.get_records(ProvElement)))
        return self.node_dict, relations

    def _update_existing_node(
        self, node_id: str, labels: List[Any], attributes: Dict[str, Any]
    ):
        """Update labels and property values of existing node.

        Update the labels and the properties of an existing node,
        if there is new information from another node declaration of the same id."""
        node = self.node_dict[node_id]
        # add missing label if node already exists
        missing_labels = labels - set(node.labels)
        for label in missing_labels:
            node.add_label(label)
        # update attribute values of existing node
        for key, values in attributes.items():
            old_attrs = node[key]
            updated = (
                set(old_attrs) if isinstance(old_attrs, list) else set([old_attrs])
            )
            if isinstance(values, list):
                updated.update(values)
            else:
                updated.add(values)
            updated = [v for v in updated if v is not None]
            node[key] = updated[0] if len(updated) <= 1 else updated
        return node

    def _create_or_update_node(self, element: Union[ProvElement, ProvBundle]):
        """Create or update py2neo node from a given prov element/bundle.

        Check whether node already exists, if yes then update the existing one.
        If no, then create a new one.
        """
        encoded_id = encode_qualified_name(element.identifier)
        attributes = {"id": encoded_id}
        if isinstance(element, ProvBundle):
            attributes["prov:type"] = "prov:Bundle"
        else:
            attributes.update(encode_attributes(element.attributes))
        labels = set([NODE_LABELS[type(element)]])
        prov_types = attributes.get("prov:type")
        if prov_types:
            labels.update(prov_types if isinstance(prov_types, list) else [prov_types])
        if encoded_id in self.node_dict:
            # update existing node
            updated_node = self._update_existing_node(encoded_id, labels, attributes)
            return encoded_id, updated_node
        # create new node
        return encoded_id, Node(*labels, **attributes)

    def _convert_edges(self, graph: ProvDocument):
        """Convert prov relations to neo4j relationships/edges."""
        graph = graph.flattened()
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
