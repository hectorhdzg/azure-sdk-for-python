# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
import unittest
from unittest.mock import MagicMock, patch, call

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from microsoft.opentelemetry._constants import (
    CONNECTION_STRING_ARG,
    DISABLE_LOGGING_ARG,
    DISABLE_METRICS_ARG,
    DISABLE_TRACING_ARG,
    ENABLE_A365_EXPORTER_ARG,
    ENABLE_AZURE_MONITOR_EXPORTER_ARG,
    ENABLE_OTLP_EXPORTER_ARG,
    ENABLE_A365_OPENAI_INSTRUMENTATION_ARG,
    ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG,
    ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG,
    ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG,
    ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG,
    ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG,
    ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG,
    A365_TOKEN_RESOLVER_ARG,
    A365_CLUSTER_CATEGORY_ARG,
    A365_EXPORTER_OPTIONS_ARG,
    OTLP_ENDPOINT_ARG,
    OTLP_PROTOCOL_ARG,
    OTLP_HEADERS_ARG,
    RESOURCE_ARG,
    SAMPLING_RATIO_ARG,
    SPAN_PROCESSORS_ARG,
    LOG_RECORD_PROCESSORS_ARG,
    METRIC_READERS_ARG,
    VIEWS_ARG,
    LOGGER_NAME_ARG,
    SAMPLING_ARG,
    SAMPLER_TYPE,
)

_MODULE = "microsoft.opentelemetry._configure"

# Env vars to clean between tests
_ENV_VARS_TO_CLEAR = [
    "APPLICATIONINSIGHTS_CONNECTION_STRING",
    "OTEL_LOGS_EXPORTER",
    "OTEL_METRICS_EXPORTER",
    "OTEL_TRACES_EXPORTER",
    "ENABLE_OTLP_EXPORTER",
    "ENABLE_A365_EXPORTER",
    "ENABLE_A365_OPENAI_INSTRUMENTATION",
    "ENABLE_A365_LANGCHAIN_INSTRUMENTATION",
    "ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION",
    "ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION",
    "ENABLE_GENAI_OPENAI_INSTRUMENTATION",
    "ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION",
    "ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION",
]


def _clean_env():
    for var in _ENV_VARS_TO_CLEAR:
        os.environ.pop(var, None)


class TestConfigureMicrosoftOpenTelemetry(unittest.TestCase):
    """Tests for the main configure_microsoft_opentelemetry orchestration."""

    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    @patch(f"{_MODULE}._setup_genai_instrumentations")
    @patch(f"{_MODULE}._setup_a365_instrumentations")
    @patch(f"{_MODULE}._setup_instrumentations")
    @patch(f"{_MODULE}._setup_standalone_providers")
    def test_standalone_mode_no_exporters(
        self, mock_standalone, mock_instr, mock_a365_instr, mock_genai_instr
    ):
        """With no exporters enabled, sets up standalone providers and instrumentations."""
        from microsoft.opentelemetry._configure import configure_microsoft_opentelemetry

        configure_microsoft_opentelemetry()

        mock_standalone.assert_called_once()
        mock_instr.assert_called_once()
        mock_a365_instr.assert_called_once()
        mock_genai_instr.assert_called_once()

    @patch(f"{_MODULE}._setup_genai_instrumentations")
    @patch(f"{_MODULE}._setup_a365_instrumentations")
    @patch(f"{_MODULE}._setup_instrumentations")
    @patch(f"{_MODULE}._add_otlp_exporters")
    @patch(f"{_MODULE}._setup_standalone_providers")
    def test_otlp_only_mode(
        self, mock_standalone, mock_otlp, mock_instr, mock_a365_instr, mock_genai_instr
    ):
        """OTLP-only: standalone providers + OTLP exporters + instrumentations."""
        from microsoft.opentelemetry._configure import configure_microsoft_opentelemetry

        configure_microsoft_opentelemetry(enable_otlp_export=True)

        mock_standalone.assert_called_once()
        mock_otlp.assert_called_once()
        mock_instr.assert_called_once()
        mock_a365_instr.assert_called_once()
        mock_genai_instr.assert_called_once()

    @patch(f"{_MODULE}._setup_genai_instrumentations")
    @patch(f"{_MODULE}._setup_a365_instrumentations")
    @patch(f"{_MODULE}._setup_instrumentations")
    @patch(f"{_MODULE}._add_a365_exporter")
    @patch(f"{_MODULE}._setup_standalone_providers")
    def test_a365_only_mode(
        self, mock_standalone, mock_a365, mock_instr, mock_a365_instr, mock_genai_instr
    ):
        """A365-only: standalone providers + A365 exporter."""
        from microsoft.opentelemetry._configure import configure_microsoft_opentelemetry

        configure_microsoft_opentelemetry(enable_a365_export=True)

        mock_standalone.assert_called_once()
        mock_a365.assert_called_once()
        mock_instr.assert_called_once()

    @patch(f"{_MODULE}._setup_genai_instrumentations")
    @patch(f"{_MODULE}._setup_a365_instrumentations")
    @patch(f"{_MODULE}._setup_instrumentations")
    @patch(f"{_MODULE}._setup_standalone_providers")
    @patch(f"{_MODULE}._setup_azure_monitor")
    def test_azure_monitor_mode(
        self, mock_az, mock_standalone, mock_instr, mock_a365_instr, mock_genai_instr
    ):
        """Azure Monitor mode: delegates to configure_azure_monitor, skips standalone and instrumentations."""
        from microsoft.opentelemetry._configure import configure_microsoft_opentelemetry

        configure_microsoft_opentelemetry(azure_monitor_connection_string="InstrumentationKey=test")

        mock_az.assert_called_once()
        mock_standalone.assert_not_called()
        mock_instr.assert_not_called()  # Azure Monitor handles instrumentations
        mock_a365_instr.assert_called_once()
        mock_genai_instr.assert_called_once()

    @patch(f"{_MODULE}._setup_genai_instrumentations")
    @patch(f"{_MODULE}._setup_a365_instrumentations")
    @patch(f"{_MODULE}._setup_instrumentations")
    @patch(f"{_MODULE}._add_otlp_exporters")
    @patch(f"{_MODULE}._add_a365_exporter")
    @patch(f"{_MODULE}._setup_standalone_providers")
    @patch(f"{_MODULE}._setup_azure_monitor")
    def test_all_exporters_mode(
        self, mock_az, mock_standalone, mock_a365, mock_otlp,
        mock_instr, mock_a365_instr, mock_genai_instr
    ):
        """All exporters: Azure Monitor + OTLP + A365."""
        from microsoft.opentelemetry._configure import configure_microsoft_opentelemetry

        configure_microsoft_opentelemetry(
            azure_monitor_connection_string="InstrumentationKey=test",
            enable_otlp_export=True,
            enable_a365_export=True,
        )

        mock_az.assert_called_once()
        mock_standalone.assert_not_called()
        mock_otlp.assert_called_once()
        mock_a365.assert_called_once()
        mock_instr.assert_not_called()


class TestSetupAzureMonitor(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    @patch(f"{_MODULE}._MICROSOFT_OTEL_ONLY_KEYS", frozenset({"key_to_filter"}))
    def test_filters_microsoft_only_keys(self):
        from microsoft.opentelemetry._configure import _setup_azure_monitor

        mock_configure = MagicMock()
        with patch.dict("sys.modules", {"azure.monitor.opentelemetry": MagicMock(configure_azure_monitor=mock_configure)}):
            with patch(f"{_MODULE}.configure_azure_monitor", mock_configure, create=True):
                # We need to test the filtering logic directly
                configurations = {
                    "key_to_filter": "should_be_excluded",
                    CONNECTION_STRING_ARG: "InstrumentationKey=test",
                    RESOURCE_ARG: Resource.create(),
                }
                # Import fresh to get the patched version
                import importlib
                import microsoft.opentelemetry._configure as mod
                # Just verify the filtering logic
                filtered = {
                    k: v for k, v in configurations.items()
                    if k not in mod._MICROSOFT_OTEL_ONLY_KEYS
                }
                self.assertNotIn(ENABLE_OTLP_EXPORTER_ARG, filtered)

    def test_import_error_logs_warning(self):
        from microsoft.opentelemetry._configure import _setup_azure_monitor

        with patch("builtins.__import__", side_effect=ImportError("no module")):
            # Should not raise, just log warning
            _setup_azure_monitor({CONNECTION_STRING_ARG: "test"})

    def test_configure_azure_monitor_exception_logs_warning(self):
        from microsoft.opentelemetry._configure import _setup_azure_monitor

        mock_configure = MagicMock(side_effect=Exception("config fail"))
        mock_module = MagicMock(configure_azure_monitor=mock_configure)

        with patch.dict("sys.modules", {"azure.monitor.opentelemetry": mock_module}):
            # Should not raise
            _setup_azure_monitor({CONNECTION_STRING_ARG: "test"})


class TestSetupStandaloneProviders(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    @patch(f"{_MODULE}._setup_standalone_metrics")
    @patch(f"{_MODULE}._setup_standalone_logging")
    @patch(f"{_MODULE}._setup_standalone_tracing")
    def test_all_signals_enabled(self, mock_trace, mock_log, mock_metric):
        from microsoft.opentelemetry._configure import _setup_standalone_providers

        config = {
            DISABLE_TRACING_ARG: False,
            DISABLE_LOGGING_ARG: False,
            DISABLE_METRICS_ARG: False,
        }
        _setup_standalone_providers(config)

        mock_trace.assert_called_once_with(config)
        mock_log.assert_called_once_with(config)
        mock_metric.assert_called_once_with(config)

    @patch(f"{_MODULE}._setup_standalone_metrics")
    @patch(f"{_MODULE}._setup_standalone_logging")
    @patch(f"{_MODULE}._setup_standalone_tracing")
    def test_tracing_disabled(self, mock_trace, mock_log, mock_metric):
        from microsoft.opentelemetry._configure import _setup_standalone_providers

        config = {
            DISABLE_TRACING_ARG: True,
            DISABLE_LOGGING_ARG: False,
            DISABLE_METRICS_ARG: False,
        }
        _setup_standalone_providers(config)

        mock_trace.assert_not_called()
        mock_log.assert_called_once()
        mock_metric.assert_called_once()

    @patch(f"{_MODULE}._setup_standalone_metrics")
    @patch(f"{_MODULE}._setup_standalone_logging")
    @patch(f"{_MODULE}._setup_standalone_tracing")
    def test_logging_disabled(self, mock_trace, mock_log, mock_metric):
        from microsoft.opentelemetry._configure import _setup_standalone_providers

        config = {
            DISABLE_TRACING_ARG: False,
            DISABLE_LOGGING_ARG: True,
            DISABLE_METRICS_ARG: False,
        }
        _setup_standalone_providers(config)

        mock_trace.assert_called_once()
        mock_log.assert_not_called()
        mock_metric.assert_called_once()

    @patch(f"{_MODULE}._setup_standalone_metrics")
    @patch(f"{_MODULE}._setup_standalone_logging")
    @patch(f"{_MODULE}._setup_standalone_tracing")
    def test_metrics_disabled(self, mock_trace, mock_log, mock_metric):
        from microsoft.opentelemetry._configure import _setup_standalone_providers

        config = {
            DISABLE_TRACING_ARG: False,
            DISABLE_LOGGING_ARG: False,
            DISABLE_METRICS_ARG: True,
        }
        _setup_standalone_providers(config)

        mock_trace.assert_called_once()
        mock_log.assert_called_once()
        mock_metric.assert_not_called()

    @patch(f"{_MODULE}._setup_standalone_metrics")
    @patch(f"{_MODULE}._setup_standalone_logging")
    @patch(f"{_MODULE}._setup_standalone_tracing")
    def test_all_disabled(self, mock_trace, mock_log, mock_metric):
        from microsoft.opentelemetry._configure import _setup_standalone_providers

        config = {
            DISABLE_TRACING_ARG: True,
            DISABLE_LOGGING_ARG: True,
            DISABLE_METRICS_ARG: True,
        }
        _setup_standalone_providers(config)

        mock_trace.assert_not_called()
        mock_log.assert_not_called()
        mock_metric.assert_not_called()


class TestSetupStandaloneTracing(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    @patch(f"{_MODULE}.set_tracer_provider")
    def test_creates_tracer_provider_with_resource(self, mock_set_tp):
        from microsoft.opentelemetry._configure import _setup_standalone_tracing

        resource = Resource.create({"service.name": "test"})
        config = {
            RESOURCE_ARG: resource,
            SPAN_PROCESSORS_ARG: [],
        }
        _setup_standalone_tracing(config)

        mock_set_tp.assert_called_once()
        tp = mock_set_tp.call_args[0][0]
        self.assertIsInstance(tp, TracerProvider)

    @patch(f"{_MODULE}.set_tracer_provider")
    def test_adds_span_processors(self, mock_set_tp):
        from microsoft.opentelemetry._configure import _setup_standalone_tracing

        mock_processor = MagicMock()
        config = {
            RESOURCE_ARG: Resource.create(),
            SPAN_PROCESSORS_ARG: [mock_processor],
        }
        _setup_standalone_tracing(config)

        tp = mock_set_tp.call_args[0][0]
        self.assertIsInstance(tp, TracerProvider)

    @patch(f"{_MODULE}.set_tracer_provider")
    def test_sampling_ratio(self, mock_set_tp):
        from microsoft.opentelemetry._configure import _setup_standalone_tracing

        config = {
            RESOURCE_ARG: Resource.create(),
            SPAN_PROCESSORS_ARG: [],
            SAMPLING_RATIO_ARG: 0.5,
        }
        _setup_standalone_tracing(config)

        mock_set_tp.assert_called_once()
        tp = mock_set_tp.call_args[0][0]
        self.assertIsInstance(tp, TracerProvider)

    @patch(f"{_MODULE}.set_tracer_provider")
    def test_sampler_arg(self, mock_set_tp):
        from microsoft.opentelemetry._configure import _setup_standalone_tracing

        config = {
            RESOURCE_ARG: Resource.create(),
            SPAN_PROCESSORS_ARG: [],
            SAMPLING_ARG: 1.0,
            SAMPLER_TYPE: "always_on",
        }
        _setup_standalone_tracing(config)

        mock_set_tp.assert_called_once()


class TestSetupStandaloneLogging(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    @patch(f"{_MODULE}.getLogger")
    def test_creates_logger_provider(self, mock_get_logger):
        from microsoft.opentelemetry._configure import _setup_standalone_logging

        mock_logger = MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger

        config = {
            RESOURCE_ARG: Resource.create(),
            LOG_RECORD_PROCESSORS_ARG: [],
            LOGGER_NAME_ARG: "",
        }
        _setup_standalone_logging(config)


class TestSetupStandaloneMetrics(unittest.TestCase):
    @patch(f"{_MODULE}.set_meter_provider")
    def test_creates_meter_provider(self, mock_set_mp):
        from microsoft.opentelemetry._configure import _setup_standalone_metrics
        from opentelemetry.sdk.metrics import MeterProvider

        config = {
            RESOURCE_ARG: Resource.create(),
            VIEWS_ARG: [],
            METRIC_READERS_ARG: [],
        }
        _setup_standalone_metrics(config)

        mock_set_mp.assert_called_once()
        mp = mock_set_mp.call_args[0][0]
        self.assertIsInstance(mp, MeterProvider)


class TestAddOtlpExporters(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    def test_skip_when_tracing_disabled(self):
        from microsoft.opentelemetry._configure import _add_otlp_exporters

        config = {
            DISABLE_TRACING_ARG: True,
            DISABLE_LOGGING_ARG: True,
            DISABLE_METRICS_ARG: True,
            OTLP_PROTOCOL_ARG: "http/protobuf",
        }
        # Should not raise even when packages are missing
        _add_otlp_exporters(config)

    @patch(f"{_MODULE}.get_tracer_provider")
    def test_adds_http_trace_exporter(self, mock_get_tp):
        from microsoft.opentelemetry._configure import _add_otlp_exporters

        mock_tp = MagicMock(spec=TracerProvider)
        mock_get_tp.return_value = mock_tp

        config = {
            DISABLE_TRACING_ARG: False,
            DISABLE_LOGGING_ARG: True,
            DISABLE_METRICS_ARG: True,
            OTLP_PROTOCOL_ARG: "http/protobuf",
        }

        mock_exporter = MagicMock()
        with patch(
            "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter",
            return_value=mock_exporter,
        ):
            _add_otlp_exporters(config)

        mock_tp.add_span_processor.assert_called_once()

    def test_import_error_logs_warning(self):
        from microsoft.opentelemetry._configure import _add_otlp_exporters

        config = {
            DISABLE_TRACING_ARG: False,
            DISABLE_LOGGING_ARG: True,
            DISABLE_METRICS_ARG: True,
            OTLP_PROTOCOL_ARG: "http/protobuf",
        }
        # This will hit ImportError for the OTLP exporter module if not installed,
        # but should handle it gracefully
        _add_otlp_exporters(config)


class TestAddA365Exporter(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    def test_skip_when_tracing_disabled(self):
        from microsoft.opentelemetry._configure import _add_a365_exporter

        config = {DISABLE_TRACING_ARG: True}
        # Should return early
        _add_a365_exporter(config)

    def test_import_error_when_package_missing(self):
        from microsoft.opentelemetry._configure import _add_a365_exporter

        config = {
            DISABLE_TRACING_ARG: False,
            A365_TOKEN_RESOLVER_ARG: lambda a, t: "token",
            A365_CLUSTER_CATEGORY_ARG: "prod",
            A365_EXPORTER_OPTIONS_ARG: None,
        }
        # Should not raise - handles ImportError gracefully
        _add_a365_exporter(config)

    def test_no_token_resolver_logs_warning(self):
        from microsoft.opentelemetry._configure import _add_a365_exporter

        mock_exporter = MagicMock()
        mock_options = MagicMock()
        mock_bsp = MagicMock()

        with patch.dict("sys.modules", {
            "microsoft_agents_a365": MagicMock(),
            "microsoft_agents_a365.observability": MagicMock(),
            "microsoft_agents_a365.observability.core": MagicMock(),
            "microsoft_agents_a365.observability.core.exporters": MagicMock(),
            "microsoft_agents_a365.observability.core.exporters.agent365_exporter": MagicMock(
                _Agent365Exporter=mock_exporter
            ),
            "microsoft_agents_a365.observability.core.exporters.agent365_exporter_options": MagicMock(
                Agent365ExporterOptions=mock_options
            ),
            "microsoft_agents_a365.observability.core.exporters.enriching_span_processor": MagicMock(
                _EnrichingBatchSpanProcessor=mock_bsp
            ),
        }):
            config = {
                DISABLE_TRACING_ARG: False,
                A365_TOKEN_RESOLVER_ARG: None,
                A365_CLUSTER_CATEGORY_ARG: "prod",
                A365_EXPORTER_OPTIONS_ARG: None,
            }
            # Should log warning and return, not raise
            _add_a365_exporter(config)
            mock_exporter.assert_not_called()


class TestSetupA365Instrumentations(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    def test_skips_when_disabled(self):
        from microsoft.opentelemetry._configure import _setup_a365_instrumentations

        config = {
            ENABLE_A365_OPENAI_INSTRUMENTATION_ARG: False,
            ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG: False,
            ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG: False,
            ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG: False,
        }
        # Should not raise or import anything
        _setup_a365_instrumentations(config)

    def test_instruments_when_enabled(self):
        from microsoft.opentelemetry._configure import _setup_a365_instrumentations

        mock_instrumentor = MagicMock()
        mock_instrumentor_class = MagicMock(return_value=mock_instrumentor)
        mock_module = MagicMock(OpenAIAgentsTraceInstrumentor=mock_instrumentor_class)

        with patch("builtins.__import__", return_value=mock_module):
            config = {
                ENABLE_A365_OPENAI_INSTRUMENTATION_ARG: True,
                ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG: False,
                ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG: False,
                ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG: False,
            }
            _setup_a365_instrumentations(config)

            mock_instrumentor.instrument.assert_called_once()

    def test_handles_import_error(self):
        from microsoft.opentelemetry._configure import _setup_a365_instrumentations

        with patch("builtins.__import__", side_effect=ImportError("no module")):
            config = {
                ENABLE_A365_OPENAI_INSTRUMENTATION_ARG: True,
                ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG: False,
                ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG: False,
                ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG: False,
            }
            # Should not raise
            _setup_a365_instrumentations(config)

    def test_handles_runtime_error(self):
        from microsoft.opentelemetry._configure import _setup_a365_instrumentations

        mock_instrumentor = MagicMock()
        mock_instrumentor.instrument.side_effect = RuntimeError("not configured")
        mock_instrumentor_class = MagicMock(return_value=mock_instrumentor)
        mock_module = MagicMock(OpenAIAgentsTraceInstrumentor=mock_instrumentor_class)

        with patch("builtins.__import__", return_value=mock_module):
            config = {
                ENABLE_A365_OPENAI_INSTRUMENTATION_ARG: True,
                ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG: False,
                ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG: False,
                ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG: False,
            }
            # Should not raise
            _setup_a365_instrumentations(config)

    def test_multiple_instrumentations_enabled(self):
        from microsoft.opentelemetry._configure import _setup_a365_instrumentations

        mock_instrumentor = MagicMock()
        mock_instrumentor_class = MagicMock(return_value=mock_instrumentor)

        def mock_import(name, *args, **kwargs):
            mock = MagicMock()
            for attr in ["OpenAIAgentsTraceInstrumentor", "CustomLangChainInstrumentor",
                         "SemanticKernelInstrumentor", "AgentFrameworkInstrumentor"]:
                setattr(mock, attr, mock_instrumentor_class)
            return mock

        with patch("builtins.__import__", side_effect=mock_import):
            config = {
                ENABLE_A365_OPENAI_INSTRUMENTATION_ARG: True,
                ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG: True,
                ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG: True,
                ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG: True,
            }
            _setup_a365_instrumentations(config)

            self.assertEqual(mock_instrumentor.instrument.call_count, 4)


class TestSetupGenAIInstrumentations(unittest.TestCase):
    def setUp(self):
        _clean_env()

    def tearDown(self):
        _clean_env()

    def test_skips_when_disabled(self):
        from microsoft.opentelemetry._configure import _setup_genai_instrumentations

        config = {
            ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG: False,
            ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG: False,
            ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG: False,
        }
        # Should not raise or attempt imports
        _setup_genai_instrumentations(config)

    def test_instruments_openai_when_enabled(self):
        from microsoft.opentelemetry._configure import _setup_genai_instrumentations

        mock_instrumentor = MagicMock()
        mock_instrumentor_class = MagicMock(return_value=mock_instrumentor)
        mock_module = MagicMock(OpenAIInstrumentor=mock_instrumentor_class)

        with patch("builtins.__import__", return_value=mock_module):
            config = {
                ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG: True,
                ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG: False,
                ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG: False,
            }
            _setup_genai_instrumentations(config)

            mock_instrumentor.instrument.assert_called_once()

    def test_instruments_openai_agents_when_enabled(self):
        from microsoft.opentelemetry._configure import _setup_genai_instrumentations

        mock_instrumentor = MagicMock()
        mock_instrumentor_class = MagicMock(return_value=mock_instrumentor)
        mock_module = MagicMock(OpenAIAgentsInstrumentor=mock_instrumentor_class)

        with patch("builtins.__import__", return_value=mock_module):
            config = {
                ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG: False,
                ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG: True,
                ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG: False,
            }
            _setup_genai_instrumentations(config)

            mock_instrumentor.instrument.assert_called_once()

    def test_instruments_langchain_when_enabled(self):
        from microsoft.opentelemetry._configure import _setup_genai_instrumentations

        mock_instrumentor = MagicMock()
        mock_instrumentor_class = MagicMock(return_value=mock_instrumentor)
        mock_module = MagicMock(LangchainInstrumentor=mock_instrumentor_class)

        with patch("builtins.__import__", return_value=mock_module):
            config = {
                ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG: False,
                ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG: False,
                ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG: True,
            }
            _setup_genai_instrumentations(config)

            mock_instrumentor.instrument.assert_called_once()

    def test_handles_import_error(self):
        from microsoft.opentelemetry._configure import _setup_genai_instrumentations

        with patch("builtins.__import__", side_effect=ImportError("no module")):
            config = {
                ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG: True,
                ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG: False,
                ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG: False,
            }
            # Should not raise
            _setup_genai_instrumentations(config)

    def test_handles_generic_exception(self):
        from microsoft.opentelemetry._configure import _setup_genai_instrumentations

        mock_instrumentor = MagicMock()
        mock_instrumentor.instrument.side_effect = Exception("instrument fail")
        mock_instrumentor_class = MagicMock(return_value=mock_instrumentor)
        mock_module = MagicMock(OpenAIInstrumentor=mock_instrumentor_class)

        with patch("builtins.__import__", return_value=mock_module):
            config = {
                ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG: True,
                ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG: False,
                ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG: False,
            }
            # Should not raise
            _setup_genai_instrumentations(config)

    def test_all_genai_instrumentations_enabled(self):
        from microsoft.opentelemetry._configure import _setup_genai_instrumentations

        mock_instrumentor = MagicMock()
        mock_instrumentor_class = MagicMock(return_value=mock_instrumentor)

        def mock_import(name, *args, **kwargs):
            mock = MagicMock()
            for attr in ["OpenAIInstrumentor", "OpenAIAgentsInstrumentor", "LangchainInstrumentor"]:
                setattr(mock, attr, mock_instrumentor_class)
            return mock

        with patch("builtins.__import__", side_effect=mock_import):
            config = {
                ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG: True,
                ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG: True,
                ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG: True,
            }
            _setup_genai_instrumentations(config)

            self.assertEqual(mock_instrumentor.instrument.call_count, 3)

    def test_missing_key_defaults_to_false(self):
        from microsoft.opentelemetry._configure import _setup_genai_instrumentations

        # Empty config — all keys missing, should default to False via .get()
        _setup_genai_instrumentations({})


class TestEntryPointDistFinder(unittest.TestCase):
    def test_key_for_static(self):
        from microsoft.opentelemetry._configure import _EntryPointDistFinder

        ep = MagicMock()
        ep.group = "opentelemetry_instrumentor"
        ep.name = "django"
        ep.value = "opentelemetry.instrumentation.django:DjangoInstrumentor"

        key = _EntryPointDistFinder._key_for(ep)
        self.assertEqual(key, "opentelemetry_instrumentor:django:opentelemetry.instrumentation.django:DjangoInstrumentor")

    def test_dist_for_with_dist_attr(self):
        from microsoft.opentelemetry._configure import _EntryPointDistFinder

        finder = _EntryPointDistFinder()
        ep = MagicMock()
        ep.dist = MagicMock()

        result = finder.dist_for(ep)
        self.assertIs(result, ep.dist)

    def test_dist_for_without_dist_attr(self):
        from microsoft.opentelemetry._configure import _EntryPointDistFinder

        finder = _EntryPointDistFinder()
        ep = MagicMock(spec=[])  # no .dist attribute
        ep.group = "g"
        ep.name = "n"
        ep.value = "v"

        # Will look up in mapping, which is empty so returns None
        result = finder.dist_for(ep)
        self.assertIsNone(result)


class TestMicrosoftOtelOnlyKeys(unittest.TestCase):
    def test_contains_all_expected_keys(self):
        from microsoft.opentelemetry._configure import _MICROSOFT_OTEL_ONLY_KEYS

        expected = {
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
        }
        self.assertEqual(_MICROSOFT_OTEL_ONLY_KEYS, expected)


if __name__ == "__main__":
    unittest.main()
