import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "filebot.db"
FILES_DIR = BASE_DIR / "files"
CHANNELS_FILE = BASE_DIR / "channels.txt"


def _load_dotenv_file(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"\'')
        if key and key not in os.environ:
            os.environ[key] = value


def _load_key_value_file(file_path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not file_path.exists():
        return data

    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().rstrip(",").strip('"\'')
        if key:
            data[key] = value
    return data


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
BOT_TOKEN1 = os.getenv("BOT_TOKEN1")  # Optional: Secondary bot for share links
BOT_ROLE = os.getenv("BOT_ROLE", "primary").strip().lower()
ADMIN_ID = _get_required_int_env("ADMIN_ID")
LOG_CHANNEL = _get_required_int_env("LOG_CHANNEL")
STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID", str(LOG_CHANNEL)))
NEVER_EXPIRE_LINKS = os.getenv("NEVER_EXPIRE_LINKS", "1").strip().lower() in {"1", "true", "yes", "on"}
USE_SUPABASE = os.getenv("USE_SUPABASE", "0").strip().lower() in {"1", "true", "yes", "on"}
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip() or None
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip() or None

if USE_SUPABASE and (not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY):
    raise RuntimeError("USE_SUPABASE=1 requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")

FILE_EXPIRY_MINUTES = int(os.getenv("FILE_EXPIRY_MINUTES", "5"))
CLEANUP_INTERVAL_MINUTES = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "1"))
BROADCAST_CLEANUP_INTERVAL_MINUTES = int(os.getenv("BROADCAST_CLEANUP_INTERVAL_MINUTES", "30"))

def _normalize_join_link(raw_value: str) -> str:
    value = raw_value.strip()
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if value.startswith("@"):  # public channel username
        return f"https://t.me/{value[1:]}"
    if value.startswith("+"):  # private invite hash
        return f"https://t.me/{value}"
    return value


def _normalize_verify_target(raw_value: str) -> str | int | None:
    value = raw_value.strip()
    if not value:
        return None
    if value.startswith("@"):  # public channel username
        return value
    if value.startswith("http://") or value.startswith("https://"):
        if "t.me/" in value:
            channel_part = value.split("t.me/", 1)[1].rstrip("/")
            if channel_part.startswith("+"):
                return None
            return f"@{channel_part.lstrip('@')}"
        return None
    try:
        return int(value)
    except ValueError:
        return f"@{value.lstrip('@')}"


def _parse_required_channel_entry(raw_entry: str) -> tuple[str, str | int | None]:
    entry = raw_entry.strip()
    if "|" in entry:
        join_part, verify_part = entry.split("|", 1)
    else:
        join_part, verify_part = entry, entry
    return _normalize_join_link(join_part), _normalize_verify_target(verify_part)


def _parse_numbered_channels(channel_data: dict[str, str]) -> list[tuple[str, str | int | None]]:
    entries: list[tuple[str, str | int | None]] = []
    index = 1
    while True:
        id_key = f"JOIN_CHANNEL_IDS{index}"
        link_key = f"JOIN_CHANNEL_LINKS{index}"
        raw_id = channel_data.get(id_key, os.getenv(id_key, "")).strip()
        raw_link = channel_data.get(link_key, os.getenv(link_key, "")).strip()
        if not raw_id and not raw_link:
            break
        if raw_link:
            join_url = _normalize_join_link(raw_link)
            verify_target = _normalize_verify_target(raw_id) if raw_id else _normalize_verify_target(raw_link)
            entries.append((join_url, verify_target))
        index += 1
    return entries


CHANNELS_FILE_DATA = _load_key_value_file(CHANNELS_FILE)
REQUIRED_CHANNEL_ENTRIES = _parse_numbered_channels(CHANNELS_FILE_DATA)

if not REQUIRED_CHANNEL_ENTRIES:
    JOIN_CHANNEL_LINK_RAW = os.getenv("JOIN_CHANNEL_LINK", "").strip()
    REQUIRED_CHANNEL_ENTRIES = [
        _parse_required_channel_entry(link)
        for link in JOIN_CHANNEL_LINK_RAW.split(",")
        if link.strip()
    ] if JOIN_CHANNEL_LINK_RAW else []

# Backwards-compatible list of join URLs.
REQUIRED_CHANNELS = [join_url for join_url, _ in REQUIRED_CHANNEL_ENTRIES]
REQUIRED_CHANNEL_VERIFY_TARGETS = [verify_target for _, verify_target in REQUIRED_CHANNEL_ENTRIES]
