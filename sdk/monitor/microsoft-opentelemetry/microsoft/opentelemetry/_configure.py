# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License in the project root for
# license information.
# --------------------------------------------------------------------------
from functools import cached_property
from logging import getLogger, Formatter
from os import environ
from typing import Any, Dict, List, Optional, cast

from opentelemetry.metrics import get_meter_provider, set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, MetricReader
from opentelemetry.sdk.metrics.view import View
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_tracer_provider, set_tracer_provider
from opentelemetry.util._importlib_metadata import (
    EntryPoint,
    distributions,
    entry_points,
)

from microsoft.opentelemetry._constants import (
    _ALL_SUPPORTED_INSTRUMENTED_LIBRARIES,
    _AZURE_SDK_INSTRUMENTATION_NAME,
    DISABLE_LOGGING_ARG,
    DISABLE_METRICS_ARG,
    DISABLE_TRACING_ARG,
    ENABLE_LIVE_METRICS_ARG,
    ENABLE_PERFORMANCE_COUNTERS_ARG,
    LOGGER_NAME_ARG,
    LOGGING_FORMATTER_ARG,
    RESOURCE_ARG,
    SAMPLING_RATIO_ARG,
    SAMPLING_TRACES_PER_SECOND_ARG,
    SPAN_PROCESSORS_ARG,
    LOG_RECORD_PROCESSORS_ARG,
    METRIC_READERS_ARG,
    VIEWS_ARG,
    ENABLE_TRACE_BASED_SAMPLING_ARG,
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
    CONNECTION_STRING_ARG,
    ENABLE_A365_OPENAI_INSTRUMENTATION_ARG,
    ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG,
    ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG,
    ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG,
    ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG,
    ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG,
    ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG,
)
from microsoft.opentelemetry._types import ConfigurationValue
from microsoft.opentelemetry._utils.configurations import (
    _get_configurations,
    _is_instrumentation_enabled,
    _get_sampler_from_name,
)
from microsoft.opentelemetry._utils.instrumentation import (
    get_dist_dependency_conflicts,
)

_logger = getLogger(__name__)

# Keys that are specific to microsoft-opentelemetry and should not be
# forwarded to configure_azure_monitor()
_MICROSOFT_OTEL_ONLY_KEYS = frozenset({
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
})


def configure_microsoft_opentelemetry(**kwargs) -> None:
    """Configure OpenTelemetry with support for multiple exporters.

    This function sets up OpenTelemetry pipelines for tracing, logging, and metrics,
    with support for three exporter backends:

    - **Azure Monitor**: Uses the full ``azure-monitor-opentelemetry`` distro package
      (enabled by default if azure_monitor_connection_string is provided)
    - **OTLP**: Standard OpenTelemetry Protocol exporter (enabled via ``enable_otlp_export=True``)
    - **Agent365**: Microsoft Agent 365 observability exporter (enabled via ``enable_a365_export=True``)

    When Azure Monitor is enabled, this function delegates to ``configure_azure_monitor()``
    from the ``azure-monitor-opentelemetry`` package, which sets up the full Azure Monitor
    pipeline including live metrics, performance counters, browser SDK loader, samplers,
    and instrumentations. OTLP and A365 exporters are then added to the existing providers.

    When Azure Monitor is disabled, this function creates its own OpenTelemetry providers
    and only configures the OTLP and/or A365 exporters.

    :keyword str azure_monitor_connection_string: Connection string for Application Insights resource.
    :keyword bool enable_otlp_export: Enable OTLP exporter. Defaults to False.
        Also controllable via ``ENABLE_OTLP_EXPORTER=true`` env var.
    :keyword str otlp_endpoint: OTLP collector endpoint. Defaults to ``OTEL_EXPORTER_OTLP_ENDPOINT`` env var.
    :keyword bool enable_a365_export: Enable Agent365 exporter. Defaults to False.
        Also controllable via ``ENABLE_A365_EXPORTER=true`` env var.
    :keyword callable a365_token_resolver: Token resolver callable ``(agent_id, tenant_id) -> token``
        required when A365 exporter is enabled.
    :keyword str a365_cluster_category: A365 cluster category. Defaults to 'prod'.
    :keyword a365_exporter_options: Agent365ExporterOptions for advanced A365 configuration.
    :keyword bool enable_azure_monitor_export: Enable Azure Monitor exporter.
        Auto-enabled when azure_monitor_connection_string is provided.
    :keyword bool enable_live_metrics: Enable live metrics. Defaults to True.
    :keyword bool enable_performance_counters: Enable performance counters. Defaults to True.
    :keyword resource: OpenTelemetry Resource.
    :keyword list span_processors: Additional span processors.
    :keyword list log_record_processors: Additional log record processors.
    :keyword list metric_readers: Additional metric readers.
    :keyword list views: Metric views.
    :keyword float sampling_ratio: Fixed-percentage sampling ratio (0-1).
    :keyword float traces_per_second: Rate-limited sampling target.
    :keyword str logger_name: Logger name for log collection.
    :keyword logging_formatter: Formatter for collected logs.
    :rtype: None
    """
    configurations = _get_configurations(**kwargs)

    enable_azure_monitor = configurations.get(ENABLE_AZURE_MONITOR_EXPORTER_ARG, False)
    enable_otlp = configurations.get(ENABLE_OTLP_EXPORTER_ARG, False)
    enable_a365 = configurations.get(ENABLE_A365_EXPORTER_ARG, False)

    # --- Step 1: If Azure Monitor is enabled, delegate to configure_azure_monitor() ---
    if enable_azure_monitor:
        _setup_azure_monitor(configurations)

    # --- Step 2: If Azure Monitor is NOT enabled, set up standalone OTel providers ---
    if not enable_azure_monitor:
        _setup_standalone_providers(configurations)

    # --- Step 3: Add OTLP exporters to existing providers ---
    if enable_otlp:
        _add_otlp_exporters(configurations)

    # --- Step 4: Add A365 exporter to existing tracer provider ---
    if enable_a365:
        _add_a365_exporter(configurations)

    # --- Step 5: If no Azure Monitor, set up instrumentations ourselves ---
    # (configure_azure_monitor already handles instrumentations when enabled)
    if not enable_azure_monitor:
        _setup_instrumentations(configurations)

    # --- Step 6: Ensure A365 core is initialized if any A365 instrumentation is enabled ---
    # The A365 instrumentors require is_configured() == True, which is set by
    # microsoft_agents_a365.observability.core.configure(). When the A365 *exporter*
    # is disabled, we still need to call configure() so the instrumentors work.
    any_a365_instrumentation = any(
        configurations.get(key, False) for key in (
            ENABLE_A365_OPENAI_INSTRUMENTATION_ARG,
            ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG,
            ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG,
            ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG,
        )
    )
    if any_a365_instrumentation:
        _ensure_a365_core_configured(configurations)

    # --- Step 7: Set up A365 observability instrumentations ---
    # These are Agent365-specific instrumentations for OpenAI, LangChain,
    # Semantic Kernel, and Agent Framework (independent of which exporter is used)
    _setup_a365_instrumentations(configurations)

    # --- Step 7: Set up GenAI OTel contrib instrumentations ---
    # Community OTel instrumentations for OpenAI, OpenAI Agents, and LangChain
    _setup_genai_instrumentations(configurations)


def _setup_azure_monitor(configurations: Dict[str, ConfigurationValue]):
    """Delegate full Azure Monitor setup to the azure-monitor-opentelemetry package."""
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
    except ImportError:
        _logger.warning(
            "azure-monitor-opentelemetry package not installed. "
            "Install with: pip install azure-monitor-opentelemetry "
            "or: pip install microsoft-opentelemetry[azure-monitor]"
        )
        return

    # Build kwargs for configure_azure_monitor, excluding microsoft-otel-only keys
    # Remap azure_monitor_connection_string -> connection_string for upstream API
    azure_monitor_kwargs = {}
    for k, v in configurations.items():
        if k in _MICROSOFT_OTEL_ONLY_KEYS:
            continue
        if k == CONNECTION_STRING_ARG:
            azure_monitor_kwargs["connection_string"] = v
        else:
            azure_monitor_kwargs[k] = v

    try:
        configure_azure_monitor(**azure_monitor_kwargs)
        _logger.info("Azure Monitor configured via azure-monitor-opentelemetry package")
    except Exception as ex:
        _logger.warning("Failed to configure Azure Monitor: %s", ex)


def _setup_standalone_providers(configurations: Dict[str, ConfigurationValue]):
    """Set up OTel providers when Azure Monitor is not enabled."""
    disable_tracing = configurations[DISABLE_TRACING_ARG]
    disable_logging = configurations[DISABLE_LOGGING_ARG]
    disable_metrics = configurations[DISABLE_METRICS_ARG]

    if not disable_tracing:
        _setup_standalone_tracing(configurations)

    if not disable_logging:
        _setup_standalone_logging(configurations)

    if not disable_metrics:
        _setup_standalone_metrics(configurations)


def _setup_standalone_tracing(configurations: Dict[str, ConfigurationValue]):
    """Create a TracerProvider when Azure Monitor is not handling it."""
    resource: Resource = configurations[RESOURCE_ARG]  # type: ignore

    if SAMPLING_ARG in configurations:
        sampler_arg = configurations[SAMPLING_ARG]
        sampler_type = configurations[SAMPLER_TYPE]
        sampler = _get_sampler_from_name(sampler_type, sampler_arg)
        tracer_provider = TracerProvider(sampler=sampler, resource=resource)
    elif SAMPLING_RATIO_ARG in configurations:
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
        tracer_provider = TracerProvider(
            sampler=TraceIdRatioBased(cast(float, configurations[SAMPLING_RATIO_ARG])),
            resource=resource,
        )
    else:
        tracer_provider = TracerProvider(resource=resource)

    for span_processor in configurations[SPAN_PROCESSORS_ARG]:  # type: ignore
        tracer_provider.add_span_processor(span_processor)  # type: ignore

    set_tracer_provider(tracer_provider)


def _setup_standalone_logging(configurations: Dict[str, ConfigurationValue]):
    """Create a LoggerProvider when Azure Monitor is not handling it."""
    try:
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler

        resource: Resource = configurations[RESOURCE_ARG]  # type: ignore
        logger_provider = LoggerProvider(resource=resource)

        for custom_processor in configurations[LOG_RECORD_PROCESSORS_ARG]:  # type: ignore
            logger_provider.add_log_record_processor(custom_processor)  # type: ignore

        set_logger_provider(logger_provider)

        # Set up logging handler
        logger_name: str = configurations[LOGGER_NAME_ARG]  # type: ignore
        logging_formatter: Optional[Formatter] = configurations.get(LOGGING_FORMATTER_ARG)  # type: ignore
        logger = getLogger(logger_name)
        if not any(isinstance(handler, LoggingHandler) for handler in logger.handlers):
            handler = LoggingHandler(logger_provider=logger_provider)
            if logging_formatter:
                try:
                    handler.setFormatter(logging_formatter)
                except Exception as ex:
                    _logger.warning("Failed to set logging formatter: %s", ex)
            logger.addHandler(handler)

        # Setup Events
        try:
            from opentelemetry._events import _set_event_logger_provider
            from opentelemetry.sdk._events import EventLoggerProvider
            _set_event_logger_provider(EventLoggerProvider(logger_provider), False)
        except ImportError:
            _logger.debug("OpenTelemetry Events API not available")

    except ImportError as ex:
        _logger.warning("Failed to set up logging pipeline: %s", ex)


def _setup_standalone_metrics(configurations: Dict[str, ConfigurationValue]):
    """Create a MeterProvider when Azure Monitor is not handling it."""
    resource: Resource = configurations[RESOURCE_ARG]  # type: ignore
    views: List[View] = configurations[VIEWS_ARG]  # type: ignore
    readers: list[MetricReader] = configurations[METRIC_READERS_ARG]  # type: ignore

    meter_provider = MeterProvider(
        metric_readers=readers,
        resource=resource,
        views=views,
    )
    set_meter_provider(meter_provider)


def _add_otlp_exporters(configurations: Dict[str, ConfigurationValue]):
    """Add OTLP exporters to the existing providers (set up by Azure Monitor or standalone)."""
    disable_tracing = configurations[DISABLE_TRACING_ARG]
    disable_logging = configurations[DISABLE_LOGGING_ARG]
    disable_metrics = configurations[DISABLE_METRICS_ARG]

    otlp_kwargs: Dict[str, Any] = {}
    otlp_endpoint = configurations.get(OTLP_ENDPOINT_ARG)
    if otlp_endpoint:
        otlp_kwargs["endpoint"] = otlp_endpoint
    otlp_protocol = configurations.get(OTLP_PROTOCOL_ARG, "http/protobuf")

    # --- OTLP Trace Exporter ---
    if not disable_tracing:
        try:
            if otlp_protocol == "grpc":
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter as GrpcOTLPSpanExporter,
                )
                otlp_trace_exporter = GrpcOTLPSpanExporter(**otlp_kwargs)
            else:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                    OTLPSpanExporter as HttpOTLPSpanExporter,
                )
                otlp_trace_exporter = HttpOTLPSpanExporter(**otlp_kwargs)

            tracer_provider = get_tracer_provider()
            if isinstance(tracer_provider, TracerProvider):
                tracer_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
                _logger.info("OTLP trace exporter added (protocol=%s)", otlp_protocol)
            else:
                _logger.warning("Cannot add OTLP trace exporter: TracerProvider is not an SDK TracerProvider")
        except ImportError:
            _logger.warning(
                "OTLP exporter packages not installed. Install opentelemetry-exporter-otlp-proto-http "
                "or opentelemetry-exporter-otlp-proto-grpc"
            )
        except Exception as ex:
            _logger.warning("Failed to configure OTLP trace exporter: %s", ex)

    # --- OTLP Log Exporter ---
    if not disable_logging:
        try:
            from opentelemetry._logs import get_logger_provider
            from opentelemetry.sdk._logs import LoggerProvider
            from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

            if otlp_protocol == "grpc":
                from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
                    OTLPLogExporter as GrpcOTLPLogExporter,
                )
                otlp_log_exporter = GrpcOTLPLogExporter(**otlp_kwargs)
            else:
                from opentelemetry.exporter.otlp.proto.http._log_exporter import (
                    OTLPLogExporter as HttpOTLPLogExporter,
                )
                otlp_log_exporter = HttpOTLPLogExporter(**otlp_kwargs)

            logger_provider = get_logger_provider()
            if isinstance(logger_provider, LoggerProvider):
                logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
                _logger.info("OTLP log exporter added (protocol=%s)", otlp_protocol)
            else:
                _logger.warning("Cannot add OTLP log exporter: LoggerProvider is not an SDK LoggerProvider")
        except ImportError:
            _logger.warning("OTLP log exporter packages not installed")
        except Exception as ex:
            _logger.warning("Failed to configure OTLP log exporter: %s", ex)

    # --- OTLP Metric Exporter ---
    if not disable_metrics:
        try:
            if otlp_protocol == "grpc":
                from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                    OTLPMetricExporter as GrpcOTLPMetricExporter,
                )
                otlp_metric_exporter = GrpcOTLPMetricExporter(**otlp_kwargs)
            else:
                from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
                    OTLPMetricExporter as HttpOTLPMetricExporter,
                )
                otlp_metric_exporter = HttpOTLPMetricExporter(**otlp_kwargs)

            meter_provider = get_meter_provider()
            if isinstance(meter_provider, MeterProvider):
                reader = PeriodicExportingMetricReader(otlp_metric_exporter)
                # MeterProvider doesn't support adding readers after creation,
                # so we log a warning if Azure Monitor already created the provider
                _logger.info("OTLP metric exporter configured (protocol=%s)", otlp_protocol)
                # For standalone mode, readers are added before MeterProvider creation.
                # When Azure Monitor is active, metrics go through Azure Monitor's reader;
                # the OTLP metric reader needs to be configured before provider creation.
                _logger.debug(
                    "Note: OTLP metric reader works best when Azure Monitor is disabled. "
                    "When Azure Monitor is active, consider passing metric_readers=[...] "
                    "to include OTLP reader at provider creation time."
                )
            else:
                _logger.warning("Cannot add OTLP metric exporter: MeterProvider is not an SDK MeterProvider")
        except ImportError:
            _logger.warning("OTLP metric exporter packages not installed")
        except Exception as ex:
            _logger.warning("Failed to configure OTLP metric exporter: %s", ex)


def _add_a365_exporter(configurations: Dict[str, ConfigurationValue]):
    """Add Agent365 exporter to the existing tracer provider."""
    if configurations.get(DISABLE_TRACING_ARG):
        return

    try:
        from microsoft_agents_a365.observability.core.exporters.agent365_exporter import _Agent365Exporter
        from microsoft_agents_a365.observability.core.exporters.agent365_exporter_options import (
            Agent365ExporterOptions,
        )
        from microsoft_agents_a365.observability.core.exporters.enriching_span_processor import (
            _EnrichingBatchSpanProcessor,
        )

        a365_options = configurations.get(A365_EXPORTER_OPTIONS_ARG)
        token_resolver = configurations.get(A365_TOKEN_RESOLVER_ARG)
        cluster_category = configurations.get(A365_CLUSTER_CATEGORY_ARG, "prod")

        if a365_options is not None:
            token_resolver = a365_options.token_resolver
            cluster_category = a365_options.cluster_category

        if token_resolver is None:
            _logger.warning("A365 exporter enabled but no token_resolver provided, skipping")
            return

        a365_exporter = _Agent365Exporter(
            token_resolver=token_resolver,
            cluster_category=cluster_category,
        )
        batch_kwargs = {}
        if a365_options is not None:
            batch_kwargs = {
                "max_queue_size": a365_options.max_queue_size,
                "schedule_delay_millis": a365_options.scheduled_delay_ms,
                "export_timeout_millis": a365_options.exporter_timeout_ms,
                "max_export_batch_size": a365_options.max_export_batch_size,
            }

        tracer_provider = get_tracer_provider()
        if isinstance(tracer_provider, TracerProvider):
            a365_bsp = _EnrichingBatchSpanProcessor(a365_exporter, **batch_kwargs)
            tracer_provider.add_span_processor(a365_bsp)
            _logger.info("Agent365 trace exporter added to existing TracerProvider")
        else:
            _logger.warning("Cannot add A365 exporter: TracerProvider is not an SDK TracerProvider")

    except ImportError:
        _logger.warning(
            "microsoft-agents-a365-observability-core not installed, skipping A365 traces. "
            "Install with: pip install microsoft-agents-a365-observability-core"
        )
    except Exception as ex:
        _logger.warning("Failed to configure Agent365 trace exporter: %s", ex)


def _ensure_a365_core_configured(configurations: Dict[str, ConfigurationValue]):
    """Ensure A365 observability core is initialized.

    The A365 instrumentors (AgentFrameworkInstrumentor, OpenAIAgentsTraceInstrumentor, etc.)
    require microsoft_agents_a365.observability.core.configure() to have been called.
    When the A365 exporter is not enabled, we still need to call configure() with a
    no-op token resolver so the instrumentors can attach to the existing TracerProvider.
    """
    try:
        from microsoft_agents_a365.observability.core import configure as a365_configure, is_configured

        if is_configured():
            return

        token_resolver = configurations.get(A365_TOKEN_RESOLVER_ARG)
        if token_resolver is None:
            token_resolver = lambda agent_id, tenant_id: None  # noqa: E731

        service_name = environ.get("OTEL_SERVICE_NAME", "unknown_service")
        service_namespace = environ.get("OTEL_SERVICE_NAMESPACE", "")

        a365_configure(
            service_name=service_name,
            service_namespace=service_namespace,
            token_resolver=token_resolver,
        )
        _logger.info("A365 observability core initialized for instrumentations")
    except ImportError:
        _logger.warning("microsoft-agents-a365-observability-core not installed, cannot initialize A365 core")
    except Exception as ex:
        _logger.warning("Failed to initialize A365 observability core: %s", ex)


def _setup_a365_instrumentations(configurations: Dict[str, ConfigurationValue]):
    """Set up Agent365 observability extension instrumentations.

    These instrumentations add span enrichment and tracing for specific
    AI frameworks (OpenAI Agents SDK, LangChain, Semantic Kernel, Agent Framework).
    They require the A365 observability core to be configured first.
    """
    # Check if any A365 instrumentation is enabled
    instrumentors = [
        (
            ENABLE_A365_OPENAI_INSTRUMENTATION_ARG,
            "microsoft_agents_a365.observability.extensions.openai",
            "OpenAIAgentsTraceInstrumentor",
            "microsoft-agents-a365-observability-extensions-openai",
        ),
        (
            ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG,
            "microsoft_agents_a365.observability.extensions.langchain",
            "CustomLangChainInstrumentor",
            "microsoft-agents-a365-observability-extensions-langchain",
        ),
        (
            ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG,
            "microsoft_agents_a365.observability.extensions.semantickernel.trace_instrumentor",
            "SemanticKernelInstrumentor",
            "microsoft-agents-a365-observability-extensions-semantic-kernel",
        ),
        (
            ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG,
            "microsoft_agents_a365.observability.extensions.agentframework",
            "AgentFrameworkInstrumentor",
            "microsoft-agents-a365-observability-extensions-agent-framework",
        ),
    ]

    for config_key, module_path, class_name, pip_package in instrumentors:
        if not configurations.get(config_key, False):
            continue
        try:
            module = __import__(module_path, fromlist=[class_name])
            instrumentor_class = getattr(module, class_name)
            instrumentor_class().instrument(skip_dep_check=True)
            _logger.info("A365 %s instrumentation enabled", class_name)
        except ImportError:
            _logger.warning(
                "%s not installed. Install with: pip install %s "
                "or: pip install microsoft-opentelemetry[a365-all]",
                pip_package,
                pip_package,
            )
        except RuntimeError as ex:
            _logger.warning(
                "A365 %s requires A365 observability core to be configured first. "
                "Enable A365 exporter (enable_a365_export=True) or configure "
                "microsoft_agents_a365.observability.core.configure() before calling "
                "configure_microsoft_opentelemetry(). Error: %s",
                class_name,
                ex,
            )
        except Exception as ex:
            _logger.warning("Failed to set up A365 %s instrumentation: %s", class_name, ex)


def _setup_genai_instrumentations(configurations: Dict[str, ConfigurationValue]):
    """Set up OpenTelemetry GenAI contrib instrumentations.

    These are community instrumentations from opentelemetry-python-contrib
    for OpenAI, OpenAI Agents SDK, and LangChain.
    """
    instrumentors = [
        (
            ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG,
            "opentelemetry.instrumentation.openai_v2",
            "OpenAIInstrumentor",
            "opentelemetry-instrumentation-openai-v2",
        ),
        (
            ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG,
            "opentelemetry.instrumentation.openai_agents",
            "OpenAIAgentsInstrumentor",
            "opentelemetry-instrumentation-openai-agents",
        ),
        (
            ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG,
            "opentelemetry.instrumentation.langchain",
            "LangchainInstrumentor",
            "opentelemetry-instrumentation-langchain",
        ),
    ]

    for config_key, module_path, class_name, pip_package in instrumentors:
        if not configurations.get(config_key, False):
            continue
        try:
            module = __import__(module_path, fromlist=[class_name])
            instrumentor_class = getattr(module, class_name)
            instrumentor_class().instrument()
            _logger.info("GenAI %s instrumentation enabled", class_name)
        except ImportError:
            _logger.warning(
                "%s not installed. Install with: pip install %s "
                "or: pip install microsoft-opentelemetry[genai-all]",
                pip_package,
                pip_package,
            )
        except Exception as ex:
            _logger.warning("Failed to set up GenAI %s instrumentation: %s", class_name, ex)


class _EntryPointDistFinder:
    @cached_property
    def _mapping(self):
        return {self._key_for(ep): dist for dist in distributions() for ep in dist.entry_points}

    def dist_for(self, entry_point: EntryPoint):
        dist = getattr(entry_point, "dist", None)
        if dist:
            return dist
        return self._mapping.get(self._key_for(entry_point))

    @staticmethod
    def _key_for(entry_point: EntryPoint):
        return f"{entry_point.group}:{entry_point.name}:{entry_point.value}"


def _setup_instrumentations(configurations: Dict[str, ConfigurationValue]):
    """Set up instrumentations (only called when Azure Monitor is not handling them)."""
    entry_point_finder = _EntryPointDistFinder()
    for entry_point in entry_points(group="opentelemetry_instrumentor"):
        lib_name = entry_point.name
        if lib_name not in _ALL_SUPPORTED_INSTRUMENTED_LIBRARIES:
            continue
        if not _is_instrumentation_enabled(configurations, lib_name):
            _logger.debug("Instrumentation skipped for library %s", entry_point.name)
            continue
        try:
            entry_point_dist = entry_point_finder.dist_for(entry_point)  # type: ignore
            conflict = get_dist_dependency_conflicts(entry_point_dist)  # type: ignore
            if conflict:
                _logger.debug("Skipping instrumentation %s: %s", entry_point.name, conflict)
                continue
            instrumentor: Any = entry_point.load()
            instrumentor().instrument(skip_dep_check=True)
        except Exception as ex:
            _logger.warning("Exception occurred when instrumenting: %s.", lib_name, exc_info=ex)

    # Set up Azure SDK tracing
    if _is_instrumentation_enabled(configurations, _AZURE_SDK_INSTRUMENTATION_NAME):
        try:
            from azure.core.settings import settings
            from azure.core.tracing.ext.opentelemetry_span import OpenTelemetrySpan
            settings.tracing_implementation = OpenTelemetrySpan
        except ImportError:
            _logger.debug("Azure SDK tracing not available")
        except Exception as ex:
            _logger.warning("Failed to set Azure SDK tracing: %s", ex)

    _setup_additional_azure_sdk_instrumentations(configurations)


def _setup_additional_azure_sdk_instrumentations(configurations: Dict[str, ConfigurationValue]):
    if _AZURE_SDK_INSTRUMENTATION_NAME not in _ALL_SUPPORTED_INSTRUMENTED_LIBRARIES:
        return
    if not _is_instrumentation_enabled(configurations, _AZURE_SDK_INSTRUMENTATION_NAME):
        return

    instrumentors = [
        ("azure.ai.inference.tracing", "AIInferenceInstrumentor"),
        ("azure.ai.agents.telemetry", "AIAgentsInstrumentor"),
        ("azure.ai.projects.telemetry", "AIProjectInstrumentor"),
    ]

    for module_path, class_name in instrumentors:
        try:
            module = __import__(module_path, fromlist=[class_name])
            instrumentor_class = getattr(module, class_name)
            instrumentor_class().instrument()
        except Exception:
            _logger.debug("Failed to instrument %s.%s", module_path, class_name)
