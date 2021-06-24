# prov2neo — Import W3C PROV Documents to Neo4j

[![License: MIT](https://img.shields.io/github/license/dlr-sc/gitlab2prov?label=License)](https://opensource.org/licenses/MIT) [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![PyPI version fury.io](https://badge.fury.io/py/prov2neo.svg)](https://pypi.python.org/pypi/prov2neo/) [![Upload Python Package](https://github.com/DLR-SC/prov2neo/actions/workflows/python-publish.yml/badge.svg?branch=main)](https://github.com/DLR-SC/prov2neo/actions/workflows/python-publish.yml) [![DOI](https://zenodo.org/badge/379262717.svg)](https://zenodo.org/badge/latestdoi/379262717)
[![Open in Visual Studio Code](https://open.vscode.dev/badges/open-in-vscode.svg)](https://open.vscode.dev/DLR-SC/prov2neo)

`prov2neo` is a Python library for importing W3C PROV documents into [Neo4j](https://neo4j.com/).  
`prov2neo` enables faster imports than comparable libs such as [`prov-db-connector`](https://github.com/DLR-SC/prov-db-connector).

## Installation

Clone the project and use the provided `setup.py` to install `prov2neo` locally

```bash
python setup.py install --user
```

Or install releases from PyPI:

```bash
pip install prov2neo
```

## Usage

prov2neo can be used both as a command line script and as a Python lib.

### As a Command Line Script

```
usage: prov2neo [-h] [-f {provn,json,rdf,xml}] [-i INPUT [INPUT ...]] [-a ADDRESS]
                [-u USERNAME] [-p PASSWORD] [-n NAME]
                [-s {bolt,bolt+s,bolt+ssc,http,https,http+s,http+ssc}]

Import W3C PROV documents to Neo4j.

optional arguments:
  -h, --help            show this help message and exit
  -f {provn,json,rdf,xml}, --format {provn,json,rdf,xml}
                        input PROV format
  -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                        input files, use '.' for stdin
  -a ADDRESS, --address ADDRESS
                        Neo4j address
  -u USERNAME, --username USERNAME
                        Neo4j username
  -p PASSWORD, --password PASSWORD
                        Neo4j password
  -n NAME, --name NAME  Neo4j target database name
  -s {bolt,bolt+s,bolt+ssc,http,https,http+s,http+ssc}, --scheme {bolt,bolt+s,bolt+ssc,http,https,http+s,http+ssc}
                        connection scheme to use when connecting to Neo4j
```

### As a Python Lib

```python
from prov.model import ProvDocument
from prov2neo.client import Client

# read graph from JSON serialization
graph = ProvDocument.deserialize(source="examples/horsemeat.json", format="json")

# create a prov2neo client
client = Client()
# connect to the neo4j instance
client.connect(
    address="localhost:7687",
    user="jane doe",
    password="**redacted**",
    name="database name",
    scheme="bolt"
)
# import the PROV graph
client.import_graph(graph)
```

prov2neo supports formats that the [`prov`](https://github.com/trungdong/prov) library provides:

* [PROV-N](http://www.w3.org/TR/prov-n/)
* [PROV-O](http://www.w3.org/TR/prov-o/) (RDF)
* [PROV-XML](http://www.w3.org/TR/prov-xml/)
* [PROV-JSON](http://www.w3.org/Submission/prov-json/)

## Contributing

Merge and Pull requests are welcome!  
For major changes, please open an issue first to discuss what you would like to change.

## License

MIT
