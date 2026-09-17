import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
from typing import Dict, List, Optional, Any
from .base import BaseExtractor

class MetadataExtractor(BaseExtractor):
    """
    OpenGraph, Twitter Card, and JSON-LD Metadata Extractor Plugin.
    Extracts embedded media metadata and direct media stream pointers from meta tags & Schema.org.
    """
    name = "MetadataExtractor"
    priority = 50

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
            
            title = None
            thumbnail = None
            duration = None
            formats: List[Dict[str, Any]] = []
            discovered_urls = set()

            # 1. OpenGraph & Meta Tags
            for meta in soup.find_all('meta'):
                prop = meta.get('property', '').lower() or meta.get('name', '').lower()
                content = meta.get('content', '')

                if not content:
                    continue

                if prop in ['og:title', 'twitter:title']:
                    title = title or content
                elif prop in ['og:image', 'twitter:image']:
                    thumbnail = thumbnail or urljoin(url, content)
                elif prop in ['og:video', 'og:video:secure_url', 'og:video:url', 'twitter:player:stream']:
                    discovered_urls.add((urljoin(url, content), 'OpenGraph Video', 'video'))
                elif prop in ['og:audio', 'og:audio:secure_url']:
                    discovered_urls.add((urljoin(url, content), 'OpenGraph Audio', 'audio'))

            # 2. JSON-LD / Schema.org VideoObject
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string or '{}')
                    objects = data if isinstance(data, list) else [data]

                    for item in objects:
                        if isinstance(item, dict):
                            item_type = str(item.get('@type', '')).lower()
                            if 'videoobject' in item_type or 'mediaobject' in item_type or 'audioobject' in item_type:
                                title = title or item.get('name') or item.get('headline')
                                thumbnail = thumbnail or item.get('thumbnailUrl')
                                content_url = item.get('contentUrl') or item.get('embedUrl')
                                
                                if content_url:
                                    kind = 'audio' if 'audioobject' in item_type else 'video'
                                    discovered_urls.add((urljoin(url, content_url), 'Schema.org JSON-LD', kind))
                except Exception:
                    continue

            # Build format objects
            for idx, (media_url, tag_source, kind) in enumerate(discovered_urls):
                ext = os.path.splitext(urlparse(media_url).path)[1].lstrip('.').lower() or ('mp4' if kind == 'video' else 'mp3')
                is_video = kind == 'video'

                formats.append({
                    "format_id": f"metadata_{kind}_{idx}",
                    "url": media_url,
                    "ext": ext,
                    "resolution": "Metadata Stream" if is_video else "Audio",
                    "quality": "High",
                    "format_note": f"{tag_source} Meta Tag",
                    "filesize": None,
                    "vcodec": "unknown" if is_video else "none",
                    "acodec": "unknown",
                    "has_video": is_video,
                    "has_audio": True,
                    "download_type": "direct"
                })

            if not formats:
                return None

            return {
                "title": title or "Metadata Media Resource",
                "duration": duration,
                "thumbnail": thumbnail,
                "source_url": url,
                "extractor_name": self.name,
                "formats": formats
            }

        except Exception:
            return None
