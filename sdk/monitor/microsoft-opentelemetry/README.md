# Microsoft OpenTelemetry Distro for Python

A unified OpenTelemetry distribution that configures tracing, logging, and metrics for multiple backends with a single call to `configure_microsoft_opentelemetry()`.

## Installation

```bash
pip install microsoft-opentelemetry
```

That's it. All exporters and instrumentations are included out of the box:

- **Azure Monitor** (Application Insights)
- **OTLP** (HTTP/protobuf)
- **Agent365** (core + OpenAI, LangChain, Semantic Kernel, Agent Framework extensions)
- **GenAI instrumentations** (OpenAI, OpenAI Agents, LangChain)
- **Standard web instrumentations** (Django, FastAPI, Flask, Requests, urllib, urllib3, psycopg2)

The only optional extra is gRPC for OTLP:

```bash
pip install microsoft-opentelemetry[otlp-grpc]
```

---

## Quick Start

### Minimal — Azure Monitor

```python
from microsoft.opentelemetry import configure_microsoft_opentelemetry

configure_microsoft_opentelemetry(
    azure_monitor_connection_string="InstrumentationKey=...;IngestionEndpoint=...",
)
```

Azure Monitor is auto-enabled when `azure_monitor_connection_string` is provided (or the `APPLICATIONINSIGHTS_CONNECTION_STRING` env var is set).

### OTLP only (no Azure Monitor)

```python
from microsoft.opentelemetry import configure_microsoft_opentelemetry

configure_microsoft_opentelemetry(
    enable_otlp_export=True,
    otlp_endpoint="http://localhost:4318",
)
```

### Azure Monitor + OTLP + Agent365

```python
from microsoft.opentelemetry import configure_microsoft_opentelemetry

configure_microsoft_opentelemetry(
    azure_monitor_connection_string="InstrumentationKey=...;IngestionEndpoint=...",
    enable_otlp_export=True,
    enable_a365_export=True,
    a365_token_resolver=lambda agent_id, tenant_id: get_token(agent_id, tenant_id),
)
```

### With GenAI instrumentations (OpenAI + LangChain)

```python
from microsoft.opentelemetry import configure_microsoft_opentelemetry

configure_microsoft_opentelemetry(
    azure_monitor_connection_string="InstrumentationKey=...;IngestionEndpoint=...",
    enable_genai_openai_instrumentation=True,
    enable_genai_openai_agents_instrumentation=True,
    enable_genai_langchain_instrumentation=True,
)

# Now all OpenAI and LangChain calls emit OTel spans automatically
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
```

### With A365 framework instrumentations

```python
from microsoft.opentelemetry import configure_microsoft_opentelemetry

configure_microsoft_opentelemetry(
    enable_a365_export=True,
    a365_token_resolver=my_token_resolver,
    enable_a365_openai_instrumentation=True,
    enable_a365_langchain_instrumentation=True,
    enable_a365_semantickernel_instrumentation=True,
    enable_a365_agentframework_instrumentation=True,
)
```

### Environment-variable driven (zero-code config)

No code changes needed — set env vars and call with no arguments:

```bash
# Exporters
export APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=..."
export ENABLE_OTLP_EXPORTER=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318

# GenAI instrumentations
export ENABLE_GENAI_OPENAI_INSTRUMENTATION=true
export ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION=true
export ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION=true
```

```python
from microsoft.opentelemetry import configure_microsoft_opentelemetry
configure_microsoft_opentelemetry()
```

---

## Configuration Reference

### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| **Exporters** | | | |
| `azure_monitor_connection_string` | `str` | Application Insights connection string | `APPLICATIONINSIGHTS_CONNECTION_STRING` env var |
| `enable_azure_monitor_export` | `bool` | Enable Azure Monitor (auto-enabled when `azure_monitor_connection_string` is set) | `False` |
| `enable_otlp_export` | `bool` | Enable OTLP exporter | `False` |
| `otlp_endpoint` | `str` | OTLP collector endpoint | `OTEL_EXPORTER_OTLP_ENDPOINT` env var |
| `otlp_protocol` | `str` | `"http/protobuf"` or `"grpc"` | `"http/protobuf"` |
| `otlp_headers` | `str` | OTLP headers (e.g. for authentication) | `OTEL_EXPORTER_OTLP_HEADERS` env var |
| `enable_a365_export` | `bool` | Enable Agent365 exporter | `False` |
| `a365_token_resolver` | `callable` | `(agent_id, tenant_id) -> token` | `None` |
| `a365_cluster_category` | `str` | A365 cluster category | `"prod"` |
| `a365_exporter_options` | `Agent365ExporterOptions` | Advanced A365 exporter config | `None` |
| **GenAI Instrumentations** | | | |
| `enable_genai_openai_instrumentation` | `bool` | Instrument OpenAI SDK (chat, embeddings) | `False` |
| `enable_genai_openai_agents_instrumentation` | `bool` | Instrument OpenAI Agents SDK | `False` |
| `enable_genai_langchain_instrumentation` | `bool` | Instrument LangChain | `False` |
| **A365 Instrumentations** | | | |
| `enable_a365_openai_instrumentation` | `bool` | A365 OpenAI Agents extension | `False` |
| `enable_a365_langchain_instrumentation` | `bool` | A365 LangChain extension | `False` |
| `enable_a365_semantickernel_instrumentation` | `bool` | A365 Semantic Kernel extension | `False` |
| `enable_a365_agentframework_instrumentation` | `bool` | A365 Agent Framework extension | `False` |
| **Pipeline control** | | | |
| `disable_tracing` | `bool` | Disable trace collection | `False` |
| `disable_logging` | `bool` | Disable log collection | `False` |
| `disable_metrics` | `bool` | Disable metric collection | `False` |
| `resource` | `Resource` | OpenTelemetry Resource | Auto-detected |
| `span_processors` | `list` | Additional `SpanProcessor` instances | `[]` |
| `log_record_processors` | `list` | Additional `LogRecordProcessor` instances | `[]` |
| `metric_readers` | `list` | Additional `MetricReader` instances | `[]` |
| `views` | `list` | Metric `View` instances | `[]` |
| `sampling_ratio` | `float` | Fixed-percentage sampling (0.0–1.0) | not set |
| `traces_per_second` | `float` | Rate-limited sampling TPS | `5.0` |
| `logger_name` | `str` | Python logger name for log capture | `""` (root) |
| `logging_formatter` | `Formatter` | Python `logging.Formatter` for collected logs | `None` |
| `instrumentation_options` | `dict` | Fine-grained instrumentation control (e.g. `{"flask": {"enabled": False}}`) | All supported libs enabled |
| `enable_live_metrics` | `bool` | Azure Monitor live metrics | `True` |
| `enable_performance_counters` | `bool` | Azure Monitor performance counters | `True` |
| `enable_trace_based_sampling_for_logs` | `bool` | Correlate log sampling with trace sampling | `False` |
| `browser_sdk_loader_config` | `dict` | Azure Monitor browser SDK loader configuration | `{}` |

### Environment Variables

| Variable | Maps to | Values |
|----------|---------|--------|
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | `azure_monitor_connection_string` | Connection string |
| `ENABLE_OTLP_EXPORTER` | `enable_otlp_export` | `true` / `false` |
| `ENABLE_A365_EXPORTER` | `enable_a365_export` | `true` / `false` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `otlp_endpoint` | URL |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `otlp_protocol` | `http/protobuf` / `grpc` |
| `OTEL_EXPORTER_OTLP_HEADERS` | `otlp_headers` | key=value pairs |
| `A365_CLUSTER_CATEGORY` | `a365_cluster_category` | string |
| `ENABLE_GENAI_OPENAI_INSTRUMENTATION` | `enable_genai_openai_instrumentation` | `true` / `false` |
| `ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION` | `enable_genai_openai_agents_instrumentation` | `true` / `false` |
| `ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION` | `enable_genai_langchain_instrumentation` | `true` / `false` |
| `ENABLE_A365_OPENAI_INSTRUMENTATION` | `enable_a365_openai_instrumentation` | `true` / `false` |
| `ENABLE_A365_LANGCHAIN_INSTRUMENTATION` | `enable_a365_langchain_instrumentation` | `true` / `false` |
| `ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION` | `enable_a365_semantickernel_instrumentation` | `true` / `false` |
| `ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION` | `enable_a365_agentframework_instrumentation` | `true` / `false` |
| `OTEL_TRACES_EXPORTER` | `disable_tracing` | Set to `none` to disable |
| `OTEL_LOGS_EXPORTER` | `disable_logging` | Set to `none` to disable |
| `OTEL_METRICS_EXPORTER` | `disable_metrics` | Set to `none` to disable |
| `PYTHON_APPLICATIONINSIGHTS_LOGGER_NAME` | `logger_name` | Logger name string |
| `PYTHON_APPLICATIONINSIGHTS_LOGGING_FORMAT` | `logging_formatter` | Logging format string |

---

## Built-in Instrumentations

These standard web/HTTP instrumentations are included by default (same as `azure-monitor-opentelemetry`):

| Library | Package |
|---------|---------|
| Django | `opentelemetry-instrumentation-django` |
| FastAPI | `opentelemetry-instrumentation-fastapi` |
| Flask | `opentelemetry-instrumentation-flask` |
| Psycopg2 | `opentelemetry-instrumentation-psycopg2` |
| Requests | `opentelemetry-instrumentation-requests` |
| urllib | `opentelemetry-instrumentation-urllib` |
| urllib3 | `opentelemetry-instrumentation-urllib3` |
| Azure SDK | `azure-core` tracing integration |

---

## Architecture

```
configure_microsoft_opentelemetry(**kwargs)
│
├─ Step 1: Azure Monitor (if azure_monitor_connection_string provided)
│  └─ Delegates to configure_azure_monitor() from azure-monitor-opentelemetry
│     Sets up TracerProvider, LoggerProvider, MeterProvider, and instrumentations
│
├─ Step 2: Standalone providers (if Azure Monitor disabled)
│  └─ Creates TracerProvider, LoggerProvider, MeterProvider directly
│
├─ Step 3: OTLP exporters (if enable_otlp_export=True)
│  └─ Adds BatchSpanProcessor, BatchLogRecordProcessor, PeriodicExportingMetricReader
│
├─ Step 4: A365 exporter (if enable_a365_export=True)
│  └─ Adds EnrichingBatchSpanProcessor → Agent365Exporter
│
├─ Step 5: Standard instrumentations (only when Azure Monitor is disabled)
│  └─ Django, Flask, FastAPI, Requests, urllib, urllib3, psycopg2, Azure SDK
│
├─ Step 6: A365 observability instrumentations (if any enabled)
│  └─ OpenAI Agents, LangChain, Semantic Kernel, Agent Framework extensions
│
└─ Step 7: GenAI OTel contrib instrumentations (if any enabled)
   └─ OpenAIInstrumentor, OpenAIAgentsInstrumentor, LangchainInstrumentor
```

---

## Sample Project

Here's a minimal FastAPI app with full observability:

```bash
pip install microsoft-opentelemetry fastapi uvicorn openai
```

```python
# app.py
from fastapi import FastAPI
from openai import OpenAI
from microsoft.opentelemetry import configure_microsoft_opentelemetry

configure_microsoft_opentelemetry(
    azure_monitor_connection_string="InstrumentationKey=...;IngestionEndpoint=...",
    enable_genai_openai_instrumentation=True,
)

app = FastAPI()
client = OpenAI()

@app.get("/ask")
async def ask(q: str = "Hello"):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": q}],
    )
    return {"answer": response.choices[0].message.content}
```

```bash
uvicorn app:app --reload
```

All HTTP requests, OpenAI calls, and traces are sent to Application Insights automatically.

---

## License

MIT License — Copyright (c) Microsoft Corporation.
