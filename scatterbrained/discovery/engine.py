"""
The Discovery Engine is responsible for discovering and
managing nodes on the Scatterbrained network.
"""

import asyncio
import attrs
from datetime import datetime
from typing import Awaitable, Callable, Dict, Optional, Sequence, Set, Tuple

import orjson
import rx

from ..types import Identity
from .types import Publisher, Subscriber


class DiscoveryEngine:
    """
    A `DiscoveryEngine` is a manager class for the process of identifying
    and communicating with other peers in the Scatterbrained network.

    The `DiscoveryEngine` is responsible for maintaining a list
    of peers, and periodically sending heartbeats to the network,
    which other peers can use to determine if the sending node is still alive.

    Identities of peers are stored in `DiscoveryEngine.peers`.

    Identities of the current node are stored in
    `DiscoveryEngine.identities` and can be manually added or
    removed using `DiscoveryEngine.add_identity` and
    `DiscoveryEngine.remove_identity`.
    """

    _publisher: Publisher
    _subscriber: Subscriber
    _heartbeat: float
    _identities: Dict[Tuple[str, str], Identity]
    _subscription: Optional[rx.disposable.Disposable]
    _heartbeat_task: Optional[asyncio.Task]
    _lifetime_task: Optional[asyncio.Task]
    _peers: Set[Identity]
    _last_seen: Dict[Identity, datetime]

    def __init__(
        self,
        publisher: Publisher,
        subscriber: Subscriber,
        identities: Optional[Sequence] = None,
        heartbeat: float = 5,
    ) -> None:
        """
        Create a new DiscoveryEngine with a publisher and subscriber.

        Arguments:
        publisher (scatterbrained.discovery.types.Publisher):
            The publisher to use for sending peer transactions.
        subscriber (scatterbrained.discovery.types.Subscriber):
            The subscriber to use for receiving peer transactions.
        identities
            (Optional[Sequence[scatterbrained.discovery.types.Identity]]):
            A list of identities to use for the initial peer list.
        heartbeat (float): The heartbeat interval in seconds.

        Returns:
            None

        """
        if identities is None:
            identities = []
        self.heartbeat = heartbeat
        self._publisher = publisher
        self._subscriber = subscriber
        self._identities = {(i.id, i.namespace): i for i in identities}
        self._subscription = None
        self._heartbeat_task = None
        self._lifetime_task = None
        self._peers = set()
        self._last_seen = {}

    @property
    def heartbeat(self):
        """
        Retrieve the heartbeat interval in seconds.
        """
        return self._heartbeat

    @heartbeat.setter
    def heartbeat(self, value):
        """
        Set the heartbeat interval in seconds.

        Arguments:
            value (float): The heartbeat interval in seconds.

        Returns:
            None

        """
        if value < 1:
            raise ValueError(f"value must be 1 or more (value={value})")
        self._heartbeat = value

    @property
    def peers(self):
        """
        Retrieve the list of peers.

        Returns:
            Set[scatterbrained.discovery.types.Identity]: The list of peers.

        """
        # Defensive copy.
        return set(self._peers)

    def add_identity(self, identity: Identity) -> None:
        """
        Add an identity to the list of identities for the current node.

        Arguments:
            identity (scatterbrained.discovery.types.Identity):
                The identity to add.

        Returns:
            None

        """
        self._identities[(identity.id, identity.namespace)] = identity

    def remove_identity(self, identity: Identity) -> None:
        """
        Remove an identity from the list of valid identities for the node.

        Arguments:
            identity (scatterbrained.discovery.types.Identity):
                The identity to remove.

        Returns:
            None

        """
        self._identities.pop((identity.id, identity.namespace), None)

    def update_identity_position(self, identity: Identity, pos: float) -> None:
        """
        Update the position of an identity from the list of valid
        identities for the node.

        Arguments:
            identity (scatterbrained.discovery.types.Identity):
                The identity to remove.
            pos: the new position
        Returns:
            None

        """
        self._identities[(identity.id, identity.namespace)].position = pos

    async def start(
        self,
        on_appear: Callable[[Identity], Awaitable[None]],
        on_disappear: Callable[[Identity], Awaitable[None]],
        on_error: Callable[[Exception], Awaitable[None]],
    ) -> None:
        """
        Start the DiscoveryEngine, with awaitable callbacks per peer.

        Callbacks receive an identity of the peer that appeared or disappeared.
        The `on_error` callback is called if an error occurs, and it receives
        as arguments the exception. Note that all callbacks are async.

        Arguments:
            on_appear (callback):
                A callback to call when a peer appears on the
                scatterbrained network.
            on_disappear (callback):
                callback to call when a peer disappears from the network.
            on_error (exception_handler):
                A callback to run when an exception is thrown
                communicating with a peer.

        Returns:
            None

        """
        if self._subscription is not None:
            return

        async def handle_peer_heartbeat(data):
            peer_info = orjson.loads(data)
            peer = Identity(**peer_info)
            # TODO: the proper way to check if a heartbeat was generated
            # locally is to look at the source ip, and cross-check that with
            # known interfaces. This will work for now, however.
            if (peer.id, peer.namespace) in self._identities:
                return
            elif peer not in self._peers:
                self._peers.add(peer)
                self._last_seen[peer] = datetime.now()
                await on_appear(peer)
            else:
                # Update time of last seen
                self._last_seen[peer] = datetime.now()

        await self._publisher.open()
        await self._subscriber.open()
        self._subscription = self._subscriber.subscribe(
            on_recv=handle_peer_heartbeat, on_error=on_error
        )
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._lifetime_task = asyncio.create_task(
            self._lifetime_monitor(on_disappear))

    async def stop(self):
        """
        Gracefully stop the `DiscoveryEngine`.

        Returns:
            None

        """
        if self._subscription is None:
            return

        assert self._heartbeat_task is not None  # nosec
        assert self._lifetime_task is not None  # nosec

        self._subscription.dispose()
        self._subscription = None

        self._heartbeat_task.cancel()
        await self._heartbeat_task
        self._heartbeat_task = None

        self._lifetime_task.cancel()
        await self._lifetime_task
        self._lifetime_task = None

        await self._publisher.close()
        await self._subscriber.close()

        self._peers = set()
        self._last_seen = {}

    async def _heartbeat_loop(self):
        try:
            while True:
                for id in self._identities.values():
                    obj = attrs.asdict(id)
                    obj = orjson.dumps(obj)
                    await self._publisher.publish(obj)
                await asyncio.sleep(self._heartbeat)
        except asyncio.CancelledError:
            pass

    async def _lifetime_monitor(
        self, on_disappear: Callable[[Identity], Awaitable[None]]
    ):
        try:
            while True:
                now = datetime.now()
                tasks = []
                to_remove = set()
                for peer, last_seen in self._last_seen.items():
                    if ((now - last_seen).total_seconds() >= self._heartbeat * 5):
                        self._peers.remove(peer)
                        to_remove.add(peer)
                        task = asyncio.create_task(on_disappear(peer))
                        tasks.append(task)
                # NOTE: not optimal, as tasks may take a long time,
                # but will suffice for now.
                if tasks:
                    for peer in to_remove:
                        self._last_seen.pop(peer)
                    await asyncio.wait(tasks)
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
