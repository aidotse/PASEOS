from typing import Optional, Sequence, Tuple

import zmq
import zmq.asyncio


class ZMQReceiver:
    _context: zmq.asyncio.Context
    _socket: Optional[zmq.asyncio.Socket]
    _host: Optional[str]
    _port: Optional[int]

    def __init__(self, context: Optional[zmq.asyncio.Context] = None):
        if context is None:
            context = zmq.asyncio.Context.instance()
        self._context = context
        self._socket = None
        self._host = None
        self._port = None

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    async def bind(self, host: str, port: Optional[int] = None) -> int:
        if self._socket is not None:
            return self._port

        self._socket = self._context.socket(zmq.ROUTER)
        if port is None:
            port = self._socket.bind_to_random_port(f"tcp://{host}")
        else:
            self._socket.bind(f"tcp://{host}:{port}")
        self._host = host
        self._port = port
        return self._port

    async def recv(self) -> Tuple[str, Sequence[bytes]]:
        if self._socket is None:
            raise RuntimeError("socket is unbound")

        peer_id, _, *segments = await self._socket.recv_multipart()
        return peer_id.decode(), segments

    async def close(self) -> None:
        if self._socket is None:
            return

        self._socket.close(linger=0)
        self._socket = None
        self._host = None
        self._port = None


class ZMQTransmitter:
    _id: str
    _context: zmq.asyncio.Context
    _socket: Optional[zmq.asyncio.Socket]
    _host: Optional[str]
    _port: Optional[int]

    def __init__(self, id: str, context: Optional[zmq.asyncio.Context] = None):
        if context is None:
            context = zmq.asyncio.Context.instance()
        self._id = id
        self._context = context
        self._socket = None
        self._host = None
        self._port = None

    @property
    def host(self) -> Optional[str]:
        return self._host

    @property
    def port(self) -> Optional[int]:
        return self._port

    async def connect(self, host: str, port: int) -> None:
        if self._socket is not None:
            return

        self._socket = self._context.socket(zmq.DEALER)
        self._socket.setsockopt_string(zmq.IDENTITY, self._id)
        self._socket.connect(f"tcp://{host}:{port}")
        self._host = host
        self._port = port

    async def send(self, *segments: bytes) -> None:
        if self._socket is None:
            raise RuntimeError("socket is not connected")
        await self._socket.send_multipart([b"", *segments])

    async def close(self) -> None:
        if self._socket is None:
            return

        self._socket.close(linger=0)
        self._socket = None
        self._host = None
        self._port = None


__all__ = ["ZMQReceiver", "ZMQTransmitter"]
