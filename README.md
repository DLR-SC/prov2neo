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
 
--- 

`prov2neo` enables faster imports than comparable libs such as [`prov-db-connector`](https://github.com/DLR-SC/prov-db-connector) with the limitation of being specialized for neo4j.

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
Usage: prov2neo [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

  Connect to a neo4j instance and import/export provenance documents.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  connect  Connect to a neo4j instance.
  export   (Deprecated) Export a provenance document from neo4j.
  import   Import a provenance document into neo4j.
```

### As a Python Lib

```python
from prov2neo import Client, read_doc

doc = read_doc(filepath="examples/horsemeat.json")

# create a client
client = Client()
# connect to your neo4j instance
client.connect(
    username="neo4j",
    password="neo4j",
    dbname="neo4j",
    address="localhost:7687",
    scheme="bolt"
)
# import the document
client.import_doc(doc)
```
### Supported Formats 

`prov2neo` supports all deserialization formats supported by the [`prov`](https://github.com/trungdong/prov) library.
Deserialization and with it the import of documents through the command line tool is limited to the following formats:

* [PROV-O](http://www.w3.org/TR/prov-o/) (RDF)
* [PROV-XML](http://www.w3.org/TR/prov-xml/)
* [PROV-JSON](http://www.w3.org/Submission/prov-json/)

## 🤝 Contributing

Contributions and pull requests are welcome!  
For major changes, please open an issue first to discuss what you would like to change.

## ✨ Citable Software 

This project is citable and contains a [`CITATION.cff`](https://citation-file-format.github.io/) file!  
Please cite the project using the metadata contained in the `CITATION.cff` if you use `prov2neo` in your research.

`CITATION.cff` files are plain text files with human- and machine-readable citation information for software (and datasets).  
To find out more about GitHub's support for citation metadata visit [here](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files)  

## 📝 License

This project is [MIT](https://github.com/dlr-sc/prov2neo/blob/master/LICENSE) licensed.  
Copyright © 2020-2022 [German Aerospace Center (DLR)](https://www.dlr.de/EN/Home/home_node.html) and individual contributors.  
