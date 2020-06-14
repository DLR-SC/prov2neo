# WIP: prov2neo — Import W3C PROV graphs into Neo4j.
Faster graph imports than comparable libs such as prov-db-connector.  
Implementation is tailored towards the provenance model used by gitlab2prov.  
Therefore it does not serve as a general purpose provenance tool.  
Unlike prov-db-connector, there is no option to retrieve stored documents.  

### Limitations
prov2neo does **not** import Bundles.   

Bundle entities will appear, nodes, bundles and relations within the bundles won't.  
Modeling bundles is no trivial task. There are several translation models from RDF   
Named Graphs to the property graph model employed by Neo4j. Implementing such a   
model remains to future work.

prov2neo has only been tested against **Neo4j 3.5**.  
As of right now (April 2020) it seems that py2neo doesn't support Neo4j 4.x yet.

#### Usage
```python
from prov.model import ProvDocument
from p2n import Importer

graph = ProvDocument()
graph.add_namespace("ex", "https://example.org/")
graph.agent("ex:alice")
graph.agent("ex:bob")

auth = {
    "host": "0.0.0.0:7687", 
    "username": "foo", 
    "password": "bar"}

imp = Importer(auth)
imp.import_graph(graph)
```
