import os
import tempfile
import subprocess
import requests
from typing import Optional, Dict, Any, Generator
from .ffmpeg_utils import get_ffmpeg_executable

class MediaDownloader:
    """
    Downloader Engine for VidLink.
    Handles Direct HTTP file downloads, HLS stream capture, and FFmpeg video+audio merging.
    """

    @staticmethod
    def download_direct(url: str, output_path: str, headers: Optional[Dict[str, str]] = None) -> bool:
        req_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        if headers:
            req_headers.update(headers)

        try:
            with requests.get(url, headers=req_headers, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
            return True
        except Exception:
            return False

    @staticmethod
    def download_ffmpeg_stream(stream_url: str, output_path: str, format_ext: str = "mp4", headers: Optional[Dict[str, str]] = None) -> bool:
        ffmpeg_exe = get_ffmpeg_executable()
        if not ffmpeg_exe:
            return False

        request_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        }
        if headers:
            request_headers.update(headers)
        header_text = ''.join(f'{key}: {value}\r\n' for key, value in request_headers.items())

        cmd = [
            ffmpeg_exe, '-y', '-headers', header_text, '-i', stream_url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            output_path
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
            return res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0
        except Exception:
            return False

    @staticmethod
    def merge_video_audio(video_url: str, audio_url: str, output_path: str, headers: Optional[Dict[str, str]] = None) -> bool:
        ffmpeg_exe = get_ffmpeg_executable()
        if not ffmpeg_exe:
            return False

        request_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        }
        if headers:
            request_headers.update(headers)
        header_text = ''.join(f'{key}: {value}\r\n' for key, value in request_headers.items())

        cmd = [
            ffmpeg_exe, '-y', '-headers', header_text,
            '-i', video_url, '-i', audio_url,
            '-c:v', 'copy',
            '-c:a', 'aac',
            output_path
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
            return res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0
        except Exception:
            return False
