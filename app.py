"""Utility helpers for building Google Chat webhook card payloads."""

from __future__ import annotations

__author__ = "Daniil Stashkevich"
__mail__ = "daniil.stash.k@gmail.com"

import json
from typing import Any, Dict, List, Optional
from urllib import error, request


# --------------------------------------------------------------------------
# Demo - creating a message card and a rough text visualization
# --------------------------------------------------------------------------
# Example usage::
#
#     message = Message(title="Deployment", subtitle="Production release ✅")
#     summary_section = message.add_section("Summary")
#     message.add_text("Version 2.14.3 was deployed without errors.", summary_section)
#     message.add_key_value(
#         top_label="Status",
#         content="All systems nominal",
#         icon=Message.CHECK_CIRCLE_ICON,
#         section=summary_section,
#     )
#     message.add_button(text="View pipeline", url="https://example.com/pipeline")
#
# Visualization of the rendered card::
#
#     ----------------------------------------
#     | Deployment                            |
#     | Production release ✅                 |
#     ----------------------------------------
#     | Summary                               |
#     |  <> Status: All systems nominal       |
#     |  [button] View pipeline               |
#     ----------------------------------------
#

class WebhookError(Exception):
    """Custom exception raised when no webhook url is provided."""


class Message:
    """Helper object for assembling Google Chat card payloads."""

    PERSON_ICON = "PERSON"
    EMAIL_ICON = "EMAIL"
    PHONE_ICON = "PHONE"
    FLIGHT_ICON = "AIRPLANE"
    CALENDAR_ICON = "CALENDAR"
    CHECK_CIRCLE_ICON = "CHECK_CIRCLE"
    BOOKMARK_ICON = "BOOKMARK"
    STAR_ICON = "STAR"

    def __init__(self, title: str, subtitle: str, webhook_url: Optional[str] = None) -> None:
        """Initialize a new Google Chat card message."""

        self.webhook_url = webhook_url
        self.card: Dict[str, Any] = {
            "header": {
                "title": title,
                "subtitle": subtitle,
            },
            "sections": [],
        }

    # ------------------------------------------------------------------
    # Section helpers
    # ------------------------------------------------------------------
    def add_section(self, header: Optional[str] = None) -> int:
        """Add a new section to the card and return its index."""

        section: Dict[str, Any] = {"widgets": []}
        if header:
            section["header"] = header

        self.card["sections"].append(section)
        return len(self.card["sections"]) - 1

    def _resolve_section(self, section: Optional[int]) -> Dict[str, Any]:
        if not self.card["sections"]:
            raise ValueError("You need at least 1 section to add a widget")

        if section is None:
            return self.card["sections"][-1]

        if section < 0 or section >= len(self.card["sections"]):
            raise IndexError("Section index out of range")

        return self.card["sections"][section]

    # ------------------------------------------------------------------
    # Widget builders
    # ------------------------------------------------------------------
    def add_text(self, text: str, section: Optional[int] = None) -> None:
        """Add a text paragraph widget to the selected section."""

        widget = {"textParagraph": {"text": text}}
        self._resolve_section(section)["widgets"].append(widget)

    def add_image(self, url: str, alt_text: str, section: Optional[int] = None) -> None:
        """Add an image widget to the selected section."""

        widget = {"image": {"imageUrl": url, "altText": alt_text}}
        self._resolve_section(section)["widgets"].append(widget)

    def add_divider(self, section: Optional[int] = None) -> None:
        """Add a divider widget to visually separate content."""

        widget = {"divider": {}}
        self._resolve_section(section)["widgets"].append(widget)

    def add_key_value(
        self,
        top_label: Optional[str],
        content: str,
        icon: Optional[str] = None,
        bottom_label: Optional[str] = None,
        button_text: Optional[str] = None,
        button_url: Optional[str] = None,
        section: Optional[int] = None,
        multiline: bool = False,
    ) -> None:
        """Add a key value widget to the selected section."""

        key_value: Dict[str, Any] = {"content": content}
        if multiline:
            key_value["contentMultiline"] = True
        if top_label:
            key_value["topLabel"] = top_label
        if bottom_label:
            key_value["bottomLabel"] = bottom_label
        if icon:
            key_value["icon"] = icon

        if button_text and button_url:
            key_value["button"] = {
                "textButton": {
                    "text": button_text,
                    "onClick": {"openLink": {"url": button_url}},
                }
            }

        widget = {"keyValue": key_value}
        self._resolve_section(section)["widgets"].append(widget)

    def add_decorated_text(
        self,
        text: str,
        start_icon: Optional[str] = None,
        end_icon: Optional[str] = None,
        on_click_url: Optional[str] = None,
        section: Optional[int] = None,
    ) -> None:
        """Add a decorated text widget to the selected section."""

        decorated: Dict[str, Any] = {"text": text}
        if start_icon:
            decorated["startIcon"] = start_icon
        if end_icon:
            decorated["endIcon"] = end_icon
        if on_click_url:
            decorated["onClick"] = {"openLink": {"url": on_click_url}}

        widget = {"decoratedText": decorated}
        self._resolve_section(section)["widgets"].append(widget)

    def add_button(
        self,
        text: Optional[str] = None,
        url: Optional[str] = None,
        image_url: Optional[str] = None,
        name: Optional[str] = None,
        section: Optional[int] = None,
    ) -> None:
        """Add a button widget (text or image) to the selected section."""

        if not url:
            raise ValueError("Button requires a URL to open")

        if text:
            button: Dict[str, Any] = {
                "textButton": {
                    "text": text,
                    "onClick": {"openLink": {"url": url}},
                }
            }
        elif image_url:
            button = {
                "imageButton": {
                    "name": name or "Button",
                    "iconUrl": image_url,
                    "onClick": {"openLink": {"url": url}},
                }
            }
        else:
            raise ValueError("Button must define either text or image_url")

        widget = {"buttons": [button]}
        self._resolve_section(section)["widgets"].append(widget)

    # ------------------------------------------------------------------
    # Message delivery
    # ------------------------------------------------------------------
    def _prepare_msg(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build the final payload for Google Chat webhook."""

        return {"cards": [self.card]}

    def send(self, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """Send the card to Google Chat via webhook."""

        url = webhook_url or self.webhook_url
        if not url:
            raise WebhookError(
                "No webhook URL provided. Please pass it to the constructor or send()."
            )

        payload = json.dumps(self._prepare_msg()).encode("utf-8")
        req = request.Request(url, data=payload, headers={"Content-Type": "application/json"})

        try:
            with request.urlopen(req) as resp:
                status = resp.getcode()
                body = resp.read().decode("utf-8")
        except error.HTTPError as exc:  # pragma: no cover - thin wrapper, easy to mock
            status = exc.code
            body = exc.read().decode("utf-8")

        result = {"status": status, "body": body}
        print(status, body)
        return result


def demo_payload() -> Dict[str, Any]:
    """Return an illustrative payload demonstrating the helper API."""

    message = Message(title="Deployment", subtitle="Production release ✅")
    summary_section = message.add_section("Summary")
    message.add_text("Version 2.14.3 was deployed without errors.", section=summary_section)
    message.add_key_value(
        top_label="Status",
        content="All systems nominal",
        icon=Message.CHECK_CIRCLE_ICON,
        section=summary_section,
    )
    message.add_button(text="View pipeline", url="https://example.com/pipeline")

    return message._prepare_msg()


if __name__ == "__main__":
    print(json.dumps(demo_payload(), indent=2))
