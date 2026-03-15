from open_waterfall.messaging.parser import parse_email_steps


def test_parse_email_steps() -> None:
    parsed = parse_email_steps(
        [
            "\n".join(
                [
                    "STEP: 2",
                    "SEND: Day 5",
                    "SUBJECT: follow up",
                    "THREAD: reply-to-1",
                    "---",
                    "Body text",
                    "---",
                ]
            )
        ]
    )

    assert parsed[0]["step"] == 2
    assert parsed[0]["subject"] == "follow up"
    assert parsed[0]["body"] == "Body text"

