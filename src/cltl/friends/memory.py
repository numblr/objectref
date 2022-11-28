from typing import Union, Iterable, List, Tuple, Mapping

from cltl.friends.api import FriendStore


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
