"""
VidLink Extractors Package
Provides modular plugin-based media extractors for universal website media discovery.
"""

from .base import BaseExtractor
from .direct_media import DirectMediaExtractor
from .yt_dlp_extractor import YtDlpExtractor
from .hls_extractor import HLSExtractor
from .dash_extractor import DASHExtractor
from .html_media import HTMLMediaExtractor
from .metadata_extractor import MetadataExtractor
from .generic import GenericExtractor

__all__ = [
    "BaseExtractor",
    "DirectMediaExtractor",
    "YtDlpExtractor",
    "HLSExtractor",
    "DASHExtractor",
    "HTMLMediaExtractor",
    "MetadataExtractor",
    "GenericExtractor",
]
