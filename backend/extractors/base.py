from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class BaseExtractor(ABC):
    """
    Abstract Base Class for all VidLink Extractor Plugins.
    Every extractor plugin must implement this unified interface.
    """
    
    name: str = "BaseExtractor"
    priority: int = 100  # Lower number = higher priority

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Determines whether this extractor can attempt handling the given URL.
        Note: Generic fallback extractors should return True or check basic web structure.
        """
        pass

    @abstractmethod
    def analyze(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Analyzes the media URL and extracts metadata along with all discovered media formats.
        Returns a dict containing:
          - title: str
          - duration: float or None
          - thumbnail: str or None
          - source_url: str
          - extractor_name: str
          - formats: List[Dict]
        Or None if no media could be extracted by this plugin.
        """
        pass

    def cleanup(self) -> None:
        """
        Perform any temporary file or resource cleanup after extraction/download.
        """
        pass
