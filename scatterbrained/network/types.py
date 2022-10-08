from typing import Optional, Protocol, Sequence, Tuple


class RX(Protocol):
    @property
    def host(self) -> Optional[str]:
        ...

    @property
    def port(self) -> Optional[int]:
        ...

    async def bind(self, host: str, port: Optional[int] = None) -> int:
        ...

    async def recv(self) -> Tuple[str, Sequence[bytes]]:
        ...

    async def close(self) -> None:
        ...


class TX(Protocol):
    @property
    def host(self) -> Optional[str]:
        ...

    @property
    def port(self) -> Optional[int]:
        ...

    async def connect(self, host: str, port: int) -> None:
        ...

    async def send(self, *segments: bytes) -> None:
        ...

    async def close(self) -> None:
        ...
