# coding=utf-8

from typing import TYPE_CHECKING, TypeAlias, Union

if TYPE_CHECKING:
    from . import models as _models
PetWithEnvelope: TypeAlias = Union["_models.Cat", "_models.Dog"]
PetWithCustomNames: TypeAlias = Union["_models.Cat", "_models.Dog"]
PetInline: TypeAlias = Union["_models.Cat", "_models.Dog"]
PetInlineWithCustomDiscriminator: TypeAlias = Union["_models.Cat", "_models.Dog"]
