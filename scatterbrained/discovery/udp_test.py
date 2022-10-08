import asyncio
import socket
from unittest.mock import AsyncMock
import pytest
from . import udp

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.fixture
def addr():
    return "127.0.0.1"


@pytest.fixture
def port():
    return 9001


async def test_UDPBroadcaster_full(event_loop, addr, port):
    # To simplify things, just use a blocking socket
    recv_socket = socket.socket(socket.AF_INET,
                                socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)
    recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    recv_socket.settimeout(3)
    await event_loop.run_in_executor(None, recv_socket.bind, ("", port))

    broadcaster = udp.UDPBroadcaster(broadcast_addr=addr, port=port)
    assert broadcaster._transport is None and broadcaster._protocol is None

    await broadcaster.open()
    assert (broadcaster._transport is not None and
            broadcaster._protocol is not None)

    expected = b"hello world"
    await broadcaster.publish(expected)
    actual, _ = await event_loop.run_in_executor(None,
                                                 recv_socket.recvfrom,
                                                 255)
    assert actual == expected

    await broadcaster.close()
    assert broadcaster._transport is None and broadcaster._protocol is None


async def test_UDPBroadcaster_full_async_with(event_loop, addr, port):
    recv_socket = socket.socket(socket.AF_INET,
                                socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)
    recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    recv_socket.settimeout(3)
    await event_loop.run_in_executor(None, recv_socket.bind, ("", port))

    broadcaster = udp.UDPBroadcaster(broadcast_addr=addr, port=port)
    assert broadcaster._transport is None and broadcaster._protocol is None

    async with broadcaster:
        assert (broadcaster._transport is not None and
                broadcaster._protocol is not None)

        expected = b"hello world"
        await broadcaster.publish(expected)
        actual, _ = await event_loop.run_in_executor(None,
                                                     recv_socket.recvfrom,
                                                     255)
        assert actual == expected

    assert broadcaster._transport is None and broadcaster._protocol is None


async def test_UDPReceiver_full(event_loop, addr, port):
    async def mock_on_recv(*args):
        async with cond:
            cond.notify()

    # To simplify things, just use a blocking socket
    send_socket = socket.socket(socket.AF_INET,
                                socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)

    receiver = udp.UDPReceiver(local_addr=addr, port=port)
    assert receiver._transport is None and receiver._protocol is None

    await receiver.open()
    assert receiver._transport is not None and receiver._protocol is not None

    cond = asyncio.Condition()
    on_recv = AsyncMock(side_effect=mock_on_recv)
    on_error = AsyncMock()
    receiver.subscribe(on_recv=on_recv, on_error=on_error)

    expected = b"hello world"
    send_socket.sendto(expected, (addr, port))
    async with cond:
        await asyncio.wait_for(cond.wait(), 3.0)

    on_recv.assert_awaited_once_with(expected)
    on_error.assert_not_awaited()

    await receiver.close()
    assert receiver._transport is None and receiver._protocol is None


async def test_UDPReceiver_async_with(event_loop, addr, port):
    async def mock_on_recv(*args):
        async with cond:
            cond.notify()

    # To simplify things, just use a blocking socket
    send_socket = socket.socket(socket.AF_INET,
                                socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)

    receiver = udp.UDPReceiver(local_addr=addr, port=port)
    assert receiver._transport is None and receiver._protocol is None

    async with receiver:
        assert (receiver._transport is not None and
                receiver._protocol is not None)

        cond = asyncio.Condition()
        on_recv = AsyncMock(side_effect=mock_on_recv)
        on_error = AsyncMock()
        receiver.subscribe(on_recv=on_recv, on_error=on_error)

        expected = b"hello world"
        send_socket.sendto(expected, (addr, port))
        async with cond:
            await asyncio.wait_for(cond.wait(), 3.0)

        on_recv.assert_awaited_once_with(expected)
        on_error.assert_not_awaited()
    assert receiver._transport is None and receiver._protocol is None


async def test_UDPReceiver_error(event_loop, addr, port):
    async def mock_on_recv(*args):
        await asyncio.sleep(0.01)
        raise RuntimeError("yeet")

    async def mock_on_error(*args):
        async with cond:
            cond.notify()

    # To simplify things, just use a blocking socket
    send_socket = socket.socket(socket.AF_INET,
                                socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)

    receiver = udp.UDPReceiver(local_addr=addr, port=port)
    assert receiver._transport is None and receiver._protocol is None

    async with receiver:
        assert (receiver._transport is not None and
                receiver._protocol is not None)

        cond = asyncio.Condition()
        on_recv = AsyncMock(side_effect=mock_on_recv)
        on_error = AsyncMock(side_effect=mock_on_error)
        receiver.subscribe(on_recv=on_recv, on_error=on_error)

        expected = b"hello world"
        send_socket.sendto(expected, (addr, port))
        async with cond:
            await asyncio.wait_for(cond.wait(), 3.0)

        on_recv.assert_awaited_once_with(expected)
        on_error.assert_awaited_once()
