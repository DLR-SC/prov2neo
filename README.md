# WIP: `prov2neo` - Import W3C PROV graphs to Neo4j

`prov2neo` is a Python library for importing W3C PROV graphs into neo4j.  
`prov2neo` enables faster imports than comparable libs such as [`prov-db-connector`](https://github.com/DLR-SC/prov-db-connector).

**Note: Project status is WIP, expect breaking changes!**

## Known Limitations :traffic_light:
- `prov2neo` does not support the import of PROV graphs that miss some node definitions! (See #7 for progress.)

## Installation

Clone the project and use the provided `setup.py` to install `prov2neo`.

```bash
python setup.py install --user
```

## Usage

`prov2neo` can be used both as a command line script and as a Python lib.

#### As a Command Line Script
```
usage: prov2neo [-h] [-f {provn,json,rdf,xml}] [-i INPUT] [-a ADDRESS] [-u USERNAME] [-p PASSWORD] [-n NAME]
                [-s {bolt,bolt+s,bolt+ssc,http,https,http+s,http+ssc}]

Import W3C PROV graphs to neo4j.

optional arguments:
  -h, --help            show this help message and exit
  -f {provn,json,rdf,xml}, --format {provn,json,rdf,xml}
                        input prov format
  -i INPUT, --input INPUT
                        input file, for stdin use '.'
  -a ADDRESS, --address ADDRESS
                        neo4j instance address
  -u USERNAME, --username USERNAME
                        neo4j instance username
  -p PASSWORD, --password PASSWORD
                        neo4j instance password
  -n NAME, --name NAME  neo4j database name
  -s {bolt,bolt+s,bolt+ssc,http,https,http+s,http+ssc}, --scheme {bolt,bolt+s,bolt+ssc,http,https,http+s,http+ssc}
                        connection scheme to use when connecting to neo4j
```

#### As a Python Lib
```python
from prov2neo import Importer
from prov.model import ProvDocument

example = ProvDocument.deserialize(source="examples/horsemeat.json", format="json")
authentication = {
    "address": "localhost:7687",
    "name": "database_name",
    "user": "john doe",
    "password": "**redacted**",
}

importer = Importer()              # create Importer instance
importer.connect(**authentication) # connect to graph database
importer.import_graph(graph)       # import provenance graph
```

## Contributing
Merge and Pull requests are welcome!  
For major changes, please open an issue first to discuss what you would like to change.

## License
TBD