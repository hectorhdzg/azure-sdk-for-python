"""Smoke test: verify all microsoft-opentelemetry modules import without errors."""

import sys

errors = []

def check(label, fn):
    try:
        fn()
        print(f"  OK  {label}")
    except Exception as e:
        print(f"  FAIL {label}: {e}")
        errors.append(label)

print("=== microsoft-opentelemetry smoke test ===\n")

# Core modules
check("_version", lambda: __import__("microsoft.opentelemetry._version", fromlist=["VERSION"]))
check("_types", lambda: __import__("microsoft.opentelemetry._types", fromlist=["ConfigurationValue"]))
check("_constants", lambda: __import__("microsoft.opentelemetry._constants", fromlist=["CONNECTION_STRING_ARG"]))
check("configurations", lambda: __import__("microsoft.opentelemetry._utils.configurations", fromlist=["_get_configurations"]))
check("instrumentation", lambda: __import__("microsoft.opentelemetry._utils.instrumentation", fromlist=["get_dist_dependency_conflicts"]))
check("_configure", lambda: __import__("microsoft.opentelemetry._configure", fromlist=["configure_microsoft_opentelemetry"]))
check("__init__", lambda: __import__("microsoft.opentelemetry", fromlist=["configure_microsoft_opentelemetry"]))

# Verify key exports
print("\n--- Checking exports ---")
check("configure_microsoft_opentelemetry is callable", lambda: (
    callable(getattr(__import__("microsoft.opentelemetry", fromlist=["configure_microsoft_opentelemetry"]), "configure_microsoft_opentelemetry"))
    or (_ for _ in ()).throw(AssertionError("not callable"))
))
check("__version__ exists", lambda: (
    isinstance(getattr(__import__("microsoft.opentelemetry", fromlist=["__version__"]), "__version__"), str)
    or (_ for _ in ()).throw(AssertionError("not a string"))
))

# Verify constants are defined
print("\n--- Checking constants ---")
consts = __import__("microsoft.opentelemetry._constants", fromlist=["*"])
for name in [
    "CONNECTION_STRING_ARG", "ENABLE_OTLP_EXPORTER_ARG", "ENABLE_AZURE_MONITOR_EXPORTER_ARG",
    "ENABLE_A365_EXPORTER_ARG", "ENABLE_A365_OPENAI_INSTRUMENTATION_ARG",
    "ENABLE_A365_LANGCHAIN_INSTRUMENTATION_ARG", "ENABLE_A365_SEMANTICKERNEL_INSTRUMENTATION_ARG",
    "ENABLE_A365_AGENTFRAMEWORK_INSTRUMENTATION_ARG", "ENABLE_GENAI_OPENAI_INSTRUMENTATION_ARG",
    "ENABLE_GENAI_OPENAI_AGENTS_INSTRUMENTATION_ARG", "ENABLE_GENAI_LANGCHAIN_INSTRUMENTATION_ARG",
]:
    check(f"constant {name}", lambda n=name: getattr(consts, n))

# Verify _get_configurations runs with no args (no exporter enabled warning is OK)
print("\n--- Checking _get_configurations defaults ---")
import logging
logging.disable(logging.CRITICAL)  # suppress expected warnings
try:
    from microsoft.opentelemetry._utils.configurations import _get_configurations
    cfg = _get_configurations()
    check("_get_configurations() returns dict", lambda: isinstance(cfg, dict) or (_ for _ in ()).throw(AssertionError))
    check("has disable_tracing key", lambda: "disable_tracing" in cfg or (_ for _ in ()).throw(AssertionError))
    check("has enable_otlp_export key", lambda: "enable_otlp_export" in cfg or (_ for _ in ()).throw(AssertionError))
    check("has enable_a365_export key", lambda: "enable_a365_export" in cfg or (_ for _ in ()).throw(AssertionError))
    check("has genai keys", lambda: "enable_genai_openai_instrumentation" in cfg or (_ for _ in ()).throw(AssertionError))
finally:
    logging.disable(logging.NOTSET)

print(f"\n{'='*45}")
if errors:
    print(f"FAILED: {len(errors)} check(s) failed: {errors}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
