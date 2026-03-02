import re

def normalize_mac(mac: str | None) -> str | None:
    if not mac:
        return None

    mac = mac.strip().upper()
    mac = re.sub(r"[^0-9A-F]", "", mac)

    if len(mac) != 12:
        return None

    return ":".join(mac[i:i+2] for i in range(0, 12, 2))