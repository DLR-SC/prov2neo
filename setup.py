import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name='prov2neo',
    version='0.2',
    author='Claas de Boer',
    author_email='claas.deboer@dlr.de',
    packages=['prov2neo'],
    description='Import W3C PROV graphs into Neo4j using py2neo\'s OGM.',
    keywords=['w3c prov', 'neo4j', 'graph import'],
    url='https://gitlab.dlr.de/provenance/prov2neo',
    install_requires=['py2neo==2021.1.5', 'prov==2.0.0', 'neotime==1.7.4'],
    entry_points={'console_scripts': ['prov2neo = prov2neo.cli:main']},
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Database',
        'Topic :: Database :: Front-Ends',
        ],
    include_package_data=True,

)
