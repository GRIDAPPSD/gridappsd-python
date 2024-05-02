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
            jsonComplexInstance = JsonComplex(real=obj.real, imag=obj.imag)
            rv = dataclasses.asdict(jsonComplexInstance)
        elif dataclasses.is_dataclass(obj):
            rv = dataclasses.asdict(obj)
        else:
            rv = super().default(obj)
        return rv


def dump(data: Any,
         fo: TextIO,
         *,
         skipkeys=False,
         ensure_ascii=True,
         check_circular=True,
         allow_nan=True,
         indent=None,
         separators=None,
         default=None,
         sort_keys=False,
         **kw):
    rv = _json.dump(data,
                    fo,
                    skipkeys=skipkeys,
                    ensure_ascii=ensure_ascii,
                    check_circular=check_circular,
                    allow_nan=allow_nan,
                    cls=JsonEncoderExtension,
                    indent=indent,
                    separators=separators,
                    default=default,
                    sort_keys=sort_keys,
                    **kw)


def dumps(data: Any,
          *,
          skipkeys=False,
          ensure_ascii=True,
          check_circular=True,
          allow_nan=True,
          indent=None,
          separators=None,
          default=None,
          sort_keys=False,
          **kw) -> str:
    rv = _json.dumps(data,
                     skipkeys=skipkeys,
                     ensure_ascii=ensure_ascii,
                     check_circular=check_circular,
                     allow_nan=allow_nan,
                     cls=JsonEncoderExtension,
                     indent=indent,
                     separators=separators,
                     default=default,
                     sort_keys=sort_keys,
                     **kw)
    return rv


def load(fo: TextIO,
         *,
         cls=None,
         parse_float=None,
         parse_int=None,
         parse_constant=None,
         object_pairs_hook=None,
         **kw) -> Any:
    rv = _json.load(fo,
                    cls=cls,
                    object_hook=jsonDecoderExtension,
                    parse_float=parse_float,
                    parse_int=parse_int,
                    parse_constant=parse_constant,
                    object_pairs_hook=object_pairs_hook,
                    **kw)
    return rv


def loads(data: str,
          *,
          cls=None,
          parse_float=None,
          parse_int=None,
          parse_constant=None,
          object_pairs_hook=None,
          **kw) -> Any:
    rv = _json.loads(data,
                     cls=cls,
                     object_hook=jsonDecoderExtension,
                     parse_float=parse_float,
                     parse_int=parse_int,
                     parse_constant=parse_constant,
                     object_pairs_hook=object_pairs_hook,
                     **kw)
    return rv
