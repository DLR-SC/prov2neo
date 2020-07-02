import types
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Set, Type, Union

from neotime import DateTime, Duration, Time
from prov.constants import PROV_N_MAP
from prov.identifier import QualifiedName
from prov.model import (ProvActivity, ProvAgent, ProvDocument, ProvElement,
                        ProvEntity, ProvRelation)
from py2neo import Graph
from py2neo.ogm import GraphObject, Property, RelatedTo


def encode_qualified_name(q_name: QualifiedName):
    """Encode a Qualified Name as a string.

    Ignore colon and prefix if no prefix is given."""
    prefix = f"{q_name.namespace.prefix}:" if q_name.namespace.prefix else ""
    return f"{prefix}{q_name.localpart}"


@dataclass
class Template:
    """Template information container for Graph Object creation."""
    name: str
    property_keys: Set[str]

    def __post_init__(self):
        """Add necessary keys, 'id' and 'prov:type'."""
        if not self.property_keys:
            return
        self.property_keys.update(["id", "prov:type"])


class TemplateBuilder:
    """Handles template information computation."""

    @staticmethod
    def get_template(graph: ProvDocument, prov_type: Union[Type[ProvActivity], Type[ProvAgent], Type[ProvEntity]]):
        """Extract property keys from a PROV graph.

        Compute the maximal set of keys for vertices of type *prov_type*.
        All of them have to be known for Graph Object creation."""
        keys = set()
        for element in graph.get_records(prov_type):
            for key, _ in element.attributes:
                keys.add(encode_qualified_name(key))
        return Template(PROV_N_MAP[prov_type._prov_type].capitalize(), keys)


class GraphObjectClassFactory:
    """Handles Graph Object creation."""

    @staticmethod
    def create_class(graph: ProvDocument, prov_type: Union[Type[ProvActivity], Type[ProvAgent], Type[ProvEntity]]):
        """Create Graph Objects from template information.

        Register properties for all known vertex attribute keys as well as necessary keys 'id' & 'prov:type'.
        Register relation hooks for all known PROV relations.
        Add '__init__' to created types."""
        template = TemplateBuilder.get_template(graph, prov_type)

        def ns_callback(namespace):
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
            cls_dict = {}
            cls_dict.update({"__init__": __init__, "__primarykey__": "id"})
            cls_dict.update({relation: RelatedTo(GraphObject, relation) for relation in PROV_N_MAP.values()})
            cls_dict.update({key: Property(key) for key in template.property_keys})
            namespace.update(cls_dict)

        return types.new_class(template.name, (GraphObject, ), {}, ns_callback)


class Importer:
    """Handles Neo4j graph imports."""

    def __init__(self, authentication: Dict[str, Any]):
        self._nodes = {}
        self.n4j = None
        self.connect(authentication)

    def import_graph(self, graph: ProvDocument):
        """Import a PROV graph to Neo4j."""
        if not self.n4j:
            return
        self._add_elements(graph)
        self._add_relations(graph)
        for node in self._nodes.values():
            self.n4j.create(node)

    def connect(self, authentication: Dict[str, Any]):
        """Connect to a Neo4j instance."""
        host: str = f"bolt://{authentication['host']}/"
        self.n4j = Graph(host, user=authentication["username"], password=authentication["password"])
        self.n4j.schema.create_uniqueness_constraint("Activity", "id")
        self.n4j.schema.create_uniqueness_constraint("Agent", "id")
        self.n4j.schema.create_uniqueness_constraint("Entity", "id")

    def _add_elements(self, graph: ProvDocument):
        """Add *graph* vertices to self._nodes."""
        activity = GraphObjectClassFactory.create_class(graph, ProvActivity)
        agent = GraphObjectClassFactory.create_class(graph, ProvAgent)
        entity = GraphObjectClassFactory.create_class(graph, ProvEntity)

        for element in graph.get_records(ProvElement):
            raw_id = element.identifier
            enc_id = encode_qualified_name(raw_id)

            enc_attributes = {}
            enc_attributes.update({"id": enc_id})
            enc_attributes.update(self._encode(dict(element.attributes)))

            graph_obj = {
                ProvActivity: activity,
                ProvAgent: agent,
                ProvEntity: entity
            }[type(element)](**enc_attributes)

            self._nodes[enc_id] = graph_obj

    def _add_relations(self, graph: ProvDocument):
        """Add *graph* edges to self._nodes."""
        for relation in graph.get_records(ProvRelation):
            (_, source), (_, target) = relation.formal_attributes[:2]
            relation_type = PROV_N_MAP[relation.get_type()]

            source_id = encode_qualified_name(source)
            target_id = encode_qualified_name(target)

            source = self._nodes[source_id]
            target = self._nodes[target_id]

            getattr(source, relation_type).add(target)

    @staticmethod
    def _encode(attributes: Dict[QualifiedName, Any]):
        """Encode dictionary of vertex attributes.

        Convert datetime objects to NeoTime objects.
        Convert qualified names to strings."""
        enc_attributes = {}
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
            enc_attributes[key] = value
        return enc_attributes


if __name__ == "__main__":
    pass
