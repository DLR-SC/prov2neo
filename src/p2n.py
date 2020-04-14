from collections import namedtuple
from datetime import date, datetime, time, timedelta

from neotime import DateTime, Duration, Time
from prov.identifier import QualifiedName
from prov.model import (ProvActivity, ProvAgent, ProvDocument, ProvElement,
                        ProvEntity, ProvRelation)
from py2neo import Graph
from py2neo.ogm import GraphObject, Property, Related


PROV_RELATIONS = {
    "Attribution":    "wasAttributedTo",
    "Association":    "wasAssociatedWith",
    "Derivation":     "wasDerivedFrom",
    "Communication":  "wasInformedBy",
    "Start":          "wasStartedBy",
    "Usage":          "used",
    "End":            "wasEndedBy",
    "Invalidation":   "wasInvalidatedBy",
    "Generation":     "wasGeneratedBy",
    "Specialization": "specializationOf",
    "Alternate":      "alternateOf",
    "Membership":     "hadMember",
    "Delegation":     "delegation",
    "Mention":        "mentionOf",
    "Influence":      "wasInfluencedBy",
    "Revision":       "wasRevisionOf",
    "Quotation":      "wasQuotedFrom"
}


def import_graph(auth, graph):
    spawn_templates(max_key_sets(graph))
    n4j = connect(auth)
    for node in nodes(graph):
        n4j.push(node)
    return


def max_key_sets(graph):
    MaxKeySets = namedtuple("MaximumKeySets", "activity agent entity")
    activity = agent = entity = set()
    for element in graph.flattened().get_records(ProvElement):
        for key, _ in element.attributes:
            if isinstance(element, ProvActivity):
                activity.add(f"{key.namespace.prefix}:{key.localpart}")
            elif isinstance(element, ProvAgent):
                agent.add(f"{key.namespace.prefix}:{key.localpart}")
            elif isinstance(element, ProvEntity):
                entity.add(f"{key.namespace.prefix}:{key.localpart}")
    return MaxKeySets(activity, agent, entity)


def spawn_templates(max_key_sets):
    globals()["Activity"] = create_template("Activity", max_key_sets.activity)
    globals()["Agent"]    = create_template("Agent",    max_key_sets.agent)
    globals()["Entity"]   = create_template("Entity",   max_key_sets.entity)
    return


def create_template(class_name, keys):
    "Construct GraphObject class definitions dynamically"
    attributes = dict()
    keys.update(["id", "prov:type"])
    for key in keys:
        attributes[key] = Property(key)
    for relation in PROV_RELATIONS.values():
        attributes[relation] = Related(GraphObject, relation)
    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    attributes["__init__"] = __init__
    attributes["__primarykey__"] = "id"
    new_class = type(class_name, (GraphObject,), attributes)
    return new_class


def connect(auth):
    print(auth)
    n4j = Graph(f"bolt://{auth['host']}/", user=auth["username"], password=auth["password"])
    print(n4j)
    n4j.schema.create_uniqueness_constraint("Activity", "id")
    n4j.schema.create_uniqueness_constraint("Agent",    "id")
    n4j.schema.create_uniqueness_constraint("Entity",   "id")
    return n4j


def nodes(graph):
    nodes = dict()

    for element in set(graph.flattened().get_records(ProvElement)):
        raw_id = element.identifier
        encoded_id = f"{raw_id.namespace.prefix}:{raw_id.localpart}"
        encoded_attributes = {"id": encoded_id}
        encoded_attributes.update(encode(element.attributes))
        # choose template according to element type
        if isinstance(element, ProvActivity):
            graph_obj = Activity
        elif isinstance(element, ProvAgent):
            graph_obj = Agent
        elif isinstance(element, ProvEntity):
            graph_obj = Entity
        nodes[encoded_id] = graph_obj(**encoded_attributes)

    for relation in set(graph.flattened().get_records(ProvRelation)):
        source, target, *_ = tuple(relation.formal_attributes)
        relation_type = PROV_RELATIONS[relation.get_type().localpart]

        source_id = f"{source[1].namespace.prefix}:{source[1].localpart}"
        target_id = f"{target[1].namespace.prefix}:{target[1].localpart}"

        source = nodes[source_id]
        target = nodes[target_id]
        getattr(source, relation_type).update(target)

    for bundle in graph.bundles:
        # TODO: layered bundles, entities for contained bundles
        bundle_id = f"{bundle.identifier.namespace.prefix}:{bundle.identifier.localpart}"
        nodes[bundle_id] = Entity(**{"id": bundle_id, "prov:type": "bundle"})
        for element in bundle.get_records(ProvElement):
            raw_id = element.identifier
            encoded_id = f"{raw_id.namespace.prefix}:{raw_id.localpart}"
            source = nodes[encoded_id]
            target = nodes[bundle_id]
            getattr(source, "wasAttributedTo").update(target)

    return nodes.values()


def encode(attributes):
    for key, value in attributes:
        if isinstance(key, QualifiedName):
            key = f"{key.namespace.prefix}:{key.localpart}"
        if isinstance(value, QualifiedName):
            value = f"{value.namespace.prefix}:{value.localpart}"
        elif isinstance(value, (date, datetime)):
            value = DateTime.from_iso_format(value.isoformat())
        elif isinstance(value, time):
            value = Time.from_iso_format(value.isoformat())
        elif isinstance(value, timedelta):
            value = Duration(seconds=value.total_seconds())
        yield key, value


if __name__ == "__main__":
    pass
