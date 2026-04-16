import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "filebot.db"
FILES_DIR = BASE_DIR / "files"

def _load_dotenv_file(dotenv_path: Path) -> None:
	if not dotenv_path.exists():
		return

	for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue

		key, value = line.split("=", 1)
		key = key.strip()
		value = value.strip().strip("\"'")

		if key and key not in os.environ:
			os.environ[key] = value


def _get_required_env(name: str) -> str:
	value = os.getenv(name)
	if value is None or value.strip() == "":
		raise RuntimeError(f"Missing required environment variable: {name}")
	return value.strip()


def _get_required_int_env(name: str) -> int:
	raw_value = _get_required_env(name)
	try:
		return int(raw_value)
	except ValueError as exc:
		raise RuntimeError(f"Environment variable {name} must be an integer") from exc


_load_dotenv_file(BASE_DIR / ".env")

BOT_TOKEN = _get_required_env("BOT_TOKEN")
ADMIN_ID = _get_required_int_env("ADMIN_ID")
LOG_CHANNEL = _get_required_int_env("LOG_CHANNEL")
STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID", str(LOG_CHANNEL)))

FILE_EXPIRY_MINUTES = int(os.getenv("FILE_EXPIRY_MINUTES", "5"))
CLEANUP_INTERVAL_MINUTES = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "1"))
BROADCAST_CLEANUP_INTERVAL_MINUTES = int(os.getenv("BROADCAST_CLEANUP_INTERVAL_MINUTES", "30"))
