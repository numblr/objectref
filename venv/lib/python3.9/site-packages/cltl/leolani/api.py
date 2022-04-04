import abc


class Leolani(abc.ABC):
    def respond(self, statement: str) -> str:
        raise NotImplementedError("")
