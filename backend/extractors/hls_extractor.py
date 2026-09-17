import m3u8
import requests
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any
from .base import BaseExtractor

class HLSExtractor(BaseExtractor):
    """
    HLS (.m3u8) Stream Manifest Analyzer.
    Parses HLS playlists and extracts all variant stream resolutions, bitrates, and codecs.
    """
    name = "HLSExtractor"
    priority = 30

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.path.lower().endswith('.m3u8') or '.m3u8?' in url.lower()

    def analyze(self, url: str) -> Optional[Dict[str, Any]]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200 or not res.text:
                return None

            playlist = m3u8.loads(res.text, uri=url)
            formats: List[Dict[str, Any]] = []

            if playlist.is_variant:
                for idx, stream in enumerate(playlist.playlists):
                    stream_url = urljoin(url, stream.uri)

                    res_str = "Unknown"
                    height = None
                    quality = "Adaptive"
                    if stream.stream_info.resolution:
                        w, h = stream.stream_info.resolution
                        res_str = f"{w}x{h}"
                        height = h
                        quality = f"{h}p"

                    bandwidth = stream.stream_info.bandwidth
                    bitrate_kbps = round(bandwidth / 1000) if bandwidth else None
                    codecs = stream.stream_info.codecs or "hls"
                    frame_rate = stream.stream_info.frame_rate

                    codecs_lower = codecs.lower()
                    has_video = 'video' in codecs_lower or stream.stream_info.resolution is not None
                    has_audio = 'audio' in codecs_lower or not has_video

                    formats.append({
                        "format_id": f"hls_variant_{idx}_{height or 'stream'}",
                        "url": stream_url,
                        "ext": "m3u8",
                        "resolution": res_str,
                        "quality": quality,
                        "height": height,
                        "fps": frame_rate,
                        "bitrate": bitrate_kbps,
                        "format_note": f"HLS Stream ({bitrate_kbps} kbps)" if bitrate_kbps else "HLS Variant Stream",
                        "filesize": None,
                        "vcodec": codecs,
                        "acodec": "hls_audio",
                        "has_video": has_video,
                        "has_audio": has_audio,
                        "download_type": "hls"
                    })
            else:
                # Media playlist (single stream)
                formats.append({
                    "format_id": "hls_master",
                    "url": url,
                    "ext": "m3u8",
                    "resolution": "HLS Stream",
                    "quality": "Adaptive",
                    "format_note": "HLS Live/Segmented Stream",
                    "filesize": None,
                    "vcodec": "hls",
                    "acodec": "hls",
                    "has_video": True,
                    "has_audio": True,
                    "download_type": "hls"
                })

            if not formats:
                return None

            return {
                "title": "HLS Stream Resource",
                "duration": playlist.target_duration if hasattr(playlist, 'target_duration') else None,
                "thumbnail": None,
                "source_url": url,
                "extractor_name": self.name,
                "formats": formats
            }

        except Exception:
            return None
