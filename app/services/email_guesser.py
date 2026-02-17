from __future__ import annotations


def guess_emails(full_name: str | None, domain: str | None) -> list[str]:
    if not full_name or not domain:
        return []
    parts = [p for p in full_name.strip().split() if p]
    if len(parts) < 2:
        return []
    first = parts[0].lower()
    last = parts[-1].lower()
    patterns = [
        f"{first}.{last}",
        f"{first}{last}",
        f"{first}",
        f"{first[0]}{last}",
        f"{first}{last[0]}",
        f"{first[0]}.{last}",
    ]
    return [f"{pattern}@{domain}" for pattern in patterns]
