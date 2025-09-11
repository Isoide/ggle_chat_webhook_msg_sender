__author__ = "Daniil Stashkevich"
__mail__ = "daniil.stash.k@gmail.com"

import requests

class WebhookError(Exception):
    """Custom exception raised when no webhook url is provided."""
    pass


class Message:
    def __init__(self, title: str, subtitle: str, webhook_url: str = None): 
        """
        Initialize a new Google Chat card message.

        :param title: Title for the card header.
        :param subtitle: Subtitle for the card header.
        :param webhook_url: Optional default webhook URL.
        """
        self.webhook_url = webhook_url
        self.card = {
            "header": {
                "title": title,
                "subtitle": subtitle
            },
            "sections": []
        }

    def add_section(self, header: str):
        """
        Add a new section to the card.

        :param header: Title of the section.
        """
        section = {"header": header, "widgets": []}
        self.card["sections"].append(section)

    def add_text(self, text: str, section: int = None):
        """
        Add a text paragraph widget to the last or chosen section.

        :param text: The text content.
        """
        
        if self.card["sections"]:
            widget = {"textParagraph": {"text": text}}
            if section:
                self.card["sections"][section]["widgets"].append(widget)
            else:
                self.card["sections"][-1]["widgets"].append(widget)
        else:
            raise ValueError("You need at least 1 section to add text")

    def add_image(self, url: str, alt_text: str, section:int = None):
        """
        Add an image widget to the last or chosen section.

        :param url: URL of the image.
        :param alt_text: Alternative text for accessibility.
        """
        if self.card["sections"]:
            widget = {"image": {"imageUrl": url, "altText": alt_text}}
            if section:
                self.card["sections"][section]["widgets"].append(widget)
            else:
                self.card["sections"][-1]["widgets"].append(widget)
        else:
            raise ValueError("You need at least 1 section to add an image")
        
    def add_button(self, text: str = None, url: str = None,
                   image_url: str = None, name: str = None, section: int = None):
        """
        Add a button widget (text or image) to the last or chosen section.

        :param text: Text for a text button (optional).
        :param url: URL the button should open.
        :param image_url: URL of an image icon for an image button (optional).
        :param name: Name of the image button (optional).
        """
        if not self.card["sections"]:
            raise ValueError("You need at least 1 section to add a button")

        if text:
            button = {
                "textButton": {
                    "text": text,
                    "onClick": {"openLink": {"url": url}}
                }
            }
        elif image_url:
            button = {
                "imageButton": {
                    "name": name or "Button",
                    "iconUrl": image_url,
                    "onClick": {"openLink": {"url": url}}
                }
            }
        else:
            raise ValueError("Button must have either text or image_url")

        widget = {"buttons": [button]}

        if section:
            self.card["sections"][section]["widgets"].append(widget)
        else:
            self.card["sections"][-1]["widgets"].append(widget)
    
    def _prepare_msg(self):
        """
        Build the final payload for Google Chat webhook.
        USED IN send()
        """
        return {"cards": [self.card]}
    

    def send(self, webhook_url: str = None):
        """
        Send the card to Google Chat via webhook.

        :param webhook_url: Optional override for the webhook URL.
        """
        url = webhook_url or self.webhook_url
        if not url:
            raise WebhookError("No webhook URL provided. Please pass it to the constructor or send().")

        response = requests.post(url, json=self._prepare_msg())
        print(response.status_code, response.text)


# Example usage
if __name__ == "__main__":
    print("a")