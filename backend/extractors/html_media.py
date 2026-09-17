import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import os
from typing import Dict, List, Optional, Any
from .base import BaseExtractor

class HTMLMediaExtractor(BaseExtractor):
    """
    HTML5 Media Extractor Plugin.
    Parses publicly accessible HTML pages to discover HTML5 <video>, <audio>, and <source> elements.
    """
    name = "HTMLMediaExtractor"
    priority = 40

    def can_handle(self, url: str) -> bool:
        # Applies to any web page URL
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
            discovered_urls = set()
            formats: List[Dict[str, Any]] = []

            # Page title fallback
            page_title = soup.title.string.strip() if soup.title and soup.title.string else "Discovered Page Media"

            # 1. Search <video> and child <source> elements
            for video in soup.find_all('video'):
                src = video.get('src')
                if src:
                    discovered_urls.add((urljoin(url, src), 'video', video.get('type', 'video/mp4')))
                for source in video.find_all('source'):
                    ssrc = source.get('src')
                    stype = source.get('type', 'video/mp4')
                    if ssrc:
                        discovered_urls.add((urljoin(url, ssrc), 'video', stype))

            # 2. Search <audio> and child <source> elements
            for audio in soup.find_all('audio'):
                src = audio.get('src')
                if src:
                    discovered_urls.add((urljoin(url, src), 'audio', audio.get('type', 'audio/mp3')))
                for source in audio.find_all('source'):
                    ssrc = source.get('src')
                    stype = source.get('type', 'audio/mp3')
                    if ssrc:
                        discovered_urls.add((urljoin(url, ssrc), 'audio', stype))

            # Build format objects
            for idx, (media_url, tag_kind, mime) in enumerate(discovered_urls):
                parsed_path = urlparse(media_url).path
                filename = os.path.basename(unquote(parsed_path)) or f"media_{idx}"
                ext = os.path.splitext(filename)[1].lstrip('.').lower() or ('mp4' if tag_kind == 'video' else 'mp3')
                
                is_video = tag_kind == 'video'
                quality = "HTML5 Video" if is_video else "HTML5 Audio"

                formats.append({
                    "format_id": f"html5_{tag_kind}_{idx}",
                    "url": media_url,
                    "ext": ext,
                    "resolution": "HTML5 Stream" if is_video else "Audio",
                    "quality": quality,
                    "format_note": f"HTML5 <{tag_kind}> Source Tag",
                    "filesize": None,
                    "vcodec": "h264" if is_video else "none",
                    "acodec": "aac" if is_video else "mp3",
                    "has_video": is_video,
                    "has_audio": True,
                    "download_type": "direct"
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
