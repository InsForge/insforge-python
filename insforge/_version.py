from importlib.metadata import version, PackageNotFoundError

try:
    VERSION = version("insforge")
except PackageNotFoundError:
    VERSION = "0.0.0-dev"

USER_AGENT = f"InsForge-Python/{VERSION}"
