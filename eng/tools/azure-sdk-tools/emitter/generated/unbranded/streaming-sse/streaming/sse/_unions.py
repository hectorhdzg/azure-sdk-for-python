# coding=utf-8

from typing import Literal, TYPE_CHECKING, TypeAlias, Union

if TYPE_CHECKING:
    from .named import models as _named_models1
    from .protocol import models as _protocol_models1
    from .protocol.data import models as _protocol_data_models2
    from .retrieve import models as _retrieve_models1
    from .unnamed import models as _unnamed_models1
UnnamedEvents: TypeAlias = "_unnamed_models1.Info"
ResponseEvents: TypeAlias = Union["_named_models1.ResponseCreated", "_named_models1.ResponseDelta", Literal["[DONE]"]]
RetrievalEvents: TypeAlias = Union[
    "_retrieve_models1.PartialResult", "_retrieve_models1.FinalResult", Literal["[DONE]"]
]
ProtocolEvents: TypeAlias = "_protocol_models1.ProtocolInfo"
DataEvents: TypeAlias = Union["_protocol_data_models2.WithEnvelope", "_protocol_data_models2.WithEnvelope1"]
