<h1 align="center">Welcome to <code>prov2neo</code>! 👋</h1>
<p align="center">
  <a href="https://github.com/dlr-sc/prov2neo/blob/master/LICENSE">
    <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-yellow.svg" target="_blank" />
  </a>
  <a href="https://img.shields.io/badge/Made%20with-Python-1f425f.svg">
    <img src="https://img.shields.io/badge/Made%20with-Python-1f425f.svg" alt="Badge: Made with Python"/>
  </a>
  <a href="https://pypi.org/project/prov2neo/">
    <img src="https://img.shields.io/pypi/v/prov2neo" alt="Badge: PyPi Version">
  </a>
  <a href="https://pypistats.org/packages/prov2neo">
    <img src="https://img.shields.io/pypi/dm/prov2neo" alt="Badge: PyPi Downloads Monthly">
  </a>
  <a href="https://twitter.com/dlr_software">
    <img alt="Twitter: DLR Software" src="https://img.shields.io/twitter/follow/dlr_software.svg?style=social" target="_blank" />
  </a>
  <a href="https://open.vscode.dev/DLR-SC/prov2neo">
    <img alt="Badge: Open in VSCode" src="https://img.shields.io/static/v1?logo=visualstudiocode&label=&message=open%20in%20visual%20studio%20code&labelColor=2c2c32&color=007acc&logoColor=007acc" target="_blank" />
  </a>
  <a href="https://zenodo.org/badge/latestdoi/379262717">
    <img alt="Badge: DOI" src="https://zenodo.org/badge/379262717.svg" target="_blank" />
  </a>
  <a href="https://www.w3.org/TR/prov-overview/">
    <img alt="Badge: W3C PROV" src="https://img.shields.io/static/v1?logo=w3c&label=&message=PROV&labelColor=2c2c32&color=007acc&logoColor=007acc?logoWidth=200" target="_blank" />
  </a>
  <a href="https://citation-file-format.github.io/">
    <img alt="Badge: Citation File Format Inside" src="https://img.shields.io/badge/-citable%20software-green" target="_blank" />
  </a>
</p>


> `prov2neo` is a Python library and command line tool that imports W3C PROV documents into [Neo4j](https://neo4j.com/).  
> 
> `prov2neo` enables faster imports than comparable libs such as [`prov-db-connector`](https://github.com/DLR-SC/prov-db-connector) with the limitation of being specialized for neo4j.

## 🏗️ Installation

Clone the project and use the provided `setup.py` to install `prov2neo` locally:

```bash
python setup.py install --user
```

Or install the latest release from [PyPi](https://pypi.org/project/prov2neo/):

```bash
pip install prov2neo
```

## 🚀 Usage

prov2neo can be used as a command line script or as a Python lib.

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

## 🤝 Contributing

Contributions and pull requests are welcome!  
For major changes, please open an issue first to discuss what you would like to change.

## ✨ Citable Software 
This project contains a [`CITATION.cff`](https://citation-file-format.github.io/) file!  

`CITATION.cff` files are plain text files with human- and machine-readable citation information for software (and datasets).  
GitHub will link the correct citation automatically.  
To find out more about GitHubs support for `CITATION.cff` files visit [here](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files)  

## 📝 License
Copyright © 2020-2022 [German Aerospace Center (DLR)](https://www.dlr.de/EN/Home/home_node.html) and individual contributors.  
This project is [MIT](https://github.com/dlr-sc/prov2neo/blob/master/LICENSE) licensed.
