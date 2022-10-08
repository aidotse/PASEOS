from attrs import define, field
from attrs.setters import frozen


@define
class Identity:
    """
    Represents the identity of a scatterbrained.Node
    (either local or remote) for a particular namespace.

    Args:
        id (str): The id of the Node.
        namespace (str): The namespace the Node is operating in.
        host (str): The advertised address of this Node.
        port (int): The advertised port of this Node.
        position (float): The mutable position of the node
    """

    id: str = field(on_setattr=frozen)
    namespace: str = field(on_setattr=frozen)
    host: str = field(on_setattr=frozen)
    port: int = field(on_setattr=frozen)
    position: float

    def __key(self):
        return (self.id, self.namespace, self.host, self.port)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Identity):
            return self.__key() == other.__key()
        return NotImplemented


__all__ = ["Identity"]
