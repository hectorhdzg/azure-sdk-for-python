# Release History

## 0.1.0b1 (Unreleased)

### Features Added

- Initial POC release of Microsoft OpenTelemetry Distro
- Unified `configure_microsoft_opentelemetry()` function supporting multiple exporters:
  - Azure Monitor (Application Insights) exporter
  - OTLP (OpenTelemetry Protocol) exporter (HTTP and gRPC)
  - Agent365 (Microsoft Agent 365) exporter
- All exporters can be enabled/disabled independently
- Installable via extras: `[azure-monitor]`, `[otlp]`, `[a365]`, `[all]`
- Same instrumentation support as azure-monitor-opentelemetry
