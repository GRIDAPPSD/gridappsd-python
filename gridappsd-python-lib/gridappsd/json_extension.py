import dataclasses
import json as _json
from typing import Any, TextIO


@dataclasses.dataclass
class JsonComplex:
    real: float
    imag: float


def jsonDecoderExtension(obj: Any):
    rv = obj
    if isinstance(obj, dict):
        try:
            complexInstance = JsonComplex(**obj)
            rv = complex(complexInstance.real, complexInstance.imag)
        except:
            rv = obj
    return rv


class JsonEncoderExtension(_json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        rv = None
        if isinstance(obj, complex):
            jsonComplexInstance = JsonComplex(
                real = obj.real,
                imag = obj.imag
            )
            rv = dataclasses.asdict(jsonComplexInstance)
        elif dataclasses.is_dataclass(obj):
            rv = dataclasses.asdict(obj)
        else:
            rv = super().default(obj)
        return rv


def dump(data: Any, fo: TextIO):
    rv = _json.dump(data, fo, cls=JsonEncoderExtension)


def dumps(data: Any) -> str:
    rv = _json.dumps(data, cls=JsonEncoderExtension)
    return rv


def load(fo: TextIO) -> Any:
    rv = _json.load(fo, object_hook=jsonDecoderExtension)
    return rv


def loads(data: str) -> Any:
    rv = _json.loads(data, object_hook=jsonDecoderExtension)
    return rv