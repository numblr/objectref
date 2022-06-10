from pathlib import Path
from typing import Union, Iterable, List

from cltl.brain.infrastructure.rdf_builder import RdfBuilder

from cltl.commons.discrete import UtteranceType
from cltl.combot.infra.time_util import timestamp_now
from cltl.friends.api import FriendStore
from cltl.friends.querying import FriendSearch


class BrainFriendsStore(FriendStore):
    def __init__(self, address, log_dir):
        super().__init__()
        self._rdf_builder = RdfBuilder()
        self._search = FriendSearch(address, log_dir)

    def add_friend(self, identifier: str, names: Union[str, Iterable[str]],
                   scenario_id: str = None, mention_id: str = None) -> str:
        names = [names] if isinstance(names, str) else names
        if not names:
            return

        self._search.capsule_statement(
            self._create_speaker_capsule(scenario_id, mention_id, None, identifier, names[0]),
            create_label=True)
        uri, name = self._search.search_entity_by_face(self._create_uri(identifier))

        for name in names[1:]:
            self._search.capsule_statement(self._create_speaker_capsule(scenario_id, mention_id, uri, identifier, name),
                                           create_label=True)

        return str(uri)

    def get_friend(self, identifier: str) -> List[str]:
        uri, name = self._search.search_entity_by_face(self._create_uri(identifier))

        return str(uri), name

    def _create_uri(self, label):
        return str(self._rdf_builder.create_resource_uri('LW', label.lower()))

    def _create_speaker_capsule(self, scenario_id, mention_id, uri, id_, name):
        return {
            'chat': scenario_id,
            'turn': mention_id,
            'author': {
                'label': 'Leolani',
                'type': ['agent'],
                'uri': None
            },
            'utterance': '',
            'utterance_type': UtteranceType.STATEMENT,
            'position': '',
            'subject': {
                'label': name,
                'type': ['person'],
                'uri': uri
            },
            'predicate': {
                'label': 'faceID',
                'type': ['DatatypeProperty'],
                'uri': "http://cltl.nl/leolani/n2mu/faceID"
            },
            'object': {
                'label': id_,
                'type': ['Literal'],
                'uri': None
            },
            'perspective': {
                'sentiment': 0.0,
                'certainty': 1.0,
                'polarity': 1.0,
                'emotion': 0.0
            },
            'context_id': scenario_id,
            'timestamp': timestamp_now()
        }


if __name__ == '__main__':
    from tempfile import TemporaryDirectory
    from cltl.commons.discrete import UtteranceType

    with TemporaryDirectory(prefix="brain-log") as log_path:
        store = BrainFriendsStore(address="http://localhost:7200/repositories/sandbox",
                                     log_dir=Path(log_path))

        print("1", store.add_friend("face_1", "thomas"))
        friend, name = store.get_friend("face_1")
        print("2", friend, name)