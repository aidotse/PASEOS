from __future__ import annotations

import asyncio
import attrs
from typing import Awaitable, Callable, Dict, Optional, Sequence, Tuple

import orjson
import rx
from loguru import logger
from rx import operators as op
from rx.scheduler.eventloop import AsyncIOScheduler
from rx.subject import Subject

from ..types import Identity
from .types import RX, TX


class NetworkEngine:
    class Disposable:
        engine: NetworkEngine
        rx_disposable: rx.disposable.Disposable
        _disposed: bool

        def __init__(
            self, engine: NetworkEngine,
            rx_disposable: rx.disposable.Disposable
        ):
            self.engine = engine
            self.rx_disposable = rx_disposable
            self._disposed = False

        async def dispose(self) -> None:
            if self._disposed:
                return

            self.rx_disposable.dispose()
            self.engine._sub_count -= 1
            if self.engine._sub_count == 0:
                # Need to be careful about concurrency here.
                # To prevent race conditions, we save/clear the rx_task
                # field, cancel the saved task, and then await on it.
                # This ensures that if someone subscribes while the
                # task is being awaited it starts the rx loop back up.
                task = self.engine._rx_task
                self.engine._rx_task = None
                # Need to check this in case the NetworkEngine
                # instance was unbound/closed.
                if task is not None:
                    task.cancel()
                    await task

    _tx_factory: Callable[[], TX]
    _rx: RX
    _physical_tx_connections: Dict[Tuple[str, int], TX]
    _bound: bool
    _subject: Subject
    _rx_task: Optional[asyncio.Task]
    _sub_count: int

    def __init__(self, rx: RX, tx_factory: Callable[[], TX]):
        self._rx = rx
        self._tx_factory = tx_factory
        self._physical_tx_connections = {}
        self._bound = False
        self._subject = Subject()
        self._rx_task = None
        self._sub_count = 0

    @property
    def bound_address(self):
        return self._rx.host, self._rx.port

    async def bind(self, host: str, port: Optional[int] = None) -> int:
        port = await self._rx.bind(host, port)
        self._bound = True
        return port

    async def unbind(self) -> None:
        if self._rx_task is not None:
            self._rx_task.cancel()
            await self._rx_task
            self._rx_task = None
        await self._rx.close()
        self._bound = False

    async def close(self) -> None:
        keys = list(self._physical_tx_connections)
        for k in keys:
            tx = self._physical_tx_connections.pop(k)
            await tx.close()
        await self.unbind()

    async def connect_to(self, host: str, port: int) -> None:
        phy_conn_info = (host, port)
        if phy_conn_info not in self._physical_tx_connections:
            tx = self._tx_factory()
            await tx.connect(host, port)

            self._physical_tx_connections[phy_conn_info] = tx

    async def disconnect_from(self, host: str, port: int) -> None:
        phy_conn_info = (host, port)
        if phy_conn_info in self._physical_tx_connections:
            tx = self._physical_tx_connections.pop(phy_conn_info)
            await tx.close()

    async def send_to(self,
                      id: Identity,
                      peer: Identity,
                      *payload: bytes) -> None:
        phy_conn_info = (peer.host, peer.port)
        if phy_conn_info not in self._physical_tx_connections:
            raise RuntimeError(
                f"not connected to peer node '{peer.id}' \
                    (addr={peer.host}:{peer.port})"
            )

        tx = self._physical_tx_connections[phy_conn_info]
        idbytes = orjson.dumps(attrs.asdict(id))
        await tx.send(idbytes, *payload)

    async def _rx_loop(self) -> None:
        logger.debug(f"{type(self).__name__} RX loop is starting")
        try:
            while True:
                peer_id, segments = await self._rx.recv()
                try:
                    identity = orjson.loads(segments[0])
                    identity = Identity(**identity)
                except Exception:
                    logger.exception(
                        f"failed extract identity in message from '{peer_id}'"
                    )
                    self._subject.on_next((True, (peer_id, segments)))
                else:
                    self._subject.on_next((False, (identity, segments[1:])))
        except asyncio.CancelledError:
            logger.debug(f"{type(self).__name__} RX loop is shutting down")
            pass
        except Exception as e:
            logger.exception(f"error in {type(self).__name__} RX loop")
            self._subject.on_error(e)

    def subscribe(
        self,
        on_recv: Callable[[Identity, Sequence[bytes]], Awaitable[None]],
        on_malformed: Callable[[str, Sequence[bytes]], Awaitable[None]],
        on_error: Optional[Callable[[Exception], Awaitable[None]]] = None,
    ):
        if not self._bound:
            raise RuntimeError(
                f"{type(self).__name__} must bound before subscribe is called"
            )

        def handle_next(data):
            malformed, payload = data
            if malformed:
                return rx.from_future(
                    asyncio.create_task(
                        on_malformed(*payload)))
            else:
                return rx.from_future(
                    asyncio.create_task(
                        on_recv(*payload)))

        def handle_error(ex, src):
            assert on_error is not None  # nosec
            return rx.from_future(asyncio.create_task(on_error(ex)))

        workflow = self._subject.pipe(op.flat_map(handle_next))
        if on_error is not None:
            workflow = workflow.pipe(op.catch(handle_error))

        d = workflow.subscribe(
            on_next=lambda _: logger.trace("message processed"),
            on_error=lambda e: logger.opt(exception=e).error(
                "network engine data stream error"
            ),
            on_completed=lambda:
                logger.trace("network engine data stream ended"),
            scheduler=AsyncIOScheduler(loop=asyncio.get_running_loop()),
        )

        if self._rx_task is None:
            self._rx_task = asyncio.create_task(self._rx_loop())
        self._sub_count += 1

        return self.Disposable(self, d)
