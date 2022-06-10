from typing import Union, Iterable, List, Tuple


class FriendStore:
    def add_friend(self, identifier: str, names: Union[str, Iterable[str]],
                   scenario_id: str = None, mention_id: str = None) -> str:
        """
        Add a friend with one or more names and return a URI identifying the friend.
        """
        raise NotImplementedError()

    def get_friend(self, identifier: str) -> Tuple[str, List[str]]:
        """
        Get the URI and names of a friend by identifier.
        """
        raise NotImplementedError()
