# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

# --------------------Distro Configuration------------------------------------------

CONNECTION_STRING_ARG = "azure_monitor_connection_string"
ENABLE_LIVE_METRICS_ARG = "enable_live_metrics"
DISABLE_AZURE_CORE_TRACING_ARG = "disable_azure_core_tracing"
DISABLE_LOGGING_ARG = "disable_logging"
DISABLE_METRICS_ARG = "disable_metrics"
DISABLE_TRACING_ARG = "disable_tracing"
ENABLE_PERFORMANCE_COUNTERS_ARG = "enable_performance_counters"
DISTRO_VERSION_ARG = "distro_version"
LOGGER_NAME_ARG = "logger_name"
LOGGING_FORMATTER_ARG = "logging_formatter"
INSTRUMENTATION_OPTIONS_ARG = "instrumentation_options"
RESOURCE_ARG = "resource"
SAMPLING_RATIO_ARG = "sampling_ratio"
SPAN_PROCESSORS_ARG = "span_processors"
LOG_RECORD_PROCESSORS_ARG = "log_record_processors"
METRIC_READERS_ARG = "metric_readers"
VIEWS_ARG = "views"
RATE_LIMITED_SAMPLER = "microsoft.rate_limited"
FIXED_PERCENTAGE_SAMPLER = "microsoft.fixed_percentage"
SAMPLING_TRACES_PER_SECOND_ARG = "traces_per_second"
ENABLE_TRACE_BASED_SAMPLING_ARG = "enable_trace_based_sampling_for_logs"
BROWSER_SDK_LOADER_CONFIG_ARG = "browser_sdk_loader_config"
SAMPLER_TYPE = "sampler_type"
SAMPLING_ARG = "sampling_arg"
ALWAYS_ON_SAMPLER = "always_on"
ALWAYS_OFF_SAMPLER = "always_off"
TRACE_ID_RATIO_SAMPLER = "trace_id_ratio"
PARENT_BASED_ALWAYS_ON_SAMPLER = "parentbased_always_on"
PARENT_BASED_ALWAYS_OFF_SAMPLER = "parentbased_always_off"
PARENT_BASED_TRACE_ID_RATIO_SAMPLER = "parentbased_trace_id_ratio"
SUPPORTED_OTEL_SAMPLERS = (
    RATE_LIMITED_SAMPLER,
    FIXED_PERCENTAGE_SAMPLER,
    ALWAYS_ON_SAMPLER,
    ALWAYS_OFF_SAMPLER,
    TRACE_ID_RATIO_SAMPLER,
    PARENT_BASED_ALWAYS_ON_SAMPLER,
    PARENT_BASED_ALWAYS_OFF_SAMPLER,
    PARENT_BASED_TRACE_ID_RATIO_SAMPLER,
)

# --------------------Exporter Configuration------------------------------------------

# OTLP Exporter
ENABLE_OTLP_EXPORTER_ARG = "enable_otlp_export"
OTLP_ENDPOINT_ARG = "otlp_endpoint"
OTLP_PROTOCOL_ARG = "otlp_protocol"
OTLP_HEADERS_ARG = "otlp_headers"

# Azure Monitor Exporter
ENABLE_AZURE_MONITOR_EXPORTER_ARG = "enable_azure_monitor_export"

# Agent365 Exporter
ENABLE_A365_EXPORTER_ARG = "enable_a365_export"
A365_TOKEN_RESOLVER_ARG = "a365_token_resolver"
A365_CLUSTER_CATEGORY_ARG = "a365_cluster_category"
A365_EXPORTER_OPTIONS_ARG = "a365_exporter_options"

# Agent365 Instrumentations
ENABLE_A365_OPENAI_INSTRUMENTATION_ARG = "enable_a365_openai_instrumentation"
ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG = "enable_a365_langchain_instrumentation"
ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG = "enable_a365_semantickernel_instrumentation"
ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG = "enable_a365_agentframework_instrumentation"

# GenAI OTel Contrib Instrumentations
ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG = "enable_genai_openai_instrumentation"
ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG = "enable_genai_openai_agents_instrumentation"
ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG = "enable_genai_langchain_instrumentation"

# --------------------Autoinstrumentation Configuration------------------------------------------

LOG_EXPORTER_NAMES_ARG = "log_exporter_names"
METRIC_EXPORTER_NAMES_ARG = "metric_exporter_names"
SAMPLER_ARG = "sampler"
TRACE_EXPORTER_NAMES_ARG = "trace_exporter_names"

LOGGER_NAME_ENV_ARG = "PYTHON_APPLICATIONINSIGHTS_LOGGER_NAME"
LOGGING_FORMAT_ENV_ARG = "PYTHON_APPLICATIONINSIGHTS_LOGGING_FORMAT"


# --------------------Diagnostic/status logging------------------------------

_LOG_PATH_LINUX = "/var/log/applicationinsights"
_LOG_PATH_WINDOWS = "\\LogFiles\\ApplicationInsights"
_PREVIEW_ENTRY_POINT_WARNING = "Autoinstrumentation for the Microsoft OpenTelemetry Distro is in preview."


# --------------------Instrumentations------------------------------

# Opt-out
_AZURE_SDK_INSTRUMENTATION_NAME = "azure_sdk"
_FULLY_SUPPORTED_INSTRUMENTED_LIBRARIES = (
    _AZURE_SDK_INSTRUMENTATION_NAME,
    "django",
    "fastapi",
    "flask",
    "psycopg2",
    "requests",
    "urllib",
    "urllib3",
)
# Opt-in
_PREVIEW_INSTRUMENTED_LIBRARIES = ()
_ALL_SUPPORTED_INSTRUMENTED_LIBRARIES = _FULLY_SUPPORTED_INSTRUMENTED_LIBRARIES + _PREVIEW_INSTRUMENTED_LIBRARIES

_AZURE_APP_SERVICE_RESOURCE_DETECTOR_NAME = "azure_app_service"
_AZURE_VM_RESOURCE_DETECTOR_NAME = "azure_vm"
