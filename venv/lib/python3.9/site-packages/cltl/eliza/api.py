import abc


class Eliza(abc.ABC):
    def respond(self, statement: str) -> str:
        raise NotImplementedError("")
