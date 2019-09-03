import json
import logging
import random
import subprocess
from time import sleep
import threading
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from mock import Mock
import pytest

from gridappsd import GOSS


@pytest.fixture(scope="module")
def assigned_stomp_port():
    """ Create a coilmq server for testing against.

    The coilmq server uses a random port (outside normal stomp protocol)
    for connecting to the bus.
    """

#     random_port = random.randint(61618, 61700)
#     args = ['coilmq', '--port',  str(random_port)]
#     proc = subprocess.Popen(args)

    # Use random port that was setup for testing
    # yield random_port

    # Use gridappsd normal port
    yield 61613

#     proc.kill()


@pytest.fixture
def goss_client(assigned_stomp_port):
    goss = GOSS(stomp_port=assigned_stomp_port)

    yield goss

    goss.disconnect()


def test_get_response(caplog, goss_client):
    caplog.set_level(logging.DEBUG)

    def addem_callback(header, message):
        print("Addem callback")
        print("Threadid: {}".format(threading.current_thread().ident))
        if isinstance(message, str):
            item = json.loads(message)
        else:
            item = message
        total = 0
        for x in item:
            total += x

        reply_to = header['reply-to']
        goss_client.send(reply_to, json.dumps(dict(result=total)))

    gen_sub = []

    def generic_subscription(header, message):
        gen_sub.append((header, message))

    # Simulate an rpc call.
    goss_client.subscribe("/addem", addem_callback)

    goss_client.subscribe("foo", generic_subscription)

    # id_before = id(goss_client._conn)
    result = goss_client.get_response('/addem', [5, 6])
    assert result['result'] == 11
    # assert id_before == id(goss_client._conn)

    goss_client.send("foo", str(result['result']))

    count = 0
    while True:
        sleep(0.1)
        count += 1
        if len(gen_sub) > 0 or count > 10:
            break

    assert gen_sub
    assert len(gen_sub) == 1
    assert len(gen_sub[0]) == 2
    assert gen_sub[0][1] == 11
    assert result['result'] == 11


def test_connect(assigned_stomp_port):
    goss = GOSS(stomp_port=assigned_stomp_port)

    assert goss.connected
    goss.disconnect()
    assert not goss.connected
    goss.connect()
    assert goss.connected


def test_send_receive(goss_client):

    message_queue = Queue()

    class MyListener(object):
        def on_message(self, headers, message):
            message_queue.put((headers, message))

    listener = MyListener()
    goss_client.subscribe('doah', listener)
    goss_client.send('doah', "I am a foo")
    sleep(0.1)
    assert message_queue.qsize() == 1
    header, message = message_queue.get()
    assert message == "I am a foo"


def test_callback_function(goss_client):

    message_queue1 = Queue()

    def callback1(headers, message):
        message_queue1.put((headers, message))

    goss_client.subscribe('/foo', callback1)
    goss_client.send('/foo', "I am a foo")
    sleep(0.1)
    assert message_queue1.qsize() == 1
    header, message = message_queue1.get()
    assert message == "I am a foo"


def test_multi_subscriptions(goss_client):

    message_queue1 = Queue()
    message_queue2 = Queue()

    def callback1(headers, message):
        message_queue1.put((headers, message))

    def callback2(headers, message):
        message_queue2.put((headers, message))

    goss_client.subscribe('bim', callback1)
    goss_client.subscribe('bar', callback2)
    goss_client.send('bim', "I am a foo")
    goss_client.send('bar', "I am a bar")
    sleep(0.5)
    assert message_queue1.qsize() == 1
    assert message_queue2.qsize() == 1
    header, message = message_queue1.get()
    assert message == "I am a foo"
    header, message = message_queue2.get()
    assert message == "I am a bar"


def test_multi_subscriptions_same_topic(goss_client):
    pytest.xfail("Multiple topics can't be subscribed to the same topic at present.")

    message_queue1 = Queue()
    message_queue2 = Queue()

    def callback1(headers, message):
        message_queue1.put((headers, message))

    def callback2(headers, message):
        message_queue2.put((headers, message))

    goss_client.subscribe('bim', callback1)
    goss_client.subscribe('bim', callback2)
    goss_client.send('bim', "I am a foo")
    goss_client.send('bim', "I am a bar")
    sleep(0.5)
    assert message_queue1.qsize() == 2
    assert message_queue2.qsize() == 2
    header, message = message_queue1.get()
    assert message == "I am a foo"
    header, message = message_queue1.get()
    assert message == "I am a bar"
    header, message = message_queue2.get()
    assert message == "I am a foo"
    header, message = message_queue2.get()
    assert message == "I am a bar"


def test_response_class(goss_client):

    message_queue = Queue()

    class SubListener():
        def on_message(self, header, message):
            message_queue.put((header, message))

    goss_client.subscribe("/bar", SubListener())
    goss_client.send("/bar", json.dumps({'abc': 'def'}))

    result = message_queue.get()

    print(result)
    assert result
    assert 2 == len(result)
    assert result[1] == {"abc": "def"}


def test_replace_subscription(caplog, goss_client):
    caplog.set_level(logging.DEBUG)
    original_queue = Queue()
    after_queue = Queue()

    def original_callback(headers, message):
        original_queue.put((headers, message))

    def after_callback(headers, message):
        after_queue.put((headers, message))

    goss_client.subscribe("woot", original_callback)
    goss_client.send("woot", "This is a message")
    sleep(0.5)

    assert original_queue.qsize() == 1


