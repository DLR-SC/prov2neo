import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="prov2neo",
    version="0.1",
    author="Claas de Boer",
    author_email="claas.deboer@dlr.de",
    packages=find_packages(),
    description="Import W3C PROV graphs into Neo4j using py2neo's OGM.",
    keywords=["w3c prov", "neo4j", "graph import"],
    install_requires=["py2neo==5.0b1", "prov==1.5.3", "neotime==1.7.4"],
    entry_points={"console_scripts": ["prov2neo = prov2neo.cli:main"]}
)