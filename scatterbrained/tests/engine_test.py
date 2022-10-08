import sys
import orjson
import pytest
import asyncio
import attrs
sys.path.append("../..")
from scatterbrained.types import Identity
from scatterbrained.network.engine import NetworkEngine
from unittest.mock import AsyncMock


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.fixture
def id1():
    return Identity(id="1",
                    namespace="foo",
                    host="127.0.0.1",
                    port=9002,
                    position=0)


@pytest.fixture
def id2():
    return Identity(id="2",
                    namespace="bar",
                    host="127.0.0.1",
                    port=9002,
                    position=0)


@pytest.fixture
def id3():
    return Identity(id="3",
                    namespace="baz",
                    host="127.0.0.1",
                    port=9003,
                    position=0)


@pytest.fixture
def msg(id1):
    identity = orjson.dumps(attrs.asdict(id1))
    payload = b"hello there"

    return (id1.id, [identity, payload])


@pytest.fixture
def malformed_msg():
    return ("foo", [b"hello there"])


@pytest.mark.unit
async def test_NetworkEngine_connect_to(id1, id2, id3):
    engine = NetworkEngine(AsyncMock(), lambda: AsyncMock())

    await engine.connect_to(id1.host, id1.port)

    assert list(engine._physical_tx_connections) == [(id1.host, id1.port)]
    tx = engine._physical_tx_connections[(id1.host, id1.port)]
    tx.connect.assert_called_once_with(id1.host, id1.port)

    await engine.connect_to(id2.host, id2.port)

    assert list(engine._physical_tx_connections) == [(id1.host, id1.port)]
    tx = engine._physical_tx_connections[(id1.host, id1.port)]
    tx.connect.assert_called_once_with(id1.host, id1.port)

    await engine.connect_to(id3.host, id3.port)

    assert list(engine._physical_tx_connections) == [
        (id1.host, id1.port),
        (id3.host, id3.port),
    ]
    tx1 = engine._physical_tx_connections[(id1.host, id1.port)]
    tx1.connect.assert_called_once_with(id1.host, id1.port)
    tx2 = engine._physical_tx_connections[(id3.host, id3.port)]
    tx2.connect.assert_called_once_with(id3.host, id3.port)


@pytest.mark.unit
async def test_NetworkEngine_subscribe(msg):
    async def mock_recv():
        await asyncio.sleep(0.01)
        return msg

    async def mock_on_recv(*args):
        async with cond:
            cond.notify()

    port = 9001
    rx = AsyncMock()
    rx.bind.return_value = port
    rx.recv.side_effect = mock_recv

    engine = NetworkEngine(rx, lambda: AsyncMock())

    actual_port = await engine.bind("127.0.0.1", port)
    assert actual_port == port

    cond = asyncio.Condition()
    on_recv = AsyncMock(side_effect=mock_on_recv)
    on_malformed = AsyncMock()
    on_error = AsyncMock()
    d = engine.subscribe(on_recv=on_recv,
                         on_malformed=on_malformed,
                         on_error=on_error)

    async with cond:
        await asyncio.wait_for(cond.wait(), 3.0)

    await d.dispose()

    expected_id = Identity(**orjson.loads(msg[1][0]))
    expected_segments = msg[1][1:]
    on_recv.assert_awaited_with(expected_id, expected_segments)
    on_malformed.assert_not_awaited()
    on_error.assert_not_awaited()


@pytest.mark.unit
async def test_NetworkEngine_subscribe_malformed(malformed_msg):
    async def mock_recv():
        await asyncio.sleep(0.01)
        return malformed_msg

    async def mock_on_malformed(*args):
        async with cond:
            cond.notify()

    port = 9001
    rx = AsyncMock()
    rx.bind.return_value = port
    rx.recv.side_effect = mock_recv

    engine = NetworkEngine(rx, lambda: AsyncMock())

    actual_port = await engine.bind("127.0.0.1", port)
    assert actual_port == port

    cond = asyncio.Condition()
    on_recv = AsyncMock()
    on_malformed = AsyncMock(side_effect=mock_on_malformed)
    on_error = AsyncMock()
    d = engine.subscribe(on_recv=on_recv,
                         on_malformed=on_malformed,
                         on_error=on_error)

    async with cond:
        await asyncio.wait_for(cond.wait(), 3.0)

    await d.dispose()

    expected_id = malformed_msg[0]
    expected_segments = malformed_msg[1]
    on_malformed.assert_awaited_with(expected_id, expected_segments)
    on_recv.assert_not_awaited()
    on_error.assert_not_awaited()


@pytest.mark.unit
async def test_NetworkEngine_subscribe_error():
    async def mock_recv():
        await asyncio.sleep(0.01)
        raise ex

    async def mock_on_error(*args):
        async with cond:
            cond.notify()

    port = 9001
    rx = AsyncMock()
    rx.bind.return_value = port
    rx.recv.side_effect = mock_recv

    engine = NetworkEngine(rx, lambda: AsyncMock())

    actual_port = await engine.bind("127.0.0.1", port)
    assert actual_port == port

    ex = ValueError("yeet")
    cond = asyncio.Condition()
    on_recv = AsyncMock()
    on_malformed = AsyncMock()
    on_error = AsyncMock(side_effect=mock_on_error)
    d = engine.subscribe(on_recv=on_recv,
                         on_malformed=on_malformed,
                         on_error=on_error)

    async with cond:
        await asyncio.wait_for(cond.wait(), 3.0)

    await d.dispose()

    on_error.assert_awaited_with(ex)
    on_recv.assert_not_awaited()
    on_malformed.assert_not_awaited()


@pytest.mark.unit
async def test_NetworkEngine_subscribe_not_bound():
    engine = NetworkEngine(AsyncMock(), lambda: AsyncMock())

    with pytest.raises(RuntimeError):
        engine.subscribe(on_recv=AsyncMock(), on_malformed=AsyncMock())


@pytest.mark.unit
async def test_NetworkEngine_send_to(id1, id2):
    engine = NetworkEngine(AsyncMock(), lambda: AsyncMock())

    await engine.connect_to(id2.host, id2.port)
    await engine.send_to(id1, id2, b"hello there")

    tx = engine._physical_tx_connections[(id2.host, id2.port)]
    await tx.send.awaited_once_with(orjson.dumps(attrs.asdict(id1)),
                                    b"hello there")


@pytest.mark.unit
async def test_NetworkEngine_send_to_not_connected(id1, id2):
    engine = NetworkEngine(AsyncMock(), lambda: AsyncMock())

    with pytest.raises(RuntimeError):
        await engine.send_to(id1, id2, b"hello there")


@pytest.mark.unit
async def test_NetworkEngine_disconnect_from(id1, id2, id3):
    engine = NetworkEngine(AsyncMock(), lambda: AsyncMock())

    await engine.connect_to(id1.host, id1.port)
    await engine.connect_to(id2.host, id2.port)
    await engine.connect_to(id3.host, id3.port)

    tx12 = engine._physical_tx_connections[(id1.host, id1.port)]
    tx3 = engine._physical_tx_connections[(id3.host, id3.port)]

    assert list(engine._physical_tx_connections) == [
        (id1.host, id1.port),
        (id3.host, id3.port),
    ]

    await engine.disconnect_from(id2.host, id2.port)

    tx12.close.assert_awaited_once()
    assert list(engine._physical_tx_connections) == [(id3.host, id3.port)]

    await engine.disconnect_from(id3.host, id3.port)

    tx3.close.assert_awaited_once()
    assert list(engine._physical_tx_connections) == []
