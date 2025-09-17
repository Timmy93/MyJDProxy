from enum import Enum
from dataclasses import dataclass
import logging
class DownloadStatus(Enum):
    """Download status enumeration."""
    UNKNOWN = "unknown"
    DOWNLOADING = "downloading"
    FINISHED = "finished"
    FAILED = "failed"
    PAUSED = "paused"
    PENDING = "pending"
    EXTRACTING = "extracting"
    
    @classmethod
    def from_string(cls, status_str: str) -> 'DownloadStatus':
        """Convert string status to enum."""
        status_map = {
            "downloading": cls.DOWNLOADING,
            "finished": cls.FINISHED,
            "failed": cls.FAILED,
            "paused": cls.PAUSED,
            "pending": cls.PENDING,
            "extracting": cls.EXTRACTING,
        }
        return status_map.get(status_str.lower(), cls.UNKNOWN)


@dataclass
class DownloadPackage:
    """Represents a download package."""
    name: str
    bytes_total: int
    bytes_loaded: int
    status: DownloadStatus
    package_id: str
    eta: int = -1
    speed: int = 0
    
    @property
    def progress_percentage(self) -> float:
        """Calculate download progress percentage."""
        if self.bytes_total == 0:
            return 0.0
        return (self.bytes_loaded / self.bytes_total) * 100
    
    @property
    def is_completed(self) -> bool:
        """Check if download is completed."""
        return self.status == DownloadStatus.FINISHED
    
    @property
    def is_downloading(self) -> bool:
        """Check if download is in progress."""
        return self.status == DownloadStatus.DOWNLOADING
    
    @property
    def formatted_size(self) -> str:
        """Get formatted file size."""
        return self._format_bytes(self.bytes_total)
    
    @property
    def formatted_downloaded(self) -> str:
        """Get formatted downloaded size."""
        return self._format_bytes(self.bytes_loaded)
    
    @property
    def formatted_speed(self) -> str:
        """Get formatted download speed."""
        if self.speed == 0:
            return "0 B/s"
        return f"{self._format_bytes(self.speed)}/s"
    
    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """Format bytes to human-readable format."""
        if bytes_value == 0:
            return "0 B"
        
        sizes = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while bytes_value >= 1024 and i < len(sizes) - 1:
            bytes_value /= 1024.0
            i += 1
        
        return f"{bytes_value:.1f} {sizes[i]}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "package_id": self.package_id,
            "status": self.status.value,
            "progress_percentage": self.progress_percentage,
            "bytes_total": self.bytes_total,
            "bytes_loaded": self.bytes_loaded,
            "formatted_size": self.formatted_size,
            "formatted_downloaded": self.formatted_downloaded,
            "speed": self.speed,
            "formatted_speed": self.formatted_speed,
            "eta": self.eta,
            "is_completed": self.is_completed,
            "is_downloading": self.is_downloading
        }


@dataclass
class DownloadRequest:
    """Represents a download request."""
    name: str
    links: list
    category: str = "other"
    auto_start: bool = True
    logger = logging.getLogger("DownloadRequestValidator")
    
    def validate(self, allowed_categories: list) -> bool:
        """Validate the download request."""
        if not self.name.strip():
            self.logger.warning("Download name is empty.")
            return False
        
        if not self.links or not isinstance(self.links, list):
            self.logger.warning("Download links are invalid or empty.")
            return False
        
        if self.category not in allowed_categories:
            self.logger.warning(f"Category '{self.category}' is not allowed.")
            return False
        
        return True
