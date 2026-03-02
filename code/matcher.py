import json
from pathlib import Path
from utils import normalize_mac

WHITELIST_PATH = Path(__file__).parent / "whitelist.json"

def load_whitelist():
    with open(WHITELIST_PATH) as f:
        return json.load(f)["devices"]

def match_device(device_addr: str | None, adv_name: str | None):
    whitelist = load_whitelist()

    addr = normalize_mac(device_addr)
    adv_name = (adv_name or "").strip()

    for entry in whitelist:
        wmac = normalize_mac(entry.get("mac"))
        if wmac and addr and wmac == addr:
            return entry

    for entry in whitelist:
        wname = (entry.get("name") or "").strip()
        if wname and adv_name and adv_name.startswith(wname):
            return entry

    return None