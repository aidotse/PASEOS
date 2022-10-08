import asyncio
import pytest
import pytest_asyncio
import zmq
import zmq.asyncio
import sys
sys.path.append("../..")
from scatterbrained.network.zmq_ip import ZMQReceiver, ZMQTransmitter

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.fixture
def addr():
    return "127.0.0.1"


@pytest.fixture
def port():
    return 9001


@pytest.fixture
def context():
    ctx = zmq.asyncio.Context()
    yield ctx
    ctx.destroy(linger=0)


@pytest.fixture
def client_id():
    return "foobar"


@pytest_asyncio.fixture
async def dealer(context, client_id, addr, port):
    socket = context.socket(zmq.DEALER)
    socket.identity = client_id.encode()
    socket.connect(f"tcp://{addr}:{port}")
    yield socket
    socket.close(linger=0)


@pytest_asyncio.fixture
async def router(context, addr, port):
    socket = context.socket(zmq.ROUTER)
    socket.bind(f"tcp://{addr}:{port}")
    yield socket
    socket.close(linger=0)


async def test_ZMQReceiver_recv(context, dealer, client_id, addr, port):
    rx = ZMQReceiver(context=context)

    await rx.bind(addr, port)

    msg1, msg2 = b"hello there", b"general kenobi"
    await dealer.send_multipart([b"", msg1, msg2])

    actual_id, actual_msg = await asyncio.wait_for(rx.recv(), timeout=3.0)

    assert actual_id == client_id
    assert actual_msg == [msg1, msg2]

    await rx.close()


async def test_ZMQTransmitter_send(context, router, client_id, addr, port):
    tx = ZMQTransmitter(client_id, context=context)

    await tx.connect(addr, port)

    msg1, msg2 = b"hello there", b"general kenobi"
    await tx.send(msg1, msg2)

    actual_id, _, *actual_segments = await router.recv_multipart()

    assert actual_id.decode() == client_id
    assert actual_segments == [msg1, msg2]
