import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any
from .base import BaseExtractor

class DASHExtractor(BaseExtractor):
    """
    MPEG-DASH (.mpd) Stream Manifest Analyzer.
    Parses DASH MPD XML structure and extracts Representation sets.
    """
    name = "DASHExtractor"
    priority = 35

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.path.lower().endswith('.mpd') or '.mpd?' in url.lower()

    def analyze(self, url: str) -> Optional[Dict[str, Any]]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200 or not res.text:
                return None

            root = ET.fromstring(res.text)
            namespace = root.tag.split('}')[0].strip('{') if '}' in root.tag else ''
            base_url = next(
                (element.text.strip() for element in root.iter() if element.tag.rsplit('}', 1)[-1] == 'BaseURL' and element.text),
                ''
            )
            manifest_base = urljoin(url, base_url) if base_url else url
            
            formats: List[Dict[str, Any]] = []
            rep_idx = 0

            # Search representations in XML tree
            for rep in root.iter(f'{{{namespace}}}Representation') if namespace else root.iter('Representation'):
                rep_idx += 1
                width = rep.attrib.get('width')
                height = rep.attrib.get('height')
                bandwidth = rep.attrib.get('bandwidth')
                mime_type = rep.attrib.get('mimeType', '')
                codecs = rep.attrib.get('codecs', 'dash')
                representation_url = next(
                    (element.text.strip() for element in rep if element.tag.rsplit('}', 1)[-1] == 'BaseURL' and element.text),
                    ''
                )
                media_url = urljoin(manifest_base, representation_url) if representation_url else url

                res_str = f"{width}x{height}" if width and height else "DASH Stream"
                quality = f"{height}p" if height else "Adaptive"
                bitrate_kbps = round(int(bandwidth) / 1000) if bandwidth else None

                is_video = 'video' in mime_type or height is not None
                is_audio = 'audio' in mime_type

                formats.append({
                    "format_id": f"dash_rep_{rep_idx}_{height or 'stream'}",
                    "url": media_url,
                    "ext": "mpd",
                    "resolution": res_str,
                    "quality": quality,
                    "height": int(height) if height else None,
                    "bitrate": bitrate_kbps,
                    "format_note": f"DASH Representation ({bitrate_kbps} kbps)" if bitrate_kbps else "DASH Representation",
                    "filesize": None,
                    "vcodec": codecs if is_video else "none",
                    "acodec": codecs if is_audio else "none",
                    "has_video": is_video,
                    "has_audio": is_audio,
                    "download_type": "dash"
                })

            if not formats:
                # Master DASH format fallback
                formats.append({
                    "format_id": "dash_master",
                    "url": url,
                    "ext": "mpd",
                    "resolution": "DASH Manifest",
                    "quality": "Adaptive",
                    "format_note": "MPEG-DASH Stream Manifest",
                    "filesize": None,
                    "vcodec": "dash",
                    "acodec": "dash",
                    "has_video": True,
                    "has_audio": True,
                    "download_type": "dash"
                })

            return {
                "title": "MPEG-DASH Stream Resource",
                "duration": None,
                "thumbnail": None,
                "source_url": url,
                "extractor_name": self.name,
                "formats": formats
            }

        except Exception:
            return None
