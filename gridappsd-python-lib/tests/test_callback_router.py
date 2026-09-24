import pytest
from queue import Queue
from time import sleep

from gridappsd.goss import CallbackRouter, _is_wildcard_topic, _wildcard_to_regex, _STOMP_V8


def _make_msg(headers, body):
    """Build on_message args matching the installed stomp version."""
    if _STOMP_V8:
        class _Frame:
            pass
        frame = _Frame()
        frame.headers = headers
        frame.body = body
        return (frame,)
    return (headers, body)


class TestIsWildcardTopic:
    def test_no_wildcards(self):
        assert _is_wildcard_topic("/topic/goss.gridappsd.simulation.output.123") is False

    def test_star_wildcard(self):
        assert _is_wildcard_topic("/topic/goss.gridappsd.field.*") is True

    def test_gt_wildcard(self):
        assert _is_wildcard_topic("/topic/goss.gridappsd.simulation.>") is True

    def test_both_wildcards(self):
        assert _is_wildcard_topic("/topic/goss.*.simulation.>") is True

    def test_plain_queue_no_wildcard(self):
        assert _is_wildcard_topic("/queue/goss.gridappsd.process.request.simulation") is False


class TestWildcardToRegex:
    def test_star_matches_one_segment(self):
        pat = _wildcard_to_regex("/topic/goss.gridappsd.field.*")
        assert pat.fullmatch("/topic/goss.gridappsd.field.sub1")
        assert not pat.fullmatch("/topic/goss.gridappsd.field.sub1.sub2")
        assert not pat.fullmatch("/topic/goss.gridappsd.field")

    def test_gt_matches_one_or_more_segments(self):
        pat = _wildcard_to_regex("/topic/goss.gridappsd.simulation.>")
        assert pat.fullmatch("/topic/goss.gridappsd.simulation.output")
        assert pat.fullmatch("/topic/goss.gridappsd.simulation.output.12345")
        assert pat.fullmatch("/topic/goss.gridappsd.simulation.log.99999")
        assert not pat.fullmatch("/topic/goss.gridappsd.simulation")
        assert not pat.fullmatch("/topic/goss.gridappsd")

    def test_star_in_middle(self):
        pat = _wildcard_to_regex("/topic/goss.*.simulation.output")
        assert pat.fullmatch("/topic/goss.gridappsd.simulation.output")
        assert not pat.fullmatch("/topic/goss.foo.bar.simulation.output")

    def test_queue_prefix(self):
        pat = _wildcard_to_regex("/queue/goss.gridappsd.process.request.*")
        assert pat.fullmatch("/queue/goss.gridappsd.process.request.simulation")
        assert pat.fullmatch("/queue/goss.gridappsd.process.request.data")
        assert not pat.fullmatch("/queue/goss.gridappsd.process.request.data.powergrid")

    def test_exact_topic_no_wildcards(self):
        pat = _wildcard_to_regex("/topic/goss.gridappsd.simulation.output.123")
        assert pat.fullmatch("/topic/goss.gridappsd.simulation.output.123")
        assert not pat.fullmatch("/topic/goss.gridappsd.simulation.output.456")

    def test_temp_queue_prefix(self):
        pat = _wildcard_to_regex("/temp-queue/response.*")
        assert pat.fullmatch("/temp-queue/response.abc123")
        assert not pat.fullmatch("/temp-queue/response.abc.def")


class TestCallbackRouterExactMatch:
    """Verify existing exact-match behavior is preserved."""

    def test_exact_topic_callback_fires(self):
        router = CallbackRouter()
        results = Queue()
        router.add_callback("/topic/foo.bar", lambda h, m: results.put((h, m)))
        router.on_message(*_make_msg({"destination": "/topic/foo.bar"}, "hello"))
        sleep(0.15)
        assert not results.empty()
        h, m = results.get()
        assert m == "hello"

    def test_exact_topic_no_match_does_not_fire(self):
        router = CallbackRouter()
        results = Queue()
        router.add_callback("/topic/foo.bar", lambda h, m: results.put((h, m)))
        router.on_message(*_make_msg({"destination": "/topic/foo.baz"}, "hello"))
        sleep(0.15)
        assert results.empty()

    def test_queue_prefix_auto_added(self):
        router = CallbackRouter()
        results = Queue()
        router.add_callback("foo.bar", lambda h, m: results.put((h, m)))
        router.on_message(*_make_msg({"destination": "/queue/foo.bar"}, "hello"))
        sleep(0.15)
        assert not results.empty()

    def test_duplicate_callback_raises(self):
        router = CallbackRouter()
        cb = lambda h, m: None
        router.add_callback("/topic/foo", cb)
        with pytest.raises(ValueError):
            router.add_callback("/topic/foo", cb)

    def test_multiple_callbacks_same_topic(self):
        router = CallbackRouter()
        q1 = Queue()
        q2 = Queue()
        router.add_callback("/topic/foo", lambda h, m: q1.put(m))
        router.add_callback("/topic/foo", lambda h, m: q2.put(m))
        router.on_message(*_make_msg({"destination": "/topic/foo"}, '"msg"'))
        sleep(0.15)
        assert not q1.empty()
        assert not q2.empty()


class TestCallbackRouterWildcard:
    """Test wildcard subscription routing."""

    def test_star_wildcard(self):
        router = CallbackRouter()
        results = Queue()
        router.add_callback("/topic/goss.gridappsd.field.*",
                            lambda h, m: results.put((h, m)))
        router.on_message(
            *_make_msg({"destination": "/topic/goss.gridappsd.field.sub1"}, '"data1"'))
        sleep(0.15)
        assert not results.empty()

    def test_star_wildcard_no_match_two_segments(self):
        router = CallbackRouter()
        results = Queue()
        router.add_callback("/topic/goss.gridappsd.field.*",
                            lambda h, m: results.put((h, m)))
        router.on_message(
            *_make_msg({"destination": "/topic/goss.gridappsd.field.a.b"}, '"data"'))
        sleep(0.15)
        assert results.empty()

    def test_gt_wildcard(self):
        router = CallbackRouter()
        results = Queue()
        router.add_callback("/topic/goss.gridappsd.simulation.>",
                            lambda h, m: results.put((h, m)))
        router.on_message(
            *_make_msg({"destination": "/topic/goss.gridappsd.simulation.output.12345"}, '"data"'))
        sleep(0.15)
        assert not results.empty()

    def test_gt_wildcard_single_trailing_segment(self):
        router = CallbackRouter()
        results = Queue()
        router.add_callback("/topic/goss.gridappsd.simulation.>",
                            lambda h, m: results.put((h, m)))
        router.on_message(
            *_make_msg({"destination": "/topic/goss.gridappsd.simulation.output"}, '"data"'))
        sleep(0.15)
        assert not results.empty()

    def test_gt_wildcard_no_match_no_trailing(self):
        router = CallbackRouter()
        results = Queue()
        router.add_callback("/topic/goss.gridappsd.simulation.>",
                            lambda h, m: results.put((h, m)))
        router.on_message(
            *_make_msg({"destination": "/topic/goss.gridappsd.simulation"}, '"data"'))
        sleep(0.15)
        assert results.empty()

    def test_wildcard_with_queue_prefix(self):
        router = CallbackRouter()
        results = Queue()
        router.add_callback("goss.gridappsd.process.request.*",
                            lambda h, m: results.put((h, m)))
        router.on_message(
            *_make_msg({"destination": "/queue/goss.gridappsd.process.request.simulation"}, '"data"'))
        sleep(0.15)
        assert not results.empty()

    def test_multiple_wildcards_both_match(self):
        router = CallbackRouter()
        q1 = Queue()
        q2 = Queue()
        router.add_callback("/topic/goss.gridappsd.>",
                            lambda h, m: q1.put(m))
        router.add_callback("/topic/goss.gridappsd.simulation.>",
                            lambda h, m: q2.put(m))
        router.on_message(
            *_make_msg({"destination": "/topic/goss.gridappsd.simulation.output.123"}, '"data"'))
        sleep(0.15)
        assert not q1.empty()
        assert not q2.empty()

    def test_exact_takes_priority_over_wildcard(self):
        """When an exact match exists, only exact callbacks fire."""
        router = CallbackRouter()
        q_exact = Queue()
        q_wild = Queue()
        router.add_callback("/topic/goss.gridappsd.field.sub1",
                            lambda h, m: q_exact.put(m))
        router.add_callback("/topic/goss.gridappsd.field.*",
                            lambda h, m: q_wild.put(m))
        router.on_message(
            *_make_msg({"destination": "/topic/goss.gridappsd.field.sub1"}, '"data"'))
        sleep(0.15)
        assert not q_exact.empty()
        assert q_wild.empty()

    def test_remove_wildcard_callback(self):
        router = CallbackRouter()
        results = Queue()
        cb = lambda h, m: results.put(m)
        router.add_callback("/topic/goss.gridappsd.field.*", cb)
        router.remove_callback("/topic/goss.gridappsd.field.*", cb)
        router.on_message(
            *_make_msg({"destination": "/topic/goss.gridappsd.field.sub1"}, '"data"'))
        sleep(0.15)
        assert results.empty()
        assert len(router._wildcard_patterns) == 0

    def test_multiple_callbacks_on_wildcard(self):
        router = CallbackRouter()
        q1 = Queue()
        q2 = Queue()
        router.add_callback("/topic/goss.gridappsd.field.*",
                            lambda h, m: q1.put(m))
        router.add_callback("/topic/goss.gridappsd.field.*",
                            lambda h, m: q2.put(m))
        router.on_message(
            *_make_msg({"destination": "/topic/goss.gridappsd.field.sub1"}, '"data"'))
        sleep(0.15)
        assert not q1.empty()
        assert not q2.empty()
        # Only one pattern entry despite two callbacks
        assert len(router._wildcard_patterns) == 1

    def test_temp_queue_wildcard(self):
        router = CallbackRouter()
        results = Queue()
        router.add_callback("/temp-queue/response.*",
                            lambda h, m: results.put(m))
        router.on_message(
            *_make_msg({"destination": "/temp-queue/response.abc123"}, '"data"'))
        sleep(0.15)
        assert not results.empty()

    def test_partial_remove_keeps_wildcard_pattern(self):
        """Removing one callback should keep the pattern if another remains."""
        router = CallbackRouter()
        q1 = Queue()
        q2 = Queue()
        cb1 = lambda h, m: q1.put(m)
        cb2 = lambda h, m: q2.put(m)
        router.add_callback("/topic/goss.gridappsd.field.*", cb1)
        router.add_callback("/topic/goss.gridappsd.field.*", cb2)
        router.remove_callback("/topic/goss.gridappsd.field.*", cb1)
        # Pattern should still exist
        assert len(router._wildcard_patterns) == 1
        # Remaining callback should still fire
        router.on_message(
            *_make_msg({"destination": "/topic/goss.gridappsd.field.sub1"}, '"data"'))
        sleep(0.15)
        assert q1.empty()
        assert not q2.empty()

    def test_concurrent_add_and_dispatch(self):
        """Thread-safe: add callbacks from threads while messages are dispatched."""
        import threading
        router = CallbackRouter()
        results = Queue()
        errors = Queue()

        def add_callbacks():
            try:
                for i in range(20):
                    router.add_callback(
                        f"/topic/concurrent.test.{i}.*",
                        lambda h, m, idx=i: results.put(idx))
            except Exception as e:
                errors.put(e)

        def send_messages():
            try:
                sleep(0.01)  # let some callbacks register first
                for i in range(20):
                    router.on_message(
                        *_make_msg({"destination": f"/topic/concurrent.test.{i}.data"}, '"msg"'))
            except Exception as e:
                errors.put(e)

        t1 = threading.Thread(target=add_callbacks)
        t2 = threading.Thread(target=send_messages)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)
        sleep(0.3)
        assert errors.empty(), f"Errors during concurrent test: {errors.get()}"
