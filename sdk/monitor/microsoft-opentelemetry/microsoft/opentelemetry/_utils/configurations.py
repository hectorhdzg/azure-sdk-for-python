# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from logging import getLogger, Formatter
from os import environ
from typing import Any, Dict

from opentelemetry.environment_variables import (
    OTEL_LOGS_EXPORTER,
    OTEL_METRICS_EXPORTER,
    OTEL_TRACES_EXPORTER,
)

try:
    from opentelemetry.instrumentation.environment_variables import (  # type: ignore
        OTEL_PYTHON_DISABLED_INSTRUMENTATIONS,
    )
except ImportError:  # pragma: no cover
    OTEL_PYTHON_DISABLED_INSTRUMENTATIONS = ""
from opentelemetry.sdk.environment_variables import (
    OTEL_EXPERIMENTAL_RESOURCE_DETECTORS,
    OTEL_TRACES_SAMPLER_ARG,
    OTEL_TRACES_SAMPLER,
)
from opentelemetry.sdk.resources import Resource

from opentelemetry.sdk.trace.sampling import (
    TraceIdRatioBased,
    ALWAYS_OFF,
    ALWAYS_ON,
    ParentBased,
)

from microsoft.opentelemetry._constants import (
    _AZURE_APP_SERVICE_RESOURCE_DETECTOR_NAME,
    _AZURE_VM_RESOURCE_DETECTOR_NAME,
    _FULLY_SUPPORTED_INSTRUMENTED_LIBRARIES,
    _PREVIEW_INSTRUMENTED_LIBRARIES,
    BROWSER_SDK_LOADER_CONFIG_ARG,
    CONNECTION_STRING_ARG,
    DISABLE_LOGGING_ARG,
    DISABLE_METRICS_ARG,
    DISABLE_TRACING_ARG,
    DISTRO_VERSION_ARG,
    ENABLE_LIVE_METRICS_ARG,
    ENABLE_PERFORMANCE_COUNTERS_ARG,
    INSTRUMENTATION_OPTIONS_ARG,
    LOGGER_NAME_ARG,
    LOGGER_NAME_ENV_ARG,
    LOGGING_FORMATTER_ARG,
    LOGGING_FORMAT_ENV_ARG,
    RESOURCE_ARG,
    SAMPLING_RATIO_ARG,
    SAMPLING_TRACES_PER_SECOND_ARG,
    SPAN_PROCESSORS_ARG,
    LOG_RECORD_PROCESSORS_ARG,
    METRIC_READERS_ARG,
    VIEWS_ARG,
    RATE_LIMITED_SAMPLER,
    FIXED_PERCENTAGE_SAMPLER,
    ENABLE_TRACE_BASED_SAMPLING_ARG,
    SUPPORTED_OTEL_SAMPLERS,
    ALWAYS_OFF_SAMPLER,
    ALWAYS_ON_SAMPLER,
    TRACE_ID_RATIO_SAMPLER,
    PARENT_BASED_ALWAYS_ON_SAMPLER,
    PARENT_BASED_ALWAYS_OFF_SAMPLER,
    PARENT_BASED_TRACE_ID_RATIO_SAMPLER,
    SAMPLING_ARG,
    SAMPLER_TYPE,
    ENABLE_OTLP_EXPORTER_ARG,
    OTLP_ENDPOINT_ARG,
    OTLP_PROTOCOL_ARG,
    OTLP_HEADERS_ARG,
    ENABLE_AZURE_MONITOR_EXPORTER_ARG,
    ENABLE_A365_EXPORTER_ARG,
    A365_TOKEN_RESOLVER_ARG,
    A365_CLUSTER_CATEGORY_ARG,
    A365_EXPORTER_OPTIONS_ARG,
    ENABLE_A365_OPENAI_INSTRUMENTATION_ARG,
    ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG,
    ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG,
    ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG,
    ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG,
    ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG,
    ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG,
)
from microsoft.opentelemetry._types import ConfigurationValue
from microsoft.opentelemetry._version import VERSION


_INVALID_FLOAT_MESSAGE = "Value of %s must be a float. Defaulting to %s: %s"
_INVALID_TRACES_PER_SECOND_MESSAGE = "Value of %s must be a positive number for traces per second. Defaulting to %s: %s"
_SUPPORTED_RESOURCE_DETECTORS = (
    _AZURE_APP_SERVICE_RESOURCE_DETECTOR_NAME,
    _AZURE_VM_RESOURCE_DETECTOR_NAME,
)

_logger = getLogger(__name__)


def _get_configurations(**kwargs) -> Dict[str, ConfigurationValue]:
    configurations: Dict[str, Any] = {}

    for key, val in kwargs.items():
        configurations[key] = val
    configurations[DISTRO_VERSION_ARG] = VERSION

    _default_disable_logging(configurations)
    _default_disable_metrics(configurations)
    _default_disable_tracing(configurations)
    _default_connection_string(configurations)
    _default_logger_name(configurations)
    _default_logging_formatter(configurations)
    _default_resource(configurations)
    _default_sampling_ratio(configurations)
    _default_instrumentation_options(configurations)
    _default_span_processors(configurations)
    _default_log_record_processors(configurations)
    _default_metric_readers(configurations)
    _default_enable_live_metrics(configurations)
    _default_enable_performance_counters(configurations)
    _default_views(configurations)
    _default_enable_trace_based_sampling(configurations)
    _default_browser_sdk_loader(configurations)
    _default_exporter_options(configurations)

    return configurations


def _default_disable_logging(configurations):
    default = False
    if OTEL_LOGS_EXPORTER in environ:
        if environ[OTEL_LOGS_EXPORTER].lower().strip() == "none":
            default = True
    configurations[DISABLE_LOGGING_ARG] = default


def _default_disable_metrics(configurations):
    default = False
    if OTEL_METRICS_EXPORTER in environ:
        if environ[OTEL_METRICS_EXPORTER].lower().strip() == "none":
            default = True
    configurations[DISABLE_METRICS_ARG] = default


def _default_disable_tracing(configurations):
    default = False
    if OTEL_TRACES_EXPORTER in environ:
        if environ[OTEL_TRACES_EXPORTER].lower().strip() == "none":
            default = True
    configurations[DISABLE_TRACING_ARG] = default


def _default_connection_string(configurations):
    if CONNECTION_STRING_ARG in configurations:
        return
    env_connection_string = environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if env_connection_string is not None:
        configurations[CONNECTION_STRING_ARG] = env_connection_string


def _default_logger_name(configurations):
    if LOGGER_NAME_ARG in configurations:
        return
    if LOGGER_NAME_ENV_ARG in environ:
        configurations[LOGGER_NAME_ARG] = environ[LOGGER_NAME_ENV_ARG]
    else:
        configurations.setdefault(LOGGER_NAME_ARG, "")


def _default_logging_formatter(configurations):
    formatter = configurations.get(LOGGING_FORMATTER_ARG)
    if formatter:
        if not isinstance(formatter, Formatter):
            configurations[LOGGING_FORMATTER_ARG] = None
            return
    elif LOGGING_FORMAT_ENV_ARG in environ:
        try:
            configurations[LOGGING_FORMATTER_ARG] = Formatter(environ[LOGGING_FORMAT_ENV_ARG])
        except Exception as ex:  # pylint: disable=broad-exception-caught
            _logger.warning(
                "Exception occurred when creating logging Formatter from format: %s, %s.",
                environ[LOGGING_FORMAT_ENV_ARG],
                ex,
            )
            configurations[LOGGING_FORMATTER_ARG] = None


def _default_resource(configurations):
    environ.setdefault(OTEL_EXPERIMENTAL_RESOURCE_DETECTORS, ",".join(_SUPPORTED_RESOURCE_DETECTORS))
    if RESOURCE_ARG not in configurations:
        configurations[RESOURCE_ARG] = Resource.create()
    else:
        configurations[RESOURCE_ARG] = Resource.create(configurations[RESOURCE_ARG].attributes)


# pylint: disable=too-many-statements,too-many-branches
def _default_sampling_ratio(configurations):
    default_value = 1.0
    default_value_for_rate_limited_sampler = 5.0
    sampler_type = environ.get(OTEL_TRACES_SAMPLER)
    sampler_arg = environ.get(OTEL_TRACES_SAMPLER_ARG)

    if sampler_type == RATE_LIMITED_SAMPLER:
        try:
            sampler_value = float(sampler_arg) if sampler_arg is not None else default_value_for_rate_limited_sampler
            if sampler_value < 0.0:
                _logger.error("Invalid value for OTEL_TRACES_SAMPLER_ARG. It should be a non-negative number.")
                sampler_value = default_value_for_rate_limited_sampler
            configurations[SAMPLING_TRACES_PER_SECOND_ARG] = sampler_value
        except ValueError as e:
            _logger.error(
                _INVALID_TRACES_PER_SECOND_MESSAGE,
                OTEL_TRACES_SAMPLER_ARG,
                default_value_for_rate_limited_sampler,
                e,
            )
            configurations[SAMPLING_TRACES_PER_SECOND_ARG] = default_value_for_rate_limited_sampler

    elif sampler_type in (FIXED_PERCENTAGE_SAMPLER, "microsoft.fixed.percentage"):
        try:
            sampler_value = float(sampler_arg) if sampler_arg is not None else default_value
            if sampler_value < 0.0 or sampler_value > 1.0:
                _logger.error("Invalid value for OTEL_TRACES_SAMPLER_ARG. It should be a value between 0 and 1.")
                sampler_value = default_value
            configurations[SAMPLING_RATIO_ARG] = sampler_value
        except ValueError as e:
            _logger.error(
                _INVALID_FLOAT_MESSAGE,
                OTEL_TRACES_SAMPLER_ARG,
                default_value,
                e,
            )
            configurations[SAMPLING_RATIO_ARG] = default_value

    elif sampler_type == ALWAYS_ON_SAMPLER:
        configurations[SAMPLING_ARG] = 1.0
        configurations[SAMPLER_TYPE] = ALWAYS_ON_SAMPLER

    elif sampler_type == ALWAYS_OFF_SAMPLER:
        configurations[SAMPLING_ARG] = 0.0
        configurations[SAMPLER_TYPE] = ALWAYS_OFF_SAMPLER

    elif sampler_type == TRACE_ID_RATIO_SAMPLER:
        try:
            sampler_value = float(sampler_arg) if sampler_arg is not None else default_value
            if sampler_value < 0.0 or sampler_value > 1.0:
                _logger.error("Invalid value for OTEL_TRACES_SAMPLER_ARG. It should be a value between 0 and 1.")
                sampler_value = default_value
            configurations[SAMPLING_ARG] = sampler_value
        except ValueError as e:
            _logger.error(
                _INVALID_FLOAT_MESSAGE,
                OTEL_TRACES_SAMPLER_ARG,
                default_value,
                e,
            )
            configurations[SAMPLING_ARG] = default_value
        configurations[SAMPLER_TYPE] = TRACE_ID_RATIO_SAMPLER

    elif sampler_type == PARENT_BASED_ALWAYS_ON_SAMPLER:
        configurations[SAMPLING_ARG] = 1.0
        configurations[SAMPLER_TYPE] = PARENT_BASED_ALWAYS_ON_SAMPLER

    elif sampler_type == PARENT_BASED_ALWAYS_OFF_SAMPLER:
        configurations[SAMPLING_ARG] = 0.0
        configurations[SAMPLER_TYPE] = PARENT_BASED_ALWAYS_OFF_SAMPLER

    elif sampler_type == PARENT_BASED_TRACE_ID_RATIO_SAMPLER:
        try:
            sampler_value = float(sampler_arg) if sampler_arg is not None else default_value
            if sampler_value < 0.0 or sampler_value > 1.0:
                _logger.error("Invalid value for OTEL_TRACES_SAMPLER_ARG. It should be a value between 0 and 1.")
                sampler_value = default_value
            configurations[SAMPLING_ARG] = sampler_value
        except ValueError as e:
            _logger.error(
                _INVALID_FLOAT_MESSAGE,
                OTEL_TRACES_SAMPLER_ARG,
                default_value,
                e,
            )
            configurations[SAMPLING_ARG] = default_value
        configurations[SAMPLER_TYPE] = PARENT_BASED_TRACE_ID_RATIO_SAMPLER

    else:
        if configurations.get(SAMPLING_TRACES_PER_SECOND_ARG) is None:
            configurations[SAMPLING_TRACES_PER_SECOND_ARG] = default_value_for_rate_limited_sampler
        if sampler_type is not None:
            _logger.error(
                "Invalid argument for the sampler to be used for tracing. "
                "Supported values are %s. Defaulting to %s: %s",
                SUPPORTED_OTEL_SAMPLERS,
                RATE_LIMITED_SAMPLER,
                configurations[SAMPLING_TRACES_PER_SECOND_ARG],
            )


def _default_instrumentation_options(configurations):
    otel_disabled_instrumentations = _get_otel_disabled_instrumentations()

    merged_instrumentation_options = {}
    instrumentation_options = configurations.get(INSTRUMENTATION_OPTIONS_ARG, {})
    for lib_name in _FULLY_SUPPORTED_INSTRUMENTED_LIBRARIES:
        disabled_by_env_var = lib_name in otel_disabled_instrumentations
        options = {"enabled": not disabled_by_env_var}
        options.update(instrumentation_options.get(lib_name, {}))
        merged_instrumentation_options[lib_name] = options
    for lib_name in _PREVIEW_INSTRUMENTED_LIBRARIES:
        options = {"enabled": False}
        options.update(instrumentation_options.get(lib_name, {}))
        merged_instrumentation_options[lib_name] = options

    configurations[INSTRUMENTATION_OPTIONS_ARG] = merged_instrumentation_options


def _default_span_processors(configurations):
    configurations.setdefault(SPAN_PROCESSORS_ARG, [])


def _default_log_record_processors(configurations):
    configurations.setdefault(LOG_RECORD_PROCESSORS_ARG, [])


def _default_metric_readers(configurations):
    configurations.setdefault(METRIC_READERS_ARG, [])


def _default_enable_live_metrics(configurations):
    configurations.setdefault(ENABLE_LIVE_METRICS_ARG, True)


def _default_enable_performance_counters(configurations):
    configurations.setdefault(ENABLE_PERFORMANCE_COUNTERS_ARG, True)


def _default_views(configurations):
    configurations.setdefault(VIEWS_ARG, [])


def _default_browser_sdk_loader(configurations):
    from typing import cast
    configurations.setdefault(BROWSER_SDK_LOADER_CONFIG_ARG, cast(Dict[str, Any], {}))


def _default_exporter_options(configurations):
    """Set default exporter options for OTLP, Azure Monitor, and A365.

    Azure Monitor is only enabled when an azure_monitor_connection_string is available
    (via parameter or APPLICATIONINSIGHTS_CONNECTION_STRING env var).
    """
    # Azure Monitor exporter: enable only when connection string is present
    has_connection_string = CONNECTION_STRING_ARG in configurations
    if ENABLE_AZURE_MONITOR_EXPORTER_ARG not in configurations:
        configurations[ENABLE_AZURE_MONITOR_EXPORTER_ARG] = has_connection_string
    elif configurations[ENABLE_AZURE_MONITOR_EXPORTER_ARG] and not has_connection_string:
        _logger.warning(
            "Azure Monitor exporter enabled but no azure_monitor_connection_string provided. "
            "Set azure_monitor_connection_string or APPLICATIONINSIGHTS_CONNECTION_STRING env var. "
            "Disabling Azure Monitor exporter."
        )
        configurations[ENABLE_AZURE_MONITOR_EXPORTER_ARG] = False

    # OTLP exporter: check environment variable or kwarg
    if ENABLE_OTLP_EXPORTER_ARG not in configurations:
        configurations[ENABLE_OTLP_EXPORTER_ARG] = (
            environ.get("ENABLE_OTLP_EXPORTER", "").lower() == "true"
        )
    configurations.setdefault(OTLP_ENDPOINT_ARG, environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"))
    configurations.setdefault(OTLP_PROTOCOL_ARG, environ.get("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf"))
    configurations.setdefault(OTLP_HEADERS_ARG, environ.get("OTEL_EXPORTER_OTLP_HEADERS"))

    # A365 exporter: check environment variable or kwarg
    if ENABLE_A365_EXPORTER_ARG not in configurations:
        configurations[ENABLE_A365_EXPORTER_ARG] = (
            environ.get("ENABLE_A365_EXPORTER", "").lower() == "true"
        )
    configurations.setdefault(A365_TOKEN_RESOLVER_ARG, None)
    configurations.setdefault(A365_CLUSTER_CATEGORY_ARG, environ.get("A365_CLUSTER_CATEGORY", "prod"))
    configurations.setdefault(A365_EXPORTER_OPTIONS_ARG, None)

    # A365 instrumentations: check environment variables or kwargs
    if ENABLE_A365_OPENAI_INSTRUMENTATION_ARG not in configurations:
        configurations[ENABLE_A365_OPENAI_INSTRUMENTATION_ARG] = (
            environ.get("ENABLE_A365_OPENAI_INSTRUMENTATION", "").lower() == "true"
        )
    if ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG not in configurations:
        configurations[ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG] = (
            environ.get("ENABLE_A365_LANGCHAIN_INSTRUMENTATION", "").lower() == "true"
        )
    if ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG not in configurations:
        configurations[ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG] = (
            environ.get("ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION", "").lower() == "true"
        )
    if ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG not in configurations:
        configurations[ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG] = (
            environ.get("ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION", "").lower() == "true"
        )

    # GenAI OTel contrib instrumentations: check environment variables or kwargs
    if ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG not in configurations:
        configurations[ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG] = (
            environ.get("ENABLE_GENAI_OPENAI_INSTRUMENTATION", "").lower() == "true"
        )
    if ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG not in configurations:
        configurations[ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG] = (
            environ.get("ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION", "").lower() == "true"
        )
    if ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG not in configurations:
        configurations[ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG] = (
            environ.get("ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION", "").lower() == "true"
        )

    # Warn if no exporters are enabled at all
    if (
        not configurations[ENABLE_AZURE_MONITOR_EXPORTER_ARG]
        and not configurations[ENABLE_OTLP_EXPORTER_ARG]
        and not configurations[ENABLE_A365_EXPORTER_ARG]
    ):
        _logger.warning(
            "No exporters are enabled. Telemetry will be collected but not exported. "
            "Enable at least one exporter: Azure Monitor (azure_monitor_connection_string), "
            "OTLP (enable_otlp_export=True), or A365 (enable_a365_export=True)."
        )


def _default_enable_trace_based_sampling(configurations):
    configurations.setdefault(ENABLE_TRACE_BASED_SAMPLING_ARG, False)


def _get_otel_disabled_instrumentations():
    disabled_instrumentation = environ.get(OTEL_PYTHON_DISABLED_INSTRUMENTATIONS, "")
    disabled_instrumentation = disabled_instrumentation.split(",")
    disabled_instrumentation = [x.strip() for x in disabled_instrumentation]
    return disabled_instrumentation


def _is_instrumentation_enabled(configurations, lib_name):
    if INSTRUMENTATION_OPTIONS_ARG not in configurations:
        return False
    instrumentation_options = configurations[INSTRUMENTATION_OPTIONS_ARG]
    if lib_name not in instrumentation_options:
        return False
    library_options = instrumentation_options[lib_name]
    if "enabled" not in library_options:
        return False
    return library_options["enabled"] is True


def _get_sampler_from_name(sampler_type, sampler_arg):
    if sampler_type == ALWAYS_ON_SAMPLER:
        return ALWAYS_ON
    if sampler_type == ALWAYS_OFF_SAMPLER:
        return ALWAYS_OFF
    if sampler_type == TRACE_ID_RATIO_SAMPLER:
        ratio = float(sampler_arg) if sampler_arg is not None else 1.0
        return TraceIdRatioBased(ratio)
    if sampler_type == PARENT_BASED_ALWAYS_OFF_SAMPLER:
        return ParentBased(ALWAYS_OFF)
    if sampler_type == PARENT_BASED_TRACE_ID_RATIO_SAMPLER:
        ratio = float(sampler_arg) if sampler_arg is not None else 1.0
        return ParentBased(TraceIdRatioBased(ratio))
    return ParentBased(ALWAYS_ON)
