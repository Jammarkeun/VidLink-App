from urllib.parse import urlparse
import requests
from typing import Dict, List, Optional, Any
from backend.extractors import (
    DirectMediaExtractor,
    YtDlpExtractor,
    HLSExtractor,
    DASHExtractor,
    HTMLMediaExtractor,
    MetadataExtractor,
    GenericExtractor
)

class MediaExtractionPipeline:
    """
    Master Media Extraction Orchestrator for VidLink.
    Enforces UNIVERSAL WEBSITE SUPPORT without domain whitelists.
    Runs multi-strategy pipeline and aggregates all discovered formats dynamically.
    """

    def __init__(self):
        # Register all modular extractor plugins in priority order
        self.extractors = [
            DirectMediaExtractor(),
            YtDlpExtractor(),
            HLSExtractor(),
            DASHExtractor(),
            HTMLMediaExtractor(),
            MetadataExtractor(),
            GenericExtractor()
        ]

    def validate_url(self, url: str) -> bool:
        if not url or not isinstance(url, str):
            return False
        parsed = urlparse(url.strip())
        return parsed.scheme in ['http', 'https'] and bool(parsed.netloc)

    def analyze_url(self, url: str) -> Dict[str, Any]:
        url = url.strip()
        if not self.validate_url(url):
            return {
                "success": False,
                "error_code": "INVALID_URL",
                "error": "Invalid URL provided. Please submit a valid HTTP/HTTPS web URL.",
                "source_url": url
            }

        # Check preliminary HTTP status / accessibility
        try:
            head_res = requests.head(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }, allow_redirects=True, timeout=6)
            if head_res.status_code in [401, 403]:
                return {
                    "success": False,
                    "error_code": "AUTHENTICATION_REQUIRED",
                    "error": "The source requires authentication or protected access.",
                    "source_url": url
                }
        except Exception:
            pass

        aggregated_title = None
        aggregated_duration = None
        aggregated_thumbnail = None
        successful_extractor = None
        all_formats: List[Dict[str, Any]] = []
        seen_format_keys = set()
        executed_strategies: List[str] = []
        extraction_errors: List[str] = []

        for extractor in self.extractors:
            try:
                if not extractor.can_handle(url):
                    continue

                executed_strategies.append(extractor.name)
                result = extractor.analyze(url)

                if not result and getattr(extractor, 'last_error', None):
                    extraction_errors.append(f"{extractor.name}: {extractor.last_error}")

                if result and result.get('formats'):
                    successful_extractor = extractor.name
                    aggregated_title = aggregated_title or result.get('title')
                    aggregated_duration = aggregated_duration or result.get('duration')
                    aggregated_thumbnail = aggregated_thumbnail or result.get('thumbnail')

                    for fmt in result['formats']:
                        fmt.setdefault('source_url', url)
                        # Generate unique key to prevent duplicate formats
                        fmt_key = (fmt.get('url'), fmt.get('resolution'), fmt.get('ext'))
                        if fmt_key not in seen_format_keys:
                            seen_format_keys.add(fmt_key)
                            all_formats.append(fmt)

            except Exception as error:
                extraction_errors.append(f"{extractor.name}: {error}")
                continue

        if not all_formats:
            return {
                "success": False,
                "error_code": "NO_MEDIA_FOUND",
                "error": "No publicly accessible media was detected.",
                "source_url": url,
                "strategies_executed": executed_strategies,
                "extraction_errors": extraction_errors
            }

        # Format Normalization and Dynamic Classification
        normalized_formats = self._normalize_formats(all_formats)

        return {
            "success": True,
            "title": aggregated_title or "Discovered Media Resource",
            "duration": aggregated_duration,
            "thumbnail": aggregated_thumbnail,
            "source_url": url,
            "source_domain": urlparse(url).netloc,
            "extractor_used": successful_extractor or "Multi-Layer Engine",
            "strategies_executed": executed_strategies,
            "total_formats_discovered": len(normalized_formats),
            "formats": normalized_formats
        }

    def _normalize_formats(self, formats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for fmt in formats:
            has_video = fmt.get('has_video', True)
            has_audio = fmt.get('has_audio', True)
            
            if has_video and has_audio:
                stream_type = "video_audio"
                badge = "Video + Audio"
            elif has_video:
                stream_type = "video_only"
                badge = "Video Only"
            elif has_audio:
                stream_type = "audio_only"
                badge = "Audio Only"
            else:
                stream_type = "unknown"
                badge = "Media Stream"

            filesize = fmt.get('filesize')
            filesize_formatted = self._format_size(filesize) if filesize else "Stream / Variable"

            normalized.append({
                "format_id": fmt.get('format_id', 'fmt_0'),
                "url": fmt.get('url'),
                "ext": (fmt.get('ext') or 'mp4').lower(),
                "resolution": fmt.get('resolution') or "Unknown",
                "quality": fmt.get('quality') or "Standard",
                "height": fmt.get('height'),
                "fps": fmt.get('fps'),
                "bitrate": fmt.get('bitrate'),
                "format_note": fmt.get('format_note') or badge,
                "filesize": filesize,
                "filesize_formatted": filesize_formatted,
                "vcodec": fmt.get('vcodec') or 'unknown',
                "acodec": fmt.get('acodec') or 'unknown',
                "has_video": has_video,
                "has_audio": has_audio,
                "stream_type": stream_type,
                "badge": badge,
                "download_type": fmt.get('download_type', 'direct'),
                "http_headers": fmt.get('http_headers'),
                "source_url": fmt.get('source_url')
            })
        
        # Sort formats logically: highest resolution/height first, then video+audio, then audio
        normalized.sort(
            key=lambda x: (
                1 if x['stream_type'] == 'video_audio' else (2 if x['stream_type'] == 'video_only' else 3),
                -(x['height'] or 0),
                -(x['bitrate'] or 0)
            )
        )
        return normalized

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if not size_bytes:
            return "Unknown"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if abs(size_bytes) < 1024.0:
                return f"{size_bytes:3.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
