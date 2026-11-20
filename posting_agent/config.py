"""Load config.yaml and .env. Tokens are never stored in code or config."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def load_dotenv(path=None):
    """Tiny .env loader. No external dependency. Ignores missing file."""
    path = Path(path) if path else BASE_DIR / ".env"
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def _simple_yaml_load(text):
    """Fallback parser for this simple config only, used when PyYAML is missing."""
    out = {}
    current = None
    current_sub = None
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if line.startswith("- "):
            item = line[2:].strip().strip('"')
            if isinstance(out.get(current), list):
                out[current].append(_coerce(item))
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().strip('"')
        val = val.strip().strip('"')
        if indent == 0:
            current = key
            current_sub = None
            if val:
                out[key] = _coerce(val)
            elif key == "slots":
                out[key] = []
            else:
                out[key] = {}
        elif indent == 2:
            if isinstance(out.get(current), dict):
                if val == "":
                    out[current][key] = {}
                    current_sub = key
                else:
                    out[current][key] = _coerce(val)
        elif indent == 4 and current_sub:
            out[current][current_sub][key] = _coerce(val)
    return out


def _coerce(val):
    if val in ("true", "True"):
        return True
    if val in ("false", "False"):
        return False
    try:
        return int(val)
    except ValueError:
        return val


def load_config(path=None):
    path = Path(path) if path else BASE_DIR / "config.yaml"
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        cfg = yaml.safe_load(text) or {}
    except ImportError:
        cfg = _simple_yaml_load(text)
    # Slots may parse as a dict in the fallback; normalise to a list.
    slots = cfg.get("slots") or ["14:00", "20:00"]
    if isinstance(slots, dict):
        slots = list(slots.values())
    cfg["slots"] = [str(s) for s in slots]
    env = load_dotenv()
    cfg["dry_run"] = str(env.get("DRY_RUN", str(cfg.get("dry_run", True)))).lower() in (
        "true",
        "1",
        "yes",
    )
    cfg["env"] = env
    cfg["base_dir"] = BASE_DIR
    return cfg
