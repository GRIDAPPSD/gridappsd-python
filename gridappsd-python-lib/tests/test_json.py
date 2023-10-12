from gridappsd import json

def test_json_complex():
    message = {
        "key1": {
            "key2": complex(3.369,4.213),
            "key3": {
                "key4": complex(-5.147,-6.258),
                "key5": {
                    "real": -9.654,
                    "imag": 8.321
                },
            },
            "key6": {
                "real": 7.894,
                "imag": -8.542,
                "garbage": True
            }
        },
        "key7": complex(7.894, -8.542)
    }
    serializedMessage = """{"key1": {"key2": {"real": 3.369, "imag": 4.213}, "key3": {"key4": {"real": -5.147, "imag": -6.258}, "key5": {"real": -9.654, "imag": 8.321}}, "key6": {"real": 7.894, "imag": -8.542, "garbage": true}}, "key7": {"real": 7.894, "imag": -8.542}}"""
    deserializedMessage = {
        "key1": {
            "key2": complex(3.369,4.213),
            "key3": {
                "key4": complex(-5.147,-6.258),
                "key5": complex(-9.654, 8.321),
            },
            "key6": {
                "real": 7.894,
                "imag": -8.542,
                "garbage": True
            }
        },
        "key7": complex(7.894, -8.542)
    }
    encodedStr = json.dumps(message)
    assert encodedStr == serializedMessage
    decodedMessage = json.loads(encodedStr)
    assert decodedMessage == deserializedMessage