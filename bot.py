import os
from pathlib import Path


def _read_env_value(name: str) -> str | None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"\'')

    return None


def run_secondary_bot() -> None:
    """Run the current bot stack with BOT_TOKEN1 as runtime BOT_TOKEN."""
    secondary_token = os.getenv("BOT_TOKEN1") or _read_env_value("BOT_TOKEN1")
    if not secondary_token:
        raise RuntimeError("BOT_TOKEN1 is missing in .env")

    # Force runtime token before importing main/config.
    os.environ["BOT_TOKEN"] = secondary_token
    os.environ["BOT_ROLE"] = "secondary"

    from main import run

    run()


if __name__ == "__main__":
    run_secondary_bot()
