# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License in the project root for
# license information.
# -------------------------------------------------------------------------

from microsoft.opentelemetry._configure import configure_microsoft_opentelemetry

from ._version import VERSION

__all__ = [
    "configure_microsoft_opentelemetry",
]
__version__ = VERSION
