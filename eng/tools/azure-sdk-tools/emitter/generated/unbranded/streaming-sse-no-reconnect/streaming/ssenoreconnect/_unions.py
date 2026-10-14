# coding=utf-8

from typing import Literal, TYPE_CHECKING, TypeAlias, Union

if TYPE_CHECKING:
    from . import models as _models
UnnamedEvents: TypeAlias = "_models.Info"
ResponseEvents: TypeAlias = Union["_models.ResponseCreated", "_models.ResponseDelta", Literal["[DONE]"]]
RetrievalEvents: TypeAlias = Union["_models.PartialResult", "_models.FinalResult", Literal["[DONE]"]]
ProtocolEvents: TypeAlias = "_models.ProtocolInfo"
DataEvents: TypeAlias = Union["_models.WithEnvelope", "_models.WithEnvelope1"]
