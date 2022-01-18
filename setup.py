import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name='prov2neo',
    version='1.2',
    author='Claas de Boer',
    author_email='claas.deboer@dlr.de',
    packages=['prov2neo'],
    description='Import W3C PROV documents into Neo4j using py2neo\'s OGM.',
    long_description=README,
    long_description_content_type='text/markdown',
    keywords=[
        'w3c prov', 
        'neo4j', 
        'graph import'
    ],
    url='https://github.com/DLR-SC/prov2neo',
    install_requires=[
        'py2neo==2021.2.3', 
        'prov>=2.0.0', 
        'interchange'
    ],
    entry_points={'console_scripts': ['prov2neo = prov2neo.cli:main']},
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
