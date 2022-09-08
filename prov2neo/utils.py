from prov.model import ProvDocument


def read_doc(filepath):
    for format in ["json", "rdf", "xml"]:
        try:
            return ProvDocument.deserialize(source=filepath, format=format)
        except:
            continue
    raise Exception


def write_doc(doc, filepath, format):
    raise NotImplementedError
