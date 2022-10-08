from typing import Awaitable, Callable, Optional, Protocol


class Publisher(Protocol):
    """
    A Publisher is a class that can publish a message to a set of peers.

    Note that this is a protocol and shouldn't be used directly!

    """

    async def publish(self, data: bytes) -> None:
        """
        Publish the given payload to a set of peers.
        """
        ...

    async def open(self) -> None:
        """
        Open the underlying connection mechanism,
        enabling this instance to send messages.
        """
        ...

    async def close(self) -> None:
        """
        Close the underlying connection mechanism,
        stopping this instance from sending messages.
        """
        ...


class Subscriber(Protocol):
    """
    A Subscriber is a class that can subscribe to messages from a set of peers.

    Note that this is a protocol and shouldn't be used directly!

    """

    def subscribe(
        self,
        on_recv: Callable[[bytes], Awaitable[None]],
        on_error: Optional[Callable[[Exception], Awaitable[None]]] = None,
    ) -> None:
        """
        Subscribe to messages from a set of peers, and attach async callbacks.

        Arguments:
            on_recv (Callable[[bytes], Awaitable[None]]):
            The callback to call when a message is received.
            on_error (Optional[Callable[[Exception], Awaitable[None]]]):
            The callback to run when an error occurs.

        Returns:
            None

        """
        ...

    async def open(self) -> None:
        """
        Open the underlying connection mechanism,
        enabling this instance to receive messages.
        """
        ...

    async def close(self) -> None:
        """
        Close the underlying connection mechanism,
        stopping this instance from receiving messages.
        """
        ...


__all__ = ["Publisher", "Subscriber"]
