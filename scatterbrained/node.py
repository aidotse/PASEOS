from __future__ import annotations

import asyncio
import attrs
from collections import defaultdict, deque
from enum import Enum
from typing import Callable, Deque, Dict, Optional
from typing import Sequence, Set, Tuple, Union, cast
from loguru import logger

from .discovery import DiscoveryEngine, UDPBroadcaster, UDPReceiver
from .network import NetworkEngine, ZMQReceiver, ZMQTransmitter
from .types import Identity


class OperatingMode(Enum):
    """
    The mode for the Node to operate in.

    Leech:      Listen for broadcasts; do not share.
    Offline:    Do not listen or broadcast.
    Peer:       Listen and broadcast.
    Seeding:    Broadcast but do not listen.

    """

    LEECHING = "leeching"
    OFFLINE = "offline"
    PEER = "peer"
    SEEDING = "seeding"


class Namespace:
    """
    A Namespace is a collection of Scatterbrained nodes that share a common
    model or parameter state space. When connecting or disconnecting from a
    community, a Scatterbrained node joins a named namespace, or creates a new
    namespace with a unique name.

    Note that this  class shouldn't be instantiated directly, rather
    instances should created via the `scatterbrained.Node.namespace` method.

    """

    node: Node
    name: str
    peer_filter: Callable[[Identity], bool]
    _operating_mode: OperatingMode
    _advertised_host: str
    _advertised_port: int
    _id: Identity
    _mq: Deque[Tuple[Identity, Sequence[bytes]]]
    _msg_cond: asyncio.Condition
    _peer_cond: asyncio.Condition

    def __init__(
        self,
        node: Node,
        name: str,
        operating_mode: Optional[OperatingMode] = None,
        peer_filter: Optional[Callable[[Identity], bool]] = None,
        advertised_host: Optional[str] = None,
        advertised_port: Optional[int] = None,
        hwm: int = 10_000,
        position: float = 0,
    ):
        """
        Create a new Namespace or point to an existing one.

        Arguments:
            node (scatterbrained.Node):
                The `scatterbrained.Node` to which this Namespace belongs.
            name (str):
                The name of the `Namespace`.
                Must be unique if you are creating a new `Namespace`.
            operating_mode (scatterbrained.OperatingMode):
                The operating mode in which the `Node` should operate in this
                namespace. For more information on the different operating
                modes, see the docs on the `scatterbrained.node.OperatingMode`
                enum.
            peer_filter (callable):
                A function that takes an `Identity` and returns a boolean
                indicating whether the `Node` should connect to the peer.
            advertised_host (str, optional):
                The hostname or IP address to advertise to other
                Scatterbrained nodes.
            advertised_port (int, optional):
                The port to advertise to other nodes.
            hwm (int):
                The high water mark for the message queue.
                Old messages  will be dropped if the queue is full
                beyond this number. Defaults to 10,000.

        """
        if not node.listening:
            raise RuntimeError(
                f"{type(node).__name__} must be listening before \
                    {type(self).__name__} creation"
            )
        if advertised_host is None:
            advertised_host = node.default_advertised_host
        if advertised_port is None:
            advertised_port = node.default_advertised_port

        assert advertised_host is not None  # nosec
        assert advertised_port is not None  # nosec

        self.node = node
        self.name = name
        self.peer_filter = peer_filter or node.default_peer_filter
        self._operating_mode = operating_mode or node.default_operating_mode
        self._advertised_host = advertised_host
        self._advertised_port = advertised_port
        self._position = position
        self._id = Identity(
            id=self.node.id,
            namespace=self.name,
            host=self._advertised_host,
            port=self._advertised_port,
            position=self._position,
        )
        self._mq = deque(maxlen=hwm)
        self._msg_cond = asyncio.Condition()
        self._peer_cond = asyncio.Condition()

    @property
    def operating_mode(self):
        """
        Get the operating mode for this namespace.

        Returns:
            scatterbrained.OperatingMode:
                The operating mode for this namespace.

        """
        return self._operating_mode

    # NOTE: This may need to be an async setter method as opposed to a
    # setter property.
    @operating_mode.setter
    def operating_mode(self, value: OperatingMode):
        self._operating_mode = value

    async def __aenter__(self) -> Namespace:
        await self.launch()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def launch(self):
        """
        Launch the Namespace.

        This is usually done by entering the `Namespace` context manager.
        You should not need to call this method
        directly.

        """
        self.node.discovery_engine.add_identity(self._id)
        current_peers = self.node.discovery_engine.peers
        # TODO: explore exception handling approaches.
        # TODO: Is returning the exceptions really the best way to do this?
        # AFAIK, gather will cancel any ops running if an exception occurs,
        # which would mean we'd only need to clean up.
        # We should clean up regardless?
        statuses = await asyncio.gather(
            *[self.connect_to(p) for p in current_peers],
            return_exceptions=True
        )

        ex = False
        connected = []
        for peer, value in zip(current_peers, statuses):
            if isinstance(value, Exception):
                logger.bind(peer=peer).opt(exception=value).error(
                    f"failed to connect to {peer.id} \
                        (addr={peer.host}:{peer.port})"
                )
                ex = True
            elif value:
                connected.append(peer)
        self.node._update_connections(self, connected)
        if ex:
            raise RuntimeError(
                f"one or more exceptions occurred when attempting to launch \
                    {type(self).__name__} '{self.name}'"
            )

    async def close(self):
        """
        Close out the Namespace gracefully.

        This is usually done by exiting the `Namespace` context manager.
        You should not need to call this method
        directly.

        """
        self.node.discovery_engine.remove_identity(
            Identity(
                id=self.node.id,
                namespace=self.name,
                host=self._advertised_host,
                port=self._advertised_port,
                position=self._position,
            )
        )

    async def connect_to(self, peer: Identity) -> bool:
        """
        Connect to a peer in this Namespace by its Identity.

        The method will not connect to the given peer if the `OperatingMode`
        of this Namespace is either `LEECHING` or`OFFLINE`, or the `Identity`
        is rejected by this instance's `peer_filter`.

        Arguments:
            peer (scatterbrained.Identity): The peer to connect to.

        Returns:
            bool: `True` if the connection was successful, `False` otherwise.

        """
        if (
            self.operating_mode == OperatingMode.LEECHING or self.operating_mode == OperatingMode.OFFLINE or not
                self.peer_filter(peer)
        ):
            return False

        await self.node.network_engine.connect_to(peer.host, peer.port)
        return True

    async def disconnect_from(self, peer: Identity) -> bool:
        """
        Disconnect from a peer in this `Namespace` by its `Identity`.

        Arguments:
            peer (scatterbrained.Identity): The peer to disconnect from.

        Returns:
            bool: `True` if the disconnection was successful, `False` otherwise

        """
        return await self.node._disconnect_from(peer)

    async def wait_for_peers(
        self,
        peers: Union[int, str, Identity, Sequence[Identity], Sequence[str]],
        timeout: Optional[float] = None,
    ) -> None:
        """
        Wait for peers to connect to this Namespace.

        This method behaves in one of three ways
        depending on the type of arguments passed:

        * If you pass one or more `Identity` objects,
        this will wait for all peers to connect. Importantly,
        this will match on all attributes of the `Identity` objects.
        * If you pass one or more strings,
        this will wait for all peers with the specified ids.
        * If you pass an integer,
        this will wait for that many peers to connect.


        Arguments:
        peers (Union[int, str, Identity, Sequence[Identity], Sequence[str]]):
            The condition to await.
        timeout (float):
            The timeout in seconds to wait for the condition  to be met.

        Returns:
            None

        """
        if isinstance(peers, int):
            try:
                peers = await asyncio.wait_for(
                    self._wait_for_n_peers(peers), timeout=timeout
                )
            except TimeoutError as e:
                logger.exception(e)
                raise
            finally:
                return peers
        elif isinstance(peers, str):
            peers = [peers]
        elif isinstance(peers, Identity):
            peers = [peers]
        strings_present = any(isinstance(v, str) for v in peers)
        if strings_present:
            peers = [v if isinstance(v, str) else v.id for v in peers]
            await asyncio.wait_for(self._wait_for_named_peers(peers),
                                   timeout=timeout)
        else:
            peers = cast(Sequence[Identity], peers)
            await asyncio.wait_for(self._wait_for_exact_peers(peers),
                                   timeout=timeout)

    async def _wait_for_n_peers(self, num_peers: int) -> None:
        def check_fn():
            return len(self.node._peers_by_namespace[self.name]) >= num_peers

        if not check_fn():
            async with self._peer_cond:
                await self._peer_cond.wait_for(check_fn)

    async def _wait_for_named_peers(self, peers: Sequence[str]) -> None:
        peer_set = set(peers)

        def check_fn():
            return (len(peer_set - set(v.id for v in self.node._peers_by_namespace[self.name])) == 0)

        if not check_fn():
            async with self._peer_cond:
                await self._peer_cond.wait_for(check_fn)

    async def _wait_for_exact_peers(self, peers: Sequence[Identity]) -> None:
        peer_set = set(peers)

        def check_fn():
            return len(peer_set - self.node._peers_by_namespace[self.name]) == 0

        if not check_fn():
            async with self._peer_cond:
                await self._peer_cond.wait_for(check_fn)

    async def send_to(self, peer: Identity, *payload: bytes) -> None:
        """
        Send a byte sequence payload to a peer by its `Identity`.

        Arguments:
            peer (scatterbrained.Identity): The peer to send to.
            payload (bytes): The payload to send.

        Returns:
            None

        """
        await self.node.network_engine.send_to(self._id, peer, *payload)

    async def recv(
        self, timeout: Optional[float] = None
    ) -> Tuple[Identity, Sequence[bytes]]:
        """
        Receive a message from the network.

        This will block until a message is received, or the timeout is reached.

        Arguments:
            timeout (float):
            The timeout in seconds to wait for a message to be received.

        Returns:
            Tuple[scatterbrained.Identity, bytes]:
            The sender's Identity and the payload if timeout not triggered
            Tuple[None, None] if timeout triggered

        """

        rx = (None, None)
        try:
            if not len(self._mq):
                async with self._msg_cond:
                    await asyncio.wait_for(self._msg_cond.wait(),
                                           timeout=timeout)
        except TimeoutError as e:
            logger.exception(e)
            raise
        else:
            rx = self._mq.pop()
        finally:
            return rx

    async def _on_appear(self, peer: Identity):
        async with self._peer_cond:
            self._peer_cond.notify_all()

    async def _add_message_from(self,
                                peer: Identity,
                                payload: Sequence[bytes]) -> None:
        empty = len(self._mq) == 0
        self._mq.append((peer, payload))

        if empty:
            async with self._msg_cond:
                self._msg_cond.notify()


class Node:
    """
    Scatterbrained peer node.

    Manages all networking infrastructure, providing an interface
    for other classes to establish connections, and send
    and receive data.
    """

    id: str
    discovery_engine: DiscoveryEngine
    network_engine: NetworkEngine
    default_operating_mode: OperatingMode
    default_peer_filter: Callable[[Identity], bool]
    default_advertised_host: Optional[str]
    default_advertised_port: Optional[int]
    _host: str
    _port: Optional[int]
    _namespaces: Dict[str, Namespace]
    _virtual_tx_connections: Dict[Tuple[str, int], Set[Identity]]
    _peers_by_namespace: Dict[str, Set[Identity]]
    _network_sub: Optional[NetworkEngine.Disposable]

    def __init__(
        self,
        id: str,
        host: str = "0.0.0.0",  # nosec
        port: Optional[int] = None,
        discovery_engine: Optional[DiscoveryEngine] = None,
        network_engine: Optional[NetworkEngine] = None,
        default_operating_mode: OperatingMode = OperatingMode.PEER,
        default_peer_filter: Optional[Callable[[Identity], bool]] = None,
        default_advertised_host: Optional[str] = None,
        default_advertised_port: Optional[int] = None,
    ) -> None:
        """
        Create a new Scatterbrained peer node.

        Arguments:
            id (str):
                The identity of this `Node`.
                Must be provided.
            host (str):
                The host to bind to.
                Defaults to bind on all IP addresses on the machine (`0.0.0.0`)
            port (int):
                The port to bind to.
                Defaults to an arbitrary open port.
            discovery_engine (scatterbrained.DiscoveryEngine):
                The `DiscoveryEngine` to use.
                Defaults to a new `DiscoveryEngine` with a
                default configuration, using UDP broadcast.
            network_engine (scatterbrained.NetworkEngine):
                The `NetworkEngine` to use.
                Defaults to a new NetworkEngine with a default
                configuration, using ZMQ.
            default_operating_mode (scatterbrained.OperatingMode):
                The default operating mode for new `Namespace`s.
                Defaults to `OperatingMode.PEER`.
            default_peer_filter (Callable[[scatterbrained.Identity], bool]):
                The default peer filter for new `Namespace`s.
                The default behavior is for all peers to be accepted.
            default_advertised_host (str):
                The advertised host to use for new `Namespace`s.
                Defaults to the host provided.
            default_advertised_port (int):
                The advertised port to use for new `Namespace`s.
                Defaults to the port provided.

        """
        if discovery_engine is None:
            discovery_engine = DiscoveryEngine(
                publisher=UDPBroadcaster(), subscriber=UDPReceiver()
            )
        if network_engine is None:
            network_engine = NetworkEngine(
                rx=ZMQReceiver(), tx_factory=lambda: ZMQTransmitter(id=id)
            )
        if default_peer_filter is None:
            default_peer_filter = lambda _: True  # noqa: E731

        self.id = id
        self.discovery_engine = discovery_engine
        self.network_engine = network_engine
        self.default_peer_filter = default_peer_filter
        self.default_operating_mode = default_operating_mode
        self.default_advertised_host = default_advertised_host
        self.default_advertised_port = default_advertised_port
        self._host = host
        self._port = port
        self._namespaces = {}
        self._virtual_tx_connections = defaultdict(set)
        self._peers_by_namespace = defaultdict(set)
        self._network_sub = None

    @property
    def listening(self):
        """
        Whether or not the `Node` is listening for incoming connections.

        Returns:
            bool: Whether or not the Node is listening for incoming connections

        """
        return self._network_sub is not None

    async def __aenter__(self) -> Node:
        await self.launch()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def launch(self) -> None:
        """
        Launch the `Node`.

        This will start the `DiscoveryEngine` and `NetworkEngine`
        and begin listening for new connections.

        Note that this method is usually called automatically when
        entering an `async with` block and is not meant to be called manually.

        Returns:
            None

        """
        if self._network_sub is not None:
            return
        await self.network_engine.bind(host=self._host, port=self._port)
        self._network_sub = self.network_engine.subscribe(
            on_recv=self._on_recv,
            on_malformed=self._on_malformed,
            on_error=self._on_network_error,
        )
        await self.discovery_engine.start(
            on_appear=self._on_appear,
            on_disappear=self._on_disappear,
            on_error=self._on_discovery_error,
        )

        bound_host, bound_port = self.network_engine.bound_address
        assert bound_host is not None, "bound host should not be None"  # nosec
        assert bound_port is not None, "bound port should not be None"  # nosec

        if self.default_advertised_host is None:
            self.default_advertised_host = bound_host
        if self.default_advertised_port is None:
            self.default_advertised_port = bound_port

    async def close(self):
        """
        Gracefully close the `Node`.

        This will close the `DiscoveryEngine` and `NetworkEngine`.

        Note that this method is usually called automatically when
        exiting an `async with` block and is not meant to be
        called manually.

        Returns:
            None

        """
        if self._network_sub is None:
            return
        await self.discovery_engine.stop()
        await self._network_sub.dispose()
        await self.network_engine.close()
        self._network_sub = None

    def namespace(self, name: str, *args, **kwargs) -> Namespace:
        """
        Gets the namespace with the given name, or creates a new one.

        Also accepts the same arguments as `scatterbrained.Namespace`
        if creating a new namespace.

        Arguments:
            name (str): The name of the namespace.

        Returns:
            scatterbrained.Namespace: The namespace with the given name.

        """
        if (ns := self._namespaces.get(name)) is not None:
            return ns

        ns = Namespace(self, name, *args, **kwargs)
        self._namespaces[ns.name] = ns
        return ns

    def _update_connections(self,
                            ns: Namespace,
                            peers: Sequence[Identity]) -> None:
        for peer in peers:
            self._virtual_tx_connections[(peer.host, peer.port)].add(peer)

    async def _on_appear(self, peer: Identity) -> None:
        cl = logger.bind(peer=attrs.asdict(peer))
        cl.debug(f"peer '{peer.id}' is online")

        ns = self._namespaces.get(peer.namespace)
        if ns is not None:
            connected = await ns.connect_to(peer)
            if connected:
                cl.debug(f"connected to '{peer.id}'")

                self._virtual_tx_connections[(peer.host, peer.port)].add(peer)
                self._peers_by_namespace[ns.name].add(peer)
                await ns._on_appear(peer)

    async def _on_disappear(self, peer: Identity) -> None:
        await self._disconnect_from(peer)

    async def _on_discovery_error(self, ex: Exception) -> None:
        logger.opt(exception=ex).error("discovery engine encountered an error")
        # TODO: determine how to best alert the user of this error.

    async def _on_recv(self, peer: Identity, payload: Sequence[bytes]) -> None:
        ns = self._namespaces.get(peer.namespace)
        if ns is not None:
            await ns._add_message_from(peer, payload)

    async def _on_malformed(self,
                            peer_id: str,
                            segments: Sequence[bytes]) -> None:
        logger.warning(
            f"malformed message consisting of {len(segments)} \
                byte segments from '{peer_id}'"
        )
        # TODO: anything else to do here? Maybe allow segments to be saved.

    async def _on_network_error(self, ex: Exception) -> None:
        logger.opt(exception=ex).error("network engine encountered an error")
        # TODO: determine how to best alert the user of this error.

    async def _disconnect_from(self, peer: Identity) -> bool:
        cl = logger.bind(peer=attrs.asdict(peer))
        cl.debug(f"peer '{peer.id}' is offline")

        virt_conns = self._virtual_tx_connections[(peer.host, peer.port)]
        if peer not in virt_conns:
            cl.warning(
                f"attempted to disconnect from peer '{peer.id}' \
                    that was never connected to originally"
            )
            return False
        virt_conns.remove(peer)
        if not virt_conns:
            await self.network_engine.disconnect_from(peer.host, peer.port)

            cl.debug(f"disconnected from '{peer.host}:{peer.port}'")
        self._peers_by_namespace[peer.namespace].remove(peer)
        return True


__all__ = ["Node"]
