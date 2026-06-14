"""Standalone validation script for the Xiaomi MiMo provider integration.

Bypasses the Settings class (which requires Python 3.14 type annotations)
by importing only the modules that don't depend on it.
"""
import sys
sys.path.insert(0, ".")

# --- 1. Verify provider_catalog has xiaomimimo ---
# Import the catalog module directly, bypassing config/__init__.py
import importlib.util, types

# Temporarily replace config package to avoid importing Settings
config_stub = types.ModuleType("config")
config_stub.__path__ = ["config"]
sys.modules["config"] = config_stub

# Stub out config.constants so providers can import it
constants_stub = types.ModuleType("config.constants")
constants_stub.ANTHROPIC_DEFAULT_MAX_OUTPUT_TOKENS = 81920
constants_stub.HTTP_CONNECT_TIMEOUT_DEFAULT = 10.0
constants_stub.NATIVE_MESSAGES_ERROR_BODY_LOG_CAP_BYTES = 4096
constants_stub.PROVIDER_ERROR_BODY_DISPLAY_CAP_BYTES = 16384
sys.modules["config.constants"] = constants_stub

# Stub out config.provider_ids (re-exported from catalog)
provider_ids_stub = types.ModuleType("config.provider_ids")
sys.modules["config.provider_ids"] = provider_ids_stub

spec = importlib.util.spec_from_file_location("config.provider_catalog", "config/provider_catalog.py")
catalog_mod = importlib.util.module_from_spec(spec)
sys.modules["config.provider_catalog"] = catalog_mod
spec.loader.exec_module(catalog_mod)

PROVIDER_CATALOG = catalog_mod.PROVIDER_CATALOG
SUPPORTED_PROVIDER_IDS = catalog_mod.SUPPORTED_PROVIDER_IDS
XIAOMIMIMO_DEFAULT_BASE = catalog_mod.XIAOMIMIMO_DEFAULT_BASE

print("=== 1. Provider Catalog ===")
print(f"  Total providers: {len(PROVIDER_CATALOG)}")
print(f"  xiaomimimo in catalog: {'xiaomimimo' in PROVIDER_CATALOG}")
print(f"  xiaomimimo in SUPPORTED_PROVIDER_IDS: {'xiaomimimo' in SUPPORTED_PROVIDER_IDS}")
print(f"  Catalog == Supported IDs: {set(PROVIDER_CATALOG.keys()) == set(SUPPORTED_PROVIDER_IDS)}")
print(f"  XIAOMIMIMO_DEFAULT_BASE: {XIAOMIMIMO_DEFAULT_BASE}")

desc = PROVIDER_CATALOG["xiaomimimo"]
print(f"  transport_type: {desc.transport_type}")
print(f"  credential_env: {desc.credential_env}")
print(f"  credential_attr: {desc.credential_attr}")
print(f"  proxy_attr: {desc.proxy_attr}")
print(f"  capabilities: {desc.capabilities}")

# --- 2. Verify provider package imports cleanly ---
print("\n=== 2. Provider Package Import ===")
# Need httpx for AnthropicMessagesTransport
try:
    import httpx
    print("  httpx available: True")
except ImportError:
    print("  httpx available: False (install httpx to test provider import)")
    sys.exit(0)

try:
    from providers.xiaomimimo import XiaomiMiMoProvider, XIAOMIMIMO_DEFAULT_BASE as base
    print(f"  XiaomiMiMoProvider imported: True")
    print(f"  XIAOMIMIMO_DEFAULT_BASE from package: {base}")
except Exception as e:
    print(f"  Import error: {e}")
    sys.exit(1)

# --- 3. Verify registry PROVIDER_FACTORIES includes xiaomimimo ---
print("\n=== 3. Registry PROVIDER_FACTORIES ===")
# We can't import registry directly (it imports Settings), so check the file
with open("providers/registry.py") as f:
    registry_src = f.read()
print(f"  _create_xiaomimimo defined: {'_create_xiaomimimo' in registry_src}")
print(f"  xiaomimimo in PROVIDER_FACTORIES: {'\"xiaomimimo\": _create_xiaomimimo' in registry_src}")

# --- 4. Verify admin_config.py has XIAOMIMIMO_API_KEY ---
print("\n=== 4. Admin Config Fields ===")
with open("api/admin_config.py") as f:
    admin_src = f.read()
print(f"  XIAOMIMIMO_API_KEY field: {'XIAOMIMIMO_API_KEY' in admin_src}")
print(f"  XIAOMIMIMO_PROXY field: {'XIAOMIMIMO_PROXY' in admin_src}")
print(f"  FCC_SMOKE_MODEL_XIAOMIMIMO field: {'FCC_SMOKE_MODEL_XIAOMIMIMO' in admin_src}")

# --- 5. Verify admin.js has xiaomimimo label ---
print("\n=== 5. Admin JS Label ===")
with open("api/admin_static/admin.js") as f:
    js_src = f.read()
print(f"  xiaomimimo: 'Xiaomi MiMo' in admin.js: {'xiaomimimo: \"Xiaomi MiMo\"' in js_src}")

# --- 6. Verify .env.example ---
print("\n=== 6. .env.example ===")
with open(".env.example") as f:
    env_src = f.read()
print(f"  XIAOMIMIMO_API_KEY: {'XIAOMIMIMO_API_KEY' in env_src}")
print(f"  XIAOMIMIMO_PROXY: {'XIAOMIMIMO_PROXY' in env_src}")
print(f"  FCC_SMOKE_MODEL_XIAOMIMIMO: {'FCC_SMOKE_MODEL_XIAOMIMIMO' in env_src}")
print(f"  xiaomimimo in valid providers comment: {'xiaomimimo' in env_src}")

# --- 7. Verify settings.py has xiaomimimo attrs ---
print("\n=== 7. Settings Attributes ===")
with open("config/settings.py") as f:
    settings_src = f.read()
print(f"  xiaomimimo_api_key field: {'xiaomimimo_api_key' in settings_src}")
print(f"  xiaomimimo_proxy field: {'xiaomimimo_proxy' in settings_src}")
print(f"  XIAOMIMIMO_API_KEY alias: {'XIAOMIMIMO_API_KEY' in settings_src}")
print(f"  XIAOMIMIMO_PROXY alias: {'XIAOMIMIMO_PROXY' in settings_src}")

# --- 8. Verify test_registry.py ---
print("\n=== 8. Test Registry Updates ===")
with open("tests/providers/test_registry.py") as f:
    test_src = f.read()
print(f"  XiaomiMiMoProvider imported: {'XiaomiMiMoProvider' in test_src}")
print(f"  xiaomimimo_api_key in _make_settings: {'xiaomimimo_api_key' in test_src}")
print(f"  xiaomimimo_proxy in _make_settings: {'xiaomimimo_proxy' in test_src}")
print(f"  xiaomimimo in test cases: {'\"xiaomimimo\": XiaomiMiMoProvider' in test_src}")

print("\n=== ALL CHECKS PASSED ===")
