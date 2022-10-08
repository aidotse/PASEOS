import asyncio
from typing import Awaitable, Callable, Optional, Tuple

import rx
from loguru import logger
from rx import operators as op
from rx.scheduler.eventloop import AsyncIOScheduler
from rx.subject import Subject


class _UDPBroadcastProtocol:
    def connection_made(self, transport: asyncio.DatagramTransport):
        self.transport = transport

    def connection_lost(self, exc: Exception):
        # TODO: determine how to inform larger
        # TODO: program about any exceptions passed.
        self.transport = None

    def error_received(self, exc: OSError):
        # TODO: determine how to inform larger
        # TODO: program about any exceptions passed.
        pass


class _UDPRecvProtocol:
    def __init__(self, subject: Optional[Subject] = None):
        if subject is None:
            subject = Subject()
        self.subject = subject

    def connection_made(self, transport: asyncio.DatagramTransport):
        self.transport = transport

    def connection_lost(self, exc: Exception):
        self.transport = None
        if exc is None:
            self.subject.on_completed()
        else:
            self.subject.on_error(exc)

    def error_received(self, exc: OSError):
        self.subject.on_error(exc)

    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        self.subject.on_next((data, addr))


class UDPBroadcaster:
    remote: str
    port: int
    _transport: Optional[asyncio.DatagramTransport]
    _protocol: Optional[asyncio.DatagramProtocol]

    def __init__(self,
                 broadcast_addr: str = "255.255.255.255",
                 port: int = 9001):
        self.broadcast_addr = broadcast_addr
        self.port = port
        self._transport = None
        self._protocol = None

    async def open(self) -> None:
        if self._transport is None:
            loop = asyncio.get_running_loop()
            self._transport, self._protocol = \
                await loop.create_datagram_endpoint(
                    lambda: _UDPBroadcastProtocol(),
                    remote_addr=(self.broadcast_addr, self.port),
                    allow_broadcast=True,
                )

    async def close(self) -> None:
        if self._transport is not None:
            self._transport.close()
            self._transport = None
            self._protocol = None

    async def __aenter__(self) -> None:
        await self.open()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def publish(self, data: bytes) -> None:
        if self._transport is None:
            raise RuntimeError("socket is not open")
        self._transport.sendto(data)


class UDPReceiver:
    source: str
    port: int
    _transport: Optional[asyncio.DatagramTransport]
    _protocol: Optional[asyncio.DatagramProtocol]

    def __init__(
        self,
        local_addr: str = "",
        port: int = 9001,
        subject: Optional[Subject] = None
    ):
        if subject is None:
            subject = Subject()
        self.local_addr = local_addr
        self.port = port
        self.subject = subject
        self._transport = None
        self._protocol = None

    async def open(self) -> None:
        if self._transport is None:
            loop = asyncio.get_running_loop()
            self._transport, self._protocol = \
                await loop.create_datagram_endpoint(
                    lambda: _UDPRecvProtocol(subject=self.subject),
                    local_addr=(self.local_addr, self.port),
                )

    async def close(self) -> None:
        if self._transport is not None:
            self._transport.close()
            self._transport = None
            self._protocol = None

    async def __aenter__(self) -> None:
        await self.open()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    def subscribe(
        self,
        on_recv: Callable[[bytes], Awaitable[None]],
        on_error: Optional[Callable[[Exception], Awaitable[None]]] = None,
    ):
        def handle_next(obj):
            data, _ = obj
            return rx.from_future(asyncio.create_task(on_recv(data)))

        def handle_error(ex, src):
            assert on_error is not None  # nosec
            return rx.from_future(asyncio.create_task(on_error(ex)))

        workflow = self.subject.pipe(op.flat_map(handle_next))
        if on_error is not None:
            workflow = workflow.pipe(op.catch(handle_error))

        d = workflow.subscribe(
            on_next=lambda _: logger.trace("message processed"),
            on_error=lambda e: logger.opt(exception=e).error(
                f"{type(self).__name__} data stream error"
            ),
            on_completed=lambda: logger.trace(
                f"{type(self).__name__} data stream ended"
            ),
            scheduler=AsyncIOScheduler(loop=asyncio.get_running_loop()),
        )

        return d


__all__ = ["UDPBroadcaster", "UDPReceiver"]
