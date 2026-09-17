import yt_dlp
from typing import Dict, List, Optional, Any
from .base import BaseExtractor

class YtDlpExtractor(BaseExtractor):
    """
    yt-dlp Media Extractor Plugin.
    Leverages yt-dlp's generic and site-specific engine without domain whitelisting.
    Discovers all available formats without artificial caps.
    """
    name = "YtDlpExtractor"
    priority = 20  # High priority for rich media extraction

    def can_handle(self, url: str) -> bool:
        # Accepts any valid HTTP/HTTPS URL
        return url.startswith("http://") or url.startswith("https://")

    def analyze(self, url: str) -> Optional[Dict[str, Any]]:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'ignoreerrors': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None

                # Handle playlist vs single video
                if '_type' in info and info['_type'] == 'playlist':
                    entries = info.get('entries', [])
                    if entries:
                        info = entries[0]
                    else:
                        return None

                title = info.get('title') or info.get('id') or "Extracted Media"
                duration = info.get('duration')
                thumbnail = info.get('thumbnail')
                
                raw_formats = info.get('formats', [])
                formats: List[Dict[str, Any]] = []

                if raw_formats:
                    for fmt in raw_formats:
                        fmt_url = fmt.get('url')
                        if not fmt_url:
                            continue

                        format_id = str(fmt.get('format_id', 'yt_format'))
                        ext = fmt.get('ext') or 'mp4'
                        resolution = fmt.get('resolution') or (
                            f"{fmt.get('width')}x{fmt.get('height')}" if fmt.get('width') and fmt.get('height') else "Audio Only"
                        )
                        height = fmt.get('height')
                        quality = f"{height}p" if height else ("Audio" if fmt.get('vcodec') == 'none' else "SD")
                        
                        vcodec = fmt.get('vcodec') or 'none'
                        acodec = fmt.get('acodec') or 'none'
                        
                        has_video = vcodec != 'none'
                        has_audio = acodec != 'none'

                        filesize = fmt.get('filesize') or fmt.get('filesize_approx')
                        fps = fmt.get('fps')
                        tbr = fmt.get('tbr') or fmt.get('vbr') or fmt.get('abr')

                        format_note = fmt.get('format_note') or ""
                        if not format_note:
                            if has_video and has_audio:
                                format_note = "Video + Audio"
                            elif has_video:
                                format_note = "Video Only"
                            elif has_audio:
                                format_note = "Audio Only"

                        formats.append({
                            "format_id": format_id,
                            "url": fmt_url,
                            "ext": ext,
                            "resolution": resolution,
                            "quality": quality,
                            "height": height,
                            "fps": fps,
                            "bitrate": tbr,
                            "format_note": format_note,
                            "filesize": filesize,
                            "vcodec": vcodec,
                            "acodec": acodec,
                            "has_video": has_video,
                            "has_audio": has_audio,
                            "download_type": "ytdlp_format",
                            "http_headers": fmt.get('http_headers')
                        })
                elif info.get('url'):
                    # Fallback single URL in yt-dlp info
                    formats.append({
                        "format_id": "ytdlp_direct",
                        "url": info['url'],
                        "ext": info.get('ext', 'mp4'),
                        "resolution": "Default Stream",
                        "quality": "Standard",
                        "format_note": "Media Stream",
                        "filesize": info.get('filesize'),
                        "vcodec": info.get('vcodec', 'unknown'),
                        "acodec": info.get('acodec', 'unknown'),
                        "has_video": True,
                        "has_audio": True,
                        "download_type": "direct"
                    })

                if not formats:
                    return None

                return {
                    "title": title,
                    "duration": duration,
                    "thumbnail": thumbnail,
                    "source_url": url,
                    "extractor_name": self.name,
                    "formats": formats
                }

        except Exception as e:
            # yt-dlp failed or raised error (e.g. auth required, private content)
            return None
