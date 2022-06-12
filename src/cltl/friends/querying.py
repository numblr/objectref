from pathlib import Path

import importlib_resources as pkg_resources
import rdflib
from cltl.brain.long_term_memory import LongTermMemory

import cltl.friends


def read_query(query_filename):
    """
    Read a query from file and return as a string
    Parameters
    ----------
    query_filename: str name of the query. It will be looked for in the queries folder of this project

    Returns
    -------
    query: str the query with placeholders for the query parameters, as a string to be formatted

    """
    resources = pkg_resources.files(cltl.friends)

    return (resources / f"{query_filename}.rq").read_text()


class FriendSearch(LongTermMemory):
    def __init__(self, address, log_dir):
        super().__init__(address, log_dir)

    def search_entity_by_face(self, id):
        query = read_query('./queries/face') % id
        response = self._submit_query(query)
        if response:
            return response[0]['person']['value'], [entity['name']['value'] for entity in response]
        else:
            return None, None

    def create_uri(self, label):
        return str(self._rdf_builder.create_resource_uri('LW', label.lower()))

if __name__ == '__main__':
    from tempfile import TemporaryDirectory
    from cltl.commons.discrete import UtteranceType

    with TemporaryDirectory(prefix="brain-log") as log_path:
        entity_search = FriendSearch(address="http://localhost:7200/repositories/sandbox",
                                     log_dir=Path(log_path))

        capsule = {
            'chat': "chat_1",
            'turn': "mention_1",
            'author': {
                'label': 'Leolani',
                'type': ['agent'],
                'uri': "http://cltl.nl/leolani/world/leolani"
            },
            'utterance': '',
            'utterance_type': UtteranceType.STATEMENT,
            'position': '',
            'subject': {
                'label': "Thomas",
                'type': ['person'],
                'uri': "http://cltl.nl/leolani/world/carl"
            },
            'predicate': {
                'label': "faceID",
                'type': ['DatatypeProperty'],
                'uri': "http://cltl.nl/leolani/n2mu/faceID"
            },
            'object': {
                'label': "face_1",
                'type': ['Literal'],
                'uri': None
            },
            'perspective': {
                'sentiment': 0.0,
                'certainty': 1.0,
                'polarity': 1.0,
                'emotion': 0.0
            },
            'context_id': "chat_1",
            'timestamp': 1
        }

        entity_search.capsule_statement(capsule, create_label=True)
        print(entity_search.get_triples_with_predicate("http://cltl.nl/leolani/n2mu/faceID"))
        print(entity_search.search_entity_by_face(entity_search.create_uri("face_1")))

