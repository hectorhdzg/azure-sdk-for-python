#!/usr/bin/env python

# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
import re

from setuptools import find_packages, setup

PACKAGE_NAME = "microsoft-opentelemetry"
PACKAGE_PPRINT_NAME = "Microsoft OpenTelemetry Distro"

package_folder_path = "microsoft/opentelemetry"

# Version extraction
with open(os.path.join(package_folder_path, "_version.py"), "r") as fd:
    version = re.search(r'^VERSION\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError("Cannot find version information")

setup(
    name=PACKAGE_NAME,
    version=version,
    description="Microsoft {} Client Library for Python".format(PACKAGE_PPRINT_NAME),
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    license="MIT License",
    author="Microsoft Corporation",
    author_email="ascl@microsoft.com",
    url="https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/monitor/microsoft-opentelemetry",
    keywords="azure, microsoft, opentelemetry, observability, monitoring, tracing, otlp, agent365",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
    ],
    zip_safe=False,
    packages=find_packages(
        exclude=[
            "tests",
            "samples",
            "microsoft",
        ]
    ),
    include_package_data=True,
    package_data={
        "pytyped": ["py.typed"],
    },
    python_requires=">=3.9",
    install_requires=[
        # OpenTelemetry SDK
        "opentelemetry-sdk~=1.39",
        "opentelemetry-resource-detector-azure<1.0.0,>=0.1.5",
        "packaging",
        # Azure Monitor
        "azure-monitor-opentelemetry~=1.6.0",
        # OTLP exporters
        "opentelemetry-exporter-otlp-proto-http~=1.39",
        # Standard web/HTTP instrumentations
        "opentelemetry-instrumentation-django~=0.60b0",
        "opentelemetry-instrumentation-fastapi~=0.60b0",
        "opentelemetry-instrumentation-flask~=0.60b0",
        "opentelemetry-instrumentation-psycopg2~=0.60b0",
        "opentelemetry-instrumentation-requests~=0.60b0",
        "opentelemetry-instrumentation-urllib~=0.60b0",
        "opentelemetry-instrumentation-urllib3~=0.60b0",
        # GenAI OTel contrib instrumentations
        "opentelemetry-instrumentation-openai-v2~=2.3b0",
        "opentelemetry-instrumentation-openai-agents~=0.53.0",
        "opentelemetry-instrumentation-langchain~=0.53.0",
        # Agent365 observability
        "microsoft-agents-a365-observability-core>=0.2.0",
        "microsoft-agents-a365-observability-extensions-openai>=0.1.0",
        "microsoft-agents-a365-observability-extensions-langchain>=0.1.0",
        "microsoft-agents-a365-observability-extensions-semantic-kernel>=0.1.0",
        "microsoft-agents-a365-observability-extensions-agent-framework>=0.1.0",
    ],
    extras_require={
        "otlp-grpc": [
            "opentelemetry-exporter-otlp-proto-grpc~=1.39",
        ],
    },
)
