import os
import requests
from urllib.parse import urlparse, unquote
from typing import Dict, Optional, Any
from .base import BaseExtractor

MEDIA_EXTENSIONS = {
    # Video
    '.mp4': ('video/mp4', 'mp4', 'Video'),
    '.webm': ('video/webm', 'webm', 'Video'),
    '.mov': ('video/quicktime', 'mov', 'Video'),
    '.mkv': ('video/x-matroska', 'mkv', 'Video'),
    '.m4v': ('video/x-m4v', 'm4v', 'Video'),
    '.avi': ('video/x-msvideo', 'avi', 'Video'),
    '.flv': ('video/x-flv', 'flv', 'Video'),
    '.ogv': ('video/ogg', 'ogv', 'Video'),
    
    # Audio
    '.mp3': ('audio/mpeg', 'mp3', 'Audio'),
    '.m4a': ('audio/mp4', 'm4a', 'Audio'),
    '.wav': ('audio/wav', 'wav', 'Audio'),
    '.aac': ('audio/aac', 'aac', 'Audio'),
    '.flac': ('audio/flac', 'flac', 'Audio'),
    '.ogg': ('audio/ogg', 'ogg', 'Audio'),
    '.opus': ('audio/opus', 'opus', 'Audio'),
}

class DirectMediaExtractor(BaseExtractor):
    """
    Direct Media Extractor.
    Handles URLs that point directly to downloadable video/audio binary files.
    """
    name = "DirectMediaExtractor"
    priority = 10  # Very high priority for direct files

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path.lower()
        for ext in MEDIA_EXTENSIONS:
            if path.endswith(ext):
                return True
        return False

    def analyze(self, url: str) -> Optional[Dict[str, Any]]:
        parsed = urlparse(url)
        path = unquote(parsed.path)
        filename = os.path.basename(path) or "direct_media_file"
        title, ext = os.path.splitext(filename)
        ext_lower = ext.lower()

        # Default values
        mime_type = "video/mp4"
        format_ext = "mp4"
        media_type = "Video"

        if ext_lower in MEDIA_EXTENSIONS:
            mime_type, format_ext, media_type = MEDIA_EXTENSIONS[ext_lower]

        filesize = None
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        try:
            # Perform HEAD request to check size and content type
            res = requests.head(url, headers=headers, allow_redirects=True, timeout=8)
            if res.status_code == 200:
                if 'Content-Length' in res.headers:
                    try:
                        filesize = int(res.headers['Content-Length'])
                    except ValueError:
                        pass
                content_type = res.headers.get('Content-Type', '').split(';')[0].strip().lower()
                if content_type.startswith('video/'):
                    media_type = 'Video'
                    format_ext = content_type.split('/')[-1] or format_ext
                elif content_type.startswith('audio/'):
                    media_type = 'Audio'
                    format_ext = content_type.split('/')[-1] or format_ext
        except Exception:
            pass

        format_entry = {
            "format_id": "direct_url",
            "url": url,
            "ext": format_ext,
            "resolution": "Direct Stream",
            "quality": "Direct Source",
            "format_note": f"Direct {media_type} URL",
            "filesize": filesize,
            "vcodec": "unknown" if media_type == 'Video' else "none",
            "acodec": "unknown" if media_type == 'Audio' else "unknown",
            "has_video": media_type == 'Video',
            "has_audio": True,
            "download_type": "direct"
        }

        return {
            "title": title.replace('_', ' ').replace('-', ' ').title() or "Direct Media Resource",
            "duration": None,
            "thumbnail": None,
            "source_url": url,
            "extractor_name": self.name,
            "formats": [format_entry]
        }
