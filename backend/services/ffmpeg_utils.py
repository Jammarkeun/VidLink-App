import shutil
import imageio_ffmpeg
import os
import subprocess
from typing import Optional

def get_ffmpeg_executable() -> Optional[str]:
    """
    Locates FFmpeg executable.
    Checks system PATH first, then imageio-ffmpeg static binary fallback.
    """
    # 1. System PATH check
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    # 2. imageio-ffmpeg static binary check
    try:
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_path and os.path.exists(ffmpeg_path):
            return ffmpeg_path
    except Exception:
        pass

    return None

def is_ffmpeg_available() -> bool:
    exe = get_ffmpeg_executable()
    return exe is not None and os.path.exists(exe)
