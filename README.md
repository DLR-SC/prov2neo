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
Support for Neo4j below Version 4.0 is available on its own branch.

#### Command Line Usage
```
usage: prov2neo [-h] [-f {provn,json,rdf,xml}] -i INPUT [-H HOST] [-u USERNAME] [-p PASSWORD]

Import W3C PROV graphs to neo4j.

optional arguments:
  -h, --help            show this help message and exit
  -f {provn,json,rdf,xml}, --format {provn,json,rdf,xml}
                        input prov format
  -i INPUT, --input INPUT
                        input file, for stdin use '.'
  -H HOST, --host HOST  neo4j instance host
  -u USERNAME, --username USERNAME
                        neo4j instance username
  -p PASSWORD, --password PASSWORD
                        neo4j instance password
```

#### Lib Usage
```python
from prov.model import ProvDocument
from prov2neo.core import Importer

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
