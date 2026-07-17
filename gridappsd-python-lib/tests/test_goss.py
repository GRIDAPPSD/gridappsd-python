"""Unit tests for gridappsd.goss.

These tests exercise the pure argument-shape and serialization helpers
directly. They do not require a live stomp broker: GOSS is constructed
with attempt_connection=False where a GOSS/GridAPPSD instance is needed
at all.
"""

import pytest

from gridappsd.goss import _serialize_message, _unpack_stomp_args


class _FakeFrame:
    """Stand in for stomp-py 8.x's Frame object.

    stomp-py 8.x calls a raw listener's on_message/on_error with a single
    object exposing .headers and .body, instead of two positional
    arguments. This fake reproduces that shape without depending on the
    installed stomp-py version actually being 8.x.
    """

    def __init__(self, headers, body):
        self.headers = headers
        self.body = body


class TestUnpackStompArgs:
    """Parametrized coverage of both stomp callback argument shapes."""

    def test_two_positional_args_stomp_pre_8(self):
        headers = {"destination": "/topic/foo", "reply-to": "/temp-queue/bar"}
        body = "hello world"

        unpacked_headers, unpacked_body = _unpack_stomp_args(headers, body)

        assert unpacked_headers == headers
        assert unpacked_body == body

    def test_two_positional_args_preserves_dict_body(self):
        headers = {"destination": "/topic/foo"}
        body = {"key": "value"}

        unpacked_headers, unpacked_body = _unpack_stomp_args(headers, body)

        assert unpacked_headers is headers
        assert unpacked_body is body

    def test_single_frame_object_stomp_8(self):
        headers = {"destination": "/topic/foo", "reply-to": "/temp-queue/bar"}
        body = "hello world"
        frame = _FakeFrame(headers, body)

        unpacked_headers, unpacked_body = _unpack_stomp_args(frame)

        assert unpacked_headers == headers
        assert unpacked_body == body

    def test_single_frame_object_preserves_dict_body(self):
        headers = {"destination": "/topic/foo"}
        body = {"key": "value"}
        frame = _FakeFrame(headers, body)

        unpacked_headers, unpacked_body = _unpack_stomp_args(frame)

        assert unpacked_headers is headers
        assert unpacked_body is body

    def test_single_tuple_falls_back_to_unpacking(self):
        headers = {"destination": "/topic/foo"}
        body = "plain body"

        unpacked_headers, unpacked_body = _unpack_stomp_args((headers, body))

        assert unpacked_headers == headers
        assert unpacked_body == body

    @pytest.mark.parametrize(
        "args,expected_headers,expected_body",
        [
            (({"destination": "/topic/a"}, "body-a"), {"destination": "/topic/a"}, "body-a"),
            (({"destination": "/topic/b"}, {"nested": 1}), {"destination": "/topic/b"}, {"nested": 1}),
        ],
    )
    def test_two_arg_shape_parametrized(self, args, expected_headers, expected_body):
        unpacked_headers, unpacked_body = _unpack_stomp_args(*args)

        assert unpacked_headers == expected_headers
        assert unpacked_body == expected_body

    @pytest.mark.parametrize(
        "headers,body",
        [
            ({"destination": "/topic/c"}, "body-c"),
            ({"destination": "/topic/d"}, {"nested": 2}),
        ],
    )
    def test_frame_shape_parametrized(self, headers, body):
        frame = _FakeFrame(headers, body)

        unpacked_headers, unpacked_body = _unpack_stomp_args(frame)

        assert unpacked_headers == headers
        assert unpacked_body == body


class TestSerializeMessage:
    def test_dict_is_serialized_to_json_string(self):
        result = _serialize_message({"a": 1, "b": 2})

        assert result == '{"a": 1, "b": 2}'

    def test_list_is_serialized_to_json_string(self):
        result = _serialize_message([1, 2, 3])

        assert result == "[1, 2, 3]"

    def test_string_passes_through_unchanged(self):
        result = _serialize_message("already a string")

        assert result == "already a string"

    def test_bytes_pass_through_unchanged(self):
        payload = b"already bytes"

        result = _serialize_message(payload)

        assert result is payload
