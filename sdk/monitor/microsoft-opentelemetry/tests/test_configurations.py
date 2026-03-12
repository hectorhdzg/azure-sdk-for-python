# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
import unittest
from unittest.mock import patch

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_OFF,
    ALWAYS_ON,
    ParentBased,
    TraceIdRatioBased,
)

from microsoft.opentelemetry._constants import (
    BROWSER_SDK_LOADER_CONFIG_ARG,
    CONNECTION_STRING_ARG,
    DISABLE_LOGGING_ARG,
    DISABLE_METRICS_ARG,
    DISABLE_TRACING_ARG,
    DISTRO_VERSION_ARG,
    ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG,
    ENABLE_A365_EXPORTER_ARG,
    ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG,
    ENABLE_A365_OPENAI_INSTRUMENTATION_ARG,
    ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG,
    ENABLE_AZURE_MONITOR_EXPORTER_ARG,
    ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG,
    ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG,
    ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG,
    ENABLE_LIVE_METRICS_ARG,
    ENABLE_OTLP_EXPORTER_ARG,
    ENABLE_PERFORMANCE_COUNTERS_ARG,
    ENABLE_TRACE_BASED_SAMPLING_ARG,
    INSTRUMENTATION_OPTIONS_ARG,
    LOG_RECORD_PROCESSORS_ARG,
    LOGGER_NAME_ARG,
    LOGGING_FORMATTER_ARG,
    METRIC_READERS_ARG,
    OTLP_ENDPOINT_ARG,
    OTLP_HEADERS_ARG,
    OTLP_PROTOCOL_ARG,
    A365_CLUSTER_CATEGORY_ARG,
    A365_EXPORTER_OPTIONS_ARG,
    A365_TOKEN_RESOLVER_ARG,
    RESOURCE_ARG,
    SAMPLING_ARG,
    SAMPLING_RATIO_ARG,
    SAMPLING_TRACES_PER_SECOND_ARG,
    SAMPLER_TYPE,
    SPAN_PROCESSORS_ARG,
    VIEWS_ARG,
)
from microsoft.opentelemetry._utils.configurations import (
    _get_configurations,
    _is_instrumentation_enabled,
    _get_sampler_from_name,
)
from microsoft.opentelemetry._version import VERSION


# Clear relevant env vars for each test
_ENV_VARS_TO_CLEAR = [
    "APPLICATIONINSIGHTS_CONNECTION_STRING",
    "OTEL_LOGS_EXPORTER",
    "OTEL_METRICS_EXPORTER",
    "OTEL_TRACES_EXPORTER",
    "OTEL_TRACES_SAMPLER",
    "OTEL_TRACES_SAMPLER_ARG",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_EXPORTER_OTLP_PROTOCOL",
    "OTEL_EXPORTER_OTLP_HEADERS",
    "ENABLE_OTLP_EXPORTER",
    "ENABLE_A365_EXPORTER",
    "A365_CLUSTER_CATEGORY",
    "ENABLE_A365_OPENAI_INSTRUMENTATION",
    "ENABLE_A365_LANGCHAIN_INSTRUMENTATION",
    "ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION",
    "ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION",
    "ENABLE_GENAI_OPENAI_INSTRUMENTATION",
    "ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION",
    "ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION",
    "PYTHON_APPLICATIONINSIGHTS_LOGGER_NAME",
    "PYTHON_APPLICATIONINSIGHTS_LOGGING_FORMAT",
    "OTEL_PYTHON_DISABLED_INSTRUMENTATIONS",
    "OTEL_EXPERIMENTAL_RESOURCE_DETECTORS",
]


def _clean_env():
    for var in _ENV_VARS_TO_CLEAR:
        os.environ.pop(var, None)


class TestGetConfigurationsDefaults(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    def test_distro_version_set(self):
        config = _get_configurations()
        self.assertEqual(config[DISTRO_VERSION_ARG], VERSION)

    def test_disable_flags_default_false(self):
        config = _get_configurations()
        self.assertFalse(config[DISABLE_LOGGING_ARG])
        self.assertFalse(config[DISABLE_METRICS_ARG])
        self.assertFalse(config[DISABLE_TRACING_ARG])

    def test_disable_logging_from_env(self):
        os.environ["OTEL_LOGS_EXPORTER"] = "none"
        config = _get_configurations()
        self.assertTrue(config[DISABLE_LOGGING_ARG])

    def test_disable_metrics_from_env(self):
        os.environ["OTEL_METRICS_EXPORTER"] = "none"
        config = _get_configurations()
        self.assertTrue(config[DISABLE_METRICS_ARG])

    def test_disable_tracing_from_env(self):
        os.environ["OTEL_TRACES_EXPORTER"] = "none"
        config = _get_configurations()
        self.assertTrue(config[DISABLE_TRACING_ARG])

    def test_no_azure_monitor_connection_string_by_default(self):
        config = _get_configurations()
        self.assertNotIn(CONNECTION_STRING_ARG, config)

    def test_azure_monitor_connection_string_from_kwarg(self):
        config = _get_configurations(azure_monitor_connection_string="InstrumentationKey=test")
        self.assertEqual(config[CONNECTION_STRING_ARG], "InstrumentationKey=test")

    def test_azure_monitor_connection_string_from_env(self):
        os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"] = "InstrumentationKey=env-test"
        config = _get_configurations()
        self.assertEqual(config[CONNECTION_STRING_ARG], "InstrumentationKey=env-test")

    def test_logger_name_default_empty(self):
        config = _get_configurations()
        self.assertEqual(config[LOGGER_NAME_ARG], "")

    def test_logger_name_from_kwarg(self):
        config = _get_configurations(logger_name="myapp")
        self.assertEqual(config[LOGGER_NAME_ARG], "myapp")

    def test_logger_name_from_env(self):
        os.environ["PYTHON_APPLICATIONINSIGHTS_LOGGER_NAME"] = "envlogger"
        config = _get_configurations()
        self.assertEqual(config[LOGGER_NAME_ARG], "envlogger")

    def test_resource_created_by_default(self):
        config = _get_configurations()
        self.assertIsInstance(config[RESOURCE_ARG], Resource)

    def test_resource_from_kwarg(self):
        resource = Resource.create({"service.name": "myservice"})
        config = _get_configurations(resource=resource)
        self.assertIn("service.name", config[RESOURCE_ARG].attributes)

    def test_default_empty_collections(self):
        config = _get_configurations()
        self.assertEqual(config[SPAN_PROCESSORS_ARG], [])
        self.assertEqual(config[LOG_RECORD_PROCESSORS_ARG], [])
        self.assertEqual(config[METRIC_READERS_ARG], [])
        self.assertEqual(config[VIEWS_ARG], [])

    def test_enable_live_metrics_default_true(self):
        config = _get_configurations()
        self.assertTrue(config[ENABLE_LIVE_METRICS_ARG])

    def test_enable_performance_counters_default_true(self):
        config = _get_configurations()
        self.assertTrue(config[ENABLE_PERFORMANCE_COUNTERS_ARG])

    def test_trace_based_sampling_default_false(self):
        config = _get_configurations()
        self.assertFalse(config[ENABLE_TRACE_BASED_SAMPLING_ARG])

    def test_browser_sdk_loader_default_empty_dict(self):
        config = _get_configurations()
        self.assertEqual(config[BROWSER_SDK_LOADER_CONFIG_ARG], {})


class TestExporterDefaults(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    def test_azure_monitor_auto_enabled_with_connection_string(self):
        config = _get_configurations(azure_monitor_connection_string="InstrumentationKey=test")
        self.assertTrue(config[ENABLE_AZURE_MONITOR_EXPORTER_ARG])

    def test_azure_monitor_disabled_without_connection_string(self):
        config = _get_configurations()
        self.assertFalse(config[ENABLE_AZURE_MONITOR_EXPORTER_ARG])

    def test_azure_monitor_explicit_enable_without_cs_gets_disabled(self):
        config = _get_configurations(enable_azure_monitor_export=True)
        # Should be disabled because no connection string
        self.assertFalse(config[ENABLE_AZURE_MONITOR_EXPORTER_ARG])

    def test_otlp_disabled_by_default(self):
        config = _get_configurations()
        self.assertFalse(config[ENABLE_OTLP_EXPORTER_ARG])

    def test_otlp_enabled_from_env(self):
        os.environ["ENABLE_OTLP_EXPORTER"] = "true"
        config = _get_configurations()
        self.assertTrue(config[ENABLE_OTLP_EXPORTER_ARG])

    def test_otlp_enabled_from_kwarg(self):
        config = _get_configurations(enable_otlp_export=True)
        self.assertTrue(config[ENABLE_OTLP_EXPORTER_ARG])

    def test_otlp_endpoint_from_env(self):
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://collector:4318"
        config = _get_configurations()
        self.assertEqual(config[OTLP_ENDPOINT_ARG], "http://collector:4318")

    def test_otlp_protocol_default(self):
        config = _get_configurations()
        self.assertEqual(config[OTLP_PROTOCOL_ARG], "http/protobuf")

    def test_otlp_protocol_from_env(self):
        os.environ["OTEL_EXPORTER_OTLP_PROTOCOL"] = "grpc"
        config = _get_configurations()
        self.assertEqual(config[OTLP_PROTOCOL_ARG], "grpc")

    def test_a365_disabled_by_default(self):
        config = _get_configurations()
        self.assertFalse(config[ENABLE_A365_EXPORTER_ARG])

    def test_a365_enabled_from_env(self):
        os.environ["ENABLE_A365_EXPORTER"] = "true"
        config = _get_configurations()
        self.assertTrue(config[ENABLE_A365_EXPORTER_ARG])

    def test_a365_cluster_category_default(self):
        config = _get_configurations()
        self.assertEqual(config[A365_CLUSTER_CATEGORY_ARG], "prod")

    def test_a365_cluster_category_from_env(self):
        os.environ["A365_CLUSTER_CATEGORY"] = "staging"
        config = _get_configurations()
        self.assertEqual(config[A365_CLUSTER_CATEGORY_ARG], "staging")

    def test_a365_token_resolver_default_none(self):
        config = _get_configurations()
        self.assertIsNone(config[A365_TOKEN_RESOLVER_ARG])

    def test_a365_exporter_options_default_none(self):
        config = _get_configurations()
        self.assertIsNone(config[A365_EXPORTER_OPTIONS_ARG])


class TestInstrumentationDefaults(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    # A365 instrumentations
    def test_a365_instrumentations_disabled_by_default(self):
        config = _get_configurations()
        self.assertFalse(config[ENABLE_A365_OPENAI_INSTRUMENTATION_ARG])
        self.assertFalse(config[ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG])
        self.assertFalse(config[ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG])
        self.assertFalse(config[ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG])

    def test_a365_openai_instrumentation_from_env(self):
        os.environ["ENABLE_A365_OPENAI_INSTRUMENTATION"] = "true"
        config = _get_configurations()
        self.assertTrue(config[ENABLE_A365_OPENAI_INSTRUMENTATION_ARG])

    def test_a365_langchain_instrumentation_from_env(self):
        os.environ["ENABLE_A365_LANGCHAIN_INSTRUMENTATION"] = "true"
        config = _get_configurations()
        self.assertTrue(config[ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG])

    def test_a365_semantickernel_instrumentation_from_env(self):
        os.environ["ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION"] = "true"
        config = _get_configurations()
        self.assertTrue(config[ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG])

    def test_a365_agentframework_instrumentation_from_env(self):
        os.environ["ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION"] = "true"
        config = _get_configurations()
        self.assertTrue(config[ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG])

    def test_a365_instrumentation_from_kwarg(self):
        config = _get_configurations(enable_a365_openai_instrumentation=True)
        self.assertTrue(config[ENABLE_A365_OPENAI_INSTRUMENTATION_ARG])

    # GenAI instrumentations
    def test_genai_instrumentations_disabled_by_default(self):
        config = _get_configurations()
        self.assertFalse(config[ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG])
        self.assertFalse(config[ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG])
        self.assertFalse(config[ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG])

    def test_genai_openai_instrumentation_from_env(self):
        os.environ["ENABLE_GENAI_OPENAI_INSTRUMENTATION"] = "true"
        config = _get_configurations()
        self.assertTrue(config[ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG])

    def test_genai_openai_agents_instrumentation_from_env(self):
        os.environ["ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION"] = "true"
        config = _get_configurations()
        self.assertTrue(config[ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG])

    def test_genai_langchain_instrumentation_from_env(self):
        os.environ["ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION"] = "true"
        config = _get_configurations()
        self.assertTrue(config[ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG])

    def test_genai_instrumentation_from_kwarg(self):
        config = _get_configurations(enable_genai_openai_instrumentation=True)
        self.assertTrue(config[ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG])


class TestInstrumentationOptions(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    def test_default_instrumentations_enabled(self):
        config = _get_configurations()
        opts = config[INSTRUMENTATION_OPTIONS_ARG]
        self.assertTrue(opts["django"]["enabled"])
        self.assertTrue(opts["flask"]["enabled"])
        self.assertTrue(opts["fastapi"]["enabled"])
        self.assertTrue(opts["requests"]["enabled"])
        self.assertTrue(opts["urllib"]["enabled"])
        self.assertTrue(opts["urllib3"]["enabled"])
        self.assertTrue(opts["psycopg2"]["enabled"])
        self.assertTrue(opts["azure_sdk"]["enabled"])

    def test_disabled_via_env_var(self):
        os.environ["OTEL_PYTHON_DISABLED_INSTRUMENTATIONS"] = "django,flask"
        config = _get_configurations()
        opts = config[INSTRUMENTATION_OPTIONS_ARG]
        self.assertFalse(opts["django"]["enabled"])
        self.assertFalse(opts["flask"]["enabled"])
        self.assertTrue(opts["requests"]["enabled"])

    def test_user_override_via_kwarg(self):
        config = _get_configurations(
            instrumentation_options={"django": {"enabled": False}}
        )
        opts = config[INSTRUMENTATION_OPTIONS_ARG]
        self.assertFalse(opts["django"]["enabled"])
        self.assertTrue(opts["flask"]["enabled"])


class TestIsInstrumentationEnabled(unittest.TestCase):
    def test_enabled(self):
        config = {INSTRUMENTATION_OPTIONS_ARG: {"django": {"enabled": True}}}
        self.assertTrue(_is_instrumentation_enabled(config, "django"))

    def test_disabled(self):
        config = {INSTRUMENTATION_OPTIONS_ARG: {"django": {"enabled": False}}}
        self.assertFalse(_is_instrumentation_enabled(config, "django"))

    def test_missing_lib(self):
        config = {INSTRUMENTATION_OPTIONS_ARG: {}}
        self.assertFalse(_is_instrumentation_enabled(config, "django"))

    def test_no_instrumentation_options(self):
        self.assertFalse(_is_instrumentation_enabled({}, "django"))

    def test_no_enabled_key(self):
        config = {INSTRUMENTATION_OPTIONS_ARG: {"django": {"other": True}}}
        self.assertFalse(_is_instrumentation_enabled(config, "django"))


class TestGetSamplerFromName(unittest.TestCase):
    def test_always_on(self):
        sampler = _get_sampler_from_name("always_on", None)
        self.assertIs(sampler, ALWAYS_ON)

    def test_always_off(self):
        sampler = _get_sampler_from_name("always_off", None)
        self.assertIs(sampler, ALWAYS_OFF)

    def test_trace_id_ratio(self):
        sampler = _get_sampler_from_name("trace_id_ratio", 0.5)
        self.assertIsInstance(sampler, TraceIdRatioBased)

    def test_parentbased_always_on(self):
        sampler = _get_sampler_from_name("parentbased_always_on", None)
        self.assertIsInstance(sampler, ParentBased)

    def test_parentbased_always_off(self):
        sampler = _get_sampler_from_name("parentbased_always_off", None)
        self.assertIsInstance(sampler, ParentBased)

    def test_parentbased_trace_id_ratio(self):
        sampler = _get_sampler_from_name("parentbased_trace_id_ratio", 0.5)
        self.assertIsInstance(sampler, ParentBased)

    def test_unknown_returns_parentbased_always_on(self):
        sampler = _get_sampler_from_name("unknown", None)
        self.assertIsInstance(sampler, ParentBased)


class TestSamplerFromEnv(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    def test_rate_limited_sampler(self):
        os.environ["OTEL_TRACES_SAMPLER"] = "microsoft.rate_limited"
        os.environ["OTEL_TRACES_SAMPLER_ARG"] = "10.0"
        config = _get_configurations()
        self.assertEqual(config[SAMPLING_TRACES_PER_SECOND_ARG], 10.0)

    def test_fixed_percentage_sampler(self):
        os.environ["OTEL_TRACES_SAMPLER"] = "microsoft.fixed_percentage"
        os.environ["OTEL_TRACES_SAMPLER_ARG"] = "0.5"
        config = _get_configurations()
        self.assertEqual(config[SAMPLING_RATIO_ARG], 0.5)

    def test_always_on_sampler(self):
        os.environ["OTEL_TRACES_SAMPLER"] = "always_on"
        config = _get_configurations()
        self.assertEqual(config[SAMPLING_ARG], 1.0)
        self.assertEqual(config[SAMPLER_TYPE], "always_on")

    def test_always_off_sampler(self):
        os.environ["OTEL_TRACES_SAMPLER"] = "always_off"
        config = _get_configurations()
        self.assertEqual(config[SAMPLING_ARG], 0.0)
        self.assertEqual(config[SAMPLER_TYPE], "always_off")

    def test_default_rate_limited_sampler(self):
        config = _get_configurations()
        self.assertEqual(config[SAMPLING_TRACES_PER_SECOND_ARG], 5.0)


if __name__ == "__main__":
    unittest.main()
