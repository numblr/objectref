import itertools
from pathlib import Path
from typing import Union, Iterable, List, Tuple, Mapping

from cltl.brain.infrastructure.rdf_builder import RdfBuilder
from cltl.combot.infra.time_util import timestamp_now
from cltl.commons.discrete import UtteranceType

from cltl.friends.api import FriendStore
from cltl.friends.querying import FriendSearch


class MemoryFriendsStore(FriendStore):
    def __init__(self):
        super().__init__()
        self._friends = dict()

    def add_friend(self, identifier: str, names: Union[str, Iterable[str]],
                   scenario_id: str = None, mention_id: str = None) -> str:
        self._friends[identifier] = (None, names)

        return None

    def get_friend(self, identifier: str) -> Tuple[str, List[str]]:
        return self._friends[identifier]

    def get_friends(self) -> Mapping[str, Tuple[str, List[str]]]:
        return dict(self._friends)

    def get_identifieres(self) -> List[str]:
        return self.get_friends().keys()
