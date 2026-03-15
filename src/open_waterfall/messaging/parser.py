from __future__ import annotations

import re
from typing import Optional


def parse_email_steps(email_variants: list[str]) -> list[dict]:
    steps = []
    for variant in email_variants:
        parsed = _parse_single_email(variant)
        if parsed:
            steps.append(parsed)
    steps.sort(key=lambda item: item.get("step", 0))
    return steps


def _parse_single_email(text: str) -> Optional[dict]:
    if not text or not text.strip():
        return None

    step_match = re.search(r"STEP:\s*(\d+)", text)
    if not step_match:
        return None

    subject_match = re.search(r"SUBJECT:\s*(.+?)(?:\n|$)", text)
    send_match = re.search(r"SEND:\s*Day\s*(\d+)", text)
    thread_match = re.search(r"THREAD:\s*(.+?)(?:\n|$)", text)
    body_match = re.search(r"---\n(.*?)\n---", text, re.DOTALL)

    return {
        "step": int(step_match.group(1)),
        "send_day": int(send_match.group(1)) if send_match else 0,
        "subject": subject_match.group(1).strip() if subject_match else "",
        "thread": thread_match.group(1).strip() if thread_match else "new",
        "body": body_match.group(1).strip() if body_match else "",
    }

