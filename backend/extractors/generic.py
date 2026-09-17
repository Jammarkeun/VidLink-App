import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
from typing import Dict, List, Optional, Any
from .base import BaseExtractor

MEDIA_REGEX = re.compile(
    r'(https?://[^\s"\'<>]+\.(?:mp4|webm|m3u8|mpd|mov|m4v|mkv|mp3|m4a|wav)(?:\?[^\s"\'<>]*)?)',
    re.IGNORECASE
)

class GenericExtractor(BaseExtractor):
    """
    Generic Network & Embedded Script Media Extractor.
    Scans scripts, JS config blocks, and iframes for media streams when specific markup is absent.
    """
    name = "GenericExtractor"
    priority = 90  # Fallback extractor

    def can_handle(self, url: str) -> bool:
        return url.startswith("http://") or url.startswith("https://")

    def analyze(self, url: str) -> Optional[Dict[str, Any]]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200 or not res.text:
                return None

            soup = BeautifulSoup(res.text, 'html.parser')
            page_title = soup.title.string.strip() if soup.title and soup.title.string else "Discovered Media Stream"
            
            matches = set(MEDIA_REGEX.findall(res.text))
            formats: List[Dict[str, Any]] = []

            for idx, media_url in enumerate(matches):
                # Ignore common icon/static image false positives
                if any(media_url.lower().endswith(img_ext) for img_ext in ['.png', '.jpg', '.jpeg', '.svg', '.gif']):
                    continue

                parsed = urlparse(media_url)
                ext = os.path.splitext(parsed.path)[1].lstrip('.').lower() or 'mp4'
                
                is_hls = ext == 'm3u8'
                is_dash = ext == 'mpd'
                is_audio = ext in ['mp3', 'm4a', 'wav', 'aac', 'flac', 'ogg']

                resolution = "HLS Stream" if is_hls else ("DASH Stream" if is_dash else ("Audio" if is_audio else "Discovered Stream"))
                quality = "Stream Manifest" if (is_hls or is_dash) else ("Audio" if is_audio else "Discovered")

                formats.append({
                    "format_id": f"generic_discovered_{idx}_{ext}",
                    "url": media_url,
                    "ext": ext,
                    "resolution": resolution,
                    "quality": quality,
                    "format_note": f"Discovered Embedded Resource ({ext.upper()})",
                    "filesize": None,
                    "vcodec": "unknown" if not is_audio else "none",
                    "acodec": "unknown",
                    "has_video": not is_audio,
                    "has_audio": True,
                    "download_type": "hls" if is_hls else ("dash" if is_dash else "direct")
                })

            if not formats:
                return None

            return {
                "title": page_title,
                "duration": None,
                "thumbnail": None,
                "source_url": url,
                "extractor_name": self.name,
                "formats": formats
            }

        except Exception:
            return None
