from plugins.base_plugin.base_plugin import BasePlugin
from datetime import datetime
import requests
import textwrap


VALID_SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]

ZODIAC_SYMBOLS = {
    "aries": "♈",
    "taurus": "♉",
    "gemini": "♊",
    "cancer": "♋",
    "leo": "♌",
    "virgo": "♍",
    "libra": "♎",
    "scorpio": "♏",
    "sagittarius": "♐",
    "capricorn": "♑",
    "aquarius": "♒",
    "pisces": "♓",
}


def split_horoscope_lines(text, width=34, max_lines=8):
    if not text:
        return ["No horoscope available today."]

    wrapped = textwrap.wrap(text, width=width)
    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        wrapped[-1] = wrapped[-1].rstrip(" .,;:-") + "…"
    return wrapped


class Horoscope(BasePlugin):
    def generate_image(self, settings, device_config):
        zodiac = (settings.get("zodiac") or "aries").lower().strip()

        if zodiac not in VALID_SIGNS:
            raise RuntimeError(
                f"Invalid zodiac sign '{zodiac}'. Must be one of: {', '.join(VALID_SIGNS)}"
            )

        api_key = device_config.load_env_key("API_NINJAS_KEY")
        if not api_key:
            raise RuntimeError("API Ninjas API key not configured.")

        url = f"https://api.api-ninjas.com/v1/horoscope?zodiac={zodiac}"
        headers = {"X-Api-Key": api_key}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            content = e.response.text if e.response is not None else "No response content"
            status_code = e.response.status_code if e.response is not None else "unknown"
            raise RuntimeError(f"HTTP error {status_code}: {content}") from e
        except requests.exceptions.Timeout as e:
            raise RuntimeError("Request timed out trying to fetch horoscope data.") from e
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network or connection error: {str(e)}") from e

        try:
            data = response.json()
        except ValueError as e:
            raise RuntimeError("Failed to parse response as JSON.") from e

        horoscope_text = (
            data.get("horoscope", "").strip()
            or "No horoscope available for this zodiac sign today."
        )

        raw_date = data.get("date", "")
        formatted_date = raw_date
        if raw_date:
            try:
                dt = datetime.strptime(raw_date, "%Y-%m-%d")
                formatted_date = dt.strftime("%b %d, %Y")
            except Exception:
                formatted_date = raw_date

        horoscope_lines = split_horoscope_lines(horoscope_text)

        width, height = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            width, height = height, width

        sign_name = zodiac.capitalize()
        sign_symbol = ZODIAC_SYMBOLS.get(zodiac, "")

        return self.render_image(
            dimensions=(width, height),
            html_file="horoscope.html",
            css_file="horoscope.css",
            template_params={
                "zodiac": sign_name,
                "zodiac_symbol": sign_symbol,
                "date": formatted_date,
                "horoscope": horoscope_text,
                "horoscope_lines": horoscope_lines,
                "plugin_settings": settings,
            }
        )

    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params["style_settings"] = True
        return template_params