from collections import Counter, defaultdict, deque
from datetime import date, datetime, time, timedelta

from neotime import DateTime, Duration, Time
from prov.constants import PROV_N_MAP
from prov.identifier import Identifier, QualifiedName
from prov.model import (
    Literal,
    ProvActivity,
    ProvAgent,
    ProvBundle,
    ProvDocument,
    ProvElement,
    ProvEntity,
    ProvRelation
)
from py2neo import Subgraph
from py2neo.data import Node, Relationship


# constant strings
PROV_ACTIVITY = "Activity"
PROV_AGENT = "Agent"
PROV_BUNDLE = "Bundle"
PROV_ENTITY = "Entity"
PROV_TYPE = "prov:type"
PROV2NEO_ID = "prov2neo:identifier"
PROV2NEO_LABEL = "prov2neo:label"
PROV2NEO_BUNDLED_IN = "prov2neo:bundledIn"


# constant tuples
PROV2NEO_NODE = (PROV2NEO_LABEL, "prov2neo:node")
PROV2NEO_EDGE = (PROV2NEO_LABEL, "prov2neo:edge")


# constant mappings
EDGE_LABELS = PROV_N_MAP
NODE_LABELS = {
    ProvActivity: PROV_ACTIVITY,
    ProvAgent: PROV_AGENT,
    ProvBundle: PROV_BUNDLE,
    ProvEntity: PROV_ENTITY,
}


def str_id(qualified_name):
    """Return PROVN representation of a URI qualified name.

    Params
    ------
    qualified_name : QualifiedName
        Qualified name for which to return the PROVN
        string representation.
    """
    return qualified_name.provn_representation().replace("'", "")


def edge_label(edge):
    """Return PROVN edge label string for a given edge.

    Params
    ------
    edge : ProvRelation
        Provenance relation for which to return the
        appropriate PROVN label.
    """
    return EDGE_LABELS[edge.get_type()]


def node_label(node):
    """Return PROVN node label string for a given node.

    Params
    ------
    node : ProvActivity, ProvAgent, ProvEntity, ProvBundle
        Provenance node for which to return the
        appropriate PROVN label.
    """
    return NODE_LABELS[type(node)]


def NodePropertySet(node=None, qualified_name=None):
    """Set store for node property tuples.

    Used to store the properties of a PROV graph node.

    A simple set suffices to store the properties,
    as sets allow to store multi-valued key-value tuple.

    Before casting to a py2neo Node, the property set has
    to be turned into a dictionary. The conversion is
    implemented in 'to_property_dict'. Examples of how
    a property set maps to a property dict are listed below.

    Multi-valued property example:
        NodePropertySet := {
            ('foo', 'b'),
            ('foo', 'a'),
            ('foo', 'r')
        }
        PropertyDict    := {'foo': ['b', 'a', 'r']}

    Single-valued property example:
        NodePropertySet := {('foo', 'bar')}
        PropertyDict    := {'foo': 'bar'}

    One property tuple is included in each NodePropertySet:
        - The tuple ("prov:type", "prov2neo:node") is used
          as a primary key for merging nodes into neo4j.
          This tuple always exists, even for otherwise
          empty nodes.

    Two more are sourced from a PROV element that can be passed
    as a parameter:
        - The tuple ("", node_type) is used to denote the type
          of PROV element that the node represents/has been
          sourced from
        - The tuple ("", node_identifier) is used as a unique
          identifier for each node. The identifier is also used
          in the clients implementation of merging nodes into
          neo4j

    [Note]
    I have decided against subclassing any Set implementations
    such as collections.abc.Set or others. This may change
    in the future and the NodePropertySet may become its own class.

    Params
    ------
    node : Optional[Union[ProvActivity, ProvAgent, ProvEntity]]
        The PROV element to source data (properties) from.
    qualified_name : Optional[QualifiedName]
        The qualified name of the empty node that the set is
        supposed to represent.
    """
    if node is None and qualified_name is None:
        # this should be avoided at all cost
        # as every node needs to have a property value for
        # PROV2NEO_ID to be succesfully merged into neo4j
        return {PROV2NEO_NODE}
    if node is None:
        return {PROV2NEO_NODE, (PROV2NEO_ID, str_id(qualified_name))}
    properties = {} if type(node) is ProvBundle else node.attributes
    ident = (PROV2NEO_ID, str_id(node.identifier))
    label = (PROV2NEO_LABEL, node_label(node))
    return {PROV2NEO_NODE, label, ident, *properties}


def EdgePropertySet(edge=None):
    """Set store for edge property tuples.

    Used to store the properties of a PROV graph node.

    A simple set suffices to store the properties,
    as sets allow to store multi-valued key-value tuple.

    One property tuple is included in each EdgePropertySet:
        - The tuple ("prov:type", "prov2neo:edge") denoting
          that the relationship encodes an edge in the PROV
          graph

    One more tuple is included when data can be sourced
    from a PROV relation:
        - The tuple ("prov:type", edge_type) is used to
          encode the type of edge/relationship that the
          edge represents

    Before being cast to a py2neo Relationship the property set
    needs to be turned into a dictionary. The conversion is
    the same as for the NodePropertySet and is ipmlemented in
    'to_property_dict'.

    [Note]
    I have decided against subclassing any Set implementations
    such as collections.abc.Set or others. This may change
    in the future and the NodePropertySet may become its own class.

    Params
    ------
    edge : Optional[ProvRelation]
        The PROV relation to source data (properties) from.
    """
    if edge is None:
        return {PROV2NEO_EDGE}
    label = (PROV2NEO_LABEL, edge_label(edge))
    properties = [*edge.attributes[2:], *edge.extra_attributes]
    return {PROV2NEO_EDGE, label, *properties}


def encode_value(value):
    """Encode a property value as a neo4j (py2neo) primitive.

    Params
    ------
    value : Any
        The value to be encoded.
    """
    if type(value) in (QualifiedName, Identifier):
        return str(value)
    elif type(value) is Literal:
        return value.provn_representation()
    elif type(value) in (date, datetime):
        return DateTime.from_native(value)
    elif type(value) is time:
        return Time.from_native(value)
    elif type(value) is timedelta:
        return Duration(seconds=value.total_seconds())
    return value


def encode_graph(graph):
    """Encode a PROV graph (ProvDocument) as a collection of
    py2neo Nodes and Relationships (Subgraph).

    Params
    ------
    graph : ProvDocument
        The PROV graph to be encoded.
    """
    nodes = encode_nodes(graph)
    edges = encode_edges(graph, nodes)
    edges.extend(encode_bundle_edges(graph, nodes))
    return Subgraph(nodes.values(), edges)


def get_graph_nodes(graph):
    """Return a list containing the nodes of a PROV graph.

    Explore the graph using BFS level by level.
    Expand bundles and add bundle nodes to the queue.
    A collections.deque is used as queue.

    Bundles are included in the returned nodes.
    Notice that while not all bundles are PROV elements
    the ones that are are PROV entities.
    Most of the time, the declaration for the entity part
    and the bundle part are stored in two different PROV
    elements.

    Params
    ------
    graph : ProvDocument
        The PROV graph to source the list of nodes from.
    """
    nodes = []
    q = deque([graph.get_records(ProvElement), graph.bundles])
    while q:
        current_bfs_level = q.popleft()
        for item in current_bfs_level:
            nodes.append(item)
            if type(item) is ProvBundle:
                q.append(item.get_records(ProvElement))
                q.append(item.bundles)
    return nodes


def get_graph_edges(graph):
    """Return a list containing the edges of a PROV graph.

    Flatten the graph and return its records filtered for
    edges (ProvRelations).

    Params
    ------
    graph : ProvDocument
        The PROV graph to source the list of edges from.
    """
    flattened = graph.flattened()
    return list(flattened.get_records(class_or_type_or_tuple=ProvRelation))


def encode_nodes(graph):
    """Encode the nodes of a PROV graph as py2neo Nodes.
    Return a mapping from node id to py2neo Node.

    Create a NodePropertySet for each PROV type contained
    in the list of nodes provided by 'get_graph_nodes'.

    RDF allows literal values to be the endpoint of relations.
    As these literals do not represent nodes themselves, we
    turn those relationships into node properties as follows:

    From:
    (Node) -{relation}-> Literal

    To:
    (Node {relation: Literal})

    Finally the computed NodePropertySets are cast to py2neo
    nodes using the 'to_py2neo_node' function before returning
    the mapping from node ids to py2neo nodes.

    Params
    ------
    graph : ProvDocument
        The PROV graph for which to encode the nodes.
    """
    nodes = {}

    for node in get_graph_nodes(graph):
        nodes[str_id(node.identifier)] = NodePropertySet(node)

    for edge in get_graph_edges(graph):
        (_, source) = edge.formal_attributes[0]
        (_, target) = edge.formal_attributes[1]
        # create source node if it doesn't exist
        source_id = str_id(source)
        if source_id not in nodes:
            nodes[source_id] = NodePropertySet(qualified_name=source)

        # handle edges of type: (Node) -relation-> Literal
        if type(target) is not QualifiedName:
            key = edge_label(edge)
            val = encode_value(target)
            nodes[source_id].update({(key, val)})
            continue

        # create target node if it doesn't exist
        target_id = str_id(target)
        if target_id not in nodes:
            nodes[target_id] = NodePropertySet(qualified_name=target)

    # convert property sets to py2neo nodes
    for node_id, node_property_set in list(nodes.items()):
        nodes[node_id] = to_py2neo_node(node_property_set)
    return nodes


def to_property_dict(property_set):
    """Turn a property set into a dict of properties.

    Examples of how a property set maps to a property
    dict are listed below.

    Multi-valued property example:
        NodePropertySet := {
            ('foo', 'b'),
            ('foo', 'a'),
            ('foo', 'r')
        }
        PropertyDict    := {'foo': ['b', 'a', 'r']}

    Single-valued property example:
        NodePropertySet := {('foo', 'bar')}
        PropertyDict    := {'foo': 'bar'}

    Params
    ------
    property_set : set
        The property set to convert to a dictonary of properties.
    """
    # encode the set of properties
    encoded_property_set = [tuple(map(encode_value, item))
                            for item in property_set]

    # count the occurence of each property key
    key_count = Counter(key for key, _ in encoded_property_set)

    property_dict = defaultdict(list)
    for (key, value) in encoded_property_set:
        # property is 'single-valued' iff
        # the property key occurs only once
        if key_count.get(key) == 1:
            property_dict[key] = value
        # property is 'multi-valued'
        # iff the property key occurs more than once

        # values of a 'multi-valued' property
        # are stored in a list
        else:
            property_dict[key].append(value)
    return property_dict


def to_py2neo_node(property_set):
    """Turn a property set into a py2neo Node.

    First convert the property set into a property dict.
    Then extract the node labels from the dict.
    Node labels are the values stored at the key 'prov:type'.

    Params
    ------
    property_set : set
        The property set to be turned into a py2neo Node
    """
    property_dict = to_property_dict(property_set)
    # get node labels, key PROV2NEO_LABEL
    labels = property_dict[PROV2NEO_LABEL]
    # delete the key PROV2NEO_LABEL
    del property_dict[PROV2NEO_LABEL]
    if type(labels) is not list:
        return Node(labels, **property_dict)
    return Node(*labels, **property_dict)


def encode_edges(graph, nodes):
    """Encode the edges of a PROV graph as py2neo Relationships (edges).
    Returns a list of py2neo Relationships.

    Encode the attributes of each edge as an EdgePropertySet.
    Turn the property set into a property dict.
    Create the py2neo relationship and add it to the list of edges.

    Ignore/Skip edges that connect a node to a literal, as these have
    been handled in the node encoding already.

    Use the provided mapping from node ids to py2neo Nodes as a
    lookup for source and target nodes of each created edge.

    Params
    ------
    graph : ProvDocument
        The PROV graph for which to encode the edges as py2neo Relationships
    nodes : dict
        A mapping from node id to py2neo nodes used as a lookup for
        source and target nodes of graph edges/relationships.
    """
    edges = []
    for edge in get_graph_edges(graph):
        (_, source) = edge.formal_attributes[0]
        (_, target) = edge.formal_attributes[1]

        if type(target) is QualifiedName:
            source = nodes[str_id(source)]
            target = nodes[str_id(target)]

            label = edge_label(edge)
            properties = EdgePropertySet(edge)
            encoded_properties = to_property_dict(properties)

            relation = Relationship(
                source, label, target, **encoded_properties)
            edges.append(relation)
    return edges


def encode_bundle_edges(graph, nodes):
    """Return a list of 'bundledIn' edges between each bundle node
    and the nodes included within the bundle.

    This is how we model the bundle inclusion of a node.
    If a node (A) is included in a bundle that is encoded in node (B),
    a relationship/edge of type 'bundledIn' is created between the two.

    (B) -[bundledIn]-> (A)

    This allows to retrieve the nodes that are included in a specific bundle
    with a simple cypher query.

    Params
    ------
    graph : ProvDocument
        The PROV graph for which to return the list of bundle eges.
    nodes : dict
        A mapping from node ids to py2neo nodes, used as a node lookup
        for source and target nodes of edges/relationships.
    """
    edges = []
    for node in get_graph_nodes(graph):
        # skip bundles as ProvBundle.bundle would raise an AttributeError
        # skip documents for the same reason
        if type(node) in (ProvBundle, ProvDocument):
            continue

        if type(node.bundle) is ProvBundle:
            n_id = str_id(node.identifier)
            b_id = str_id(node.bundle.identifier)

            source = nodes[n_id]
            target = nodes[b_id]

            relation = Relationship(source, PROV2NEO_BUNDLED_IN, target)
            edges.append(relation)
    return edges
