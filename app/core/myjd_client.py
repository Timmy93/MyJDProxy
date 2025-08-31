import os
import logging
from typing import List, Dict, Optional
from myjdapi import Myjdapi

from app.core.config_manager import Config
from app.models.download_models import DownloadPackage, DownloadStatus
from app.utils.exceptions import MyJDConnectionError, MyJDOperationError


class MyJDClient:
    """MyJDownloader API client wrapper."""
    
    def __init__(self, config: Config):
        self.config = config
        self.jd = Myjdapi()
        self.device = None
        self._is_connected = False
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        if not self.config.validate():
            raise ValueError("Invalid configuration. Please check your config.toml file.")
    
    def connect(self) -> bool:
        """Connect to MyJDownloader service."""
        try:
            self.jd.connect(
                email=self.config.myjd_username,
                password=self.config.myjd_password
            )
            
            # Get device
            self.device = self.jd.get_device(self.config.myjd_deviceid)
            
            if not self.device:
                raise MyJDConnectionError(f"Device with ID {self.config.myjd_deviceid} not found")
            
            self._is_connected = True
            self.logger.info("Successfully connected to MyJDownloader")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MyJDownloader: {str(e)}")
            raise MyJDConnectionError(f"Connection failed: {str(e)}")
    
    def disconnect(self):
        """Disconnect from MyJDownloader service."""
        try:
            if self.jd:
                self.jd.disconnect()
            self._is_connected = False
            self.logger.info("Disconnected from MyJDownloader")
        except Exception as e:
            self.logger.error(f"Error during disconnection: {str(e)}")
    
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._is_connected and self.device is not None
    
    def add_download_package(
        self, 
        name: str, 
        download_links: List[str], 
        category: str = "other",
        auto_start: bool = True
    ) -> bool:
        """
        Add a download package to MyJDownloader.
        
        Args:
            name: Package name
            download_links: List of download URLs
            category: Download category (must be in allowed_categories)
            auto_start: Whether to auto-start the download
            
        Returns:
            bool: Success status
        """
        if not self.is_connected():
            raise MyJDConnectionError("Not connected to MyJDownloader")
        
        if not download_links:
            raise ValueError("No download links provided")
        
        if category not in self.config.allowed_categories:
            raise ValueError(
                f"Invalid category: {category}. "
                f"Allowed categories: {', '.join(self.config.allowed_categories)}"
            )
        
        try:
            destination_folder = os.path.join(self.config.base_path, category)
            
            package = {
                "packageName": name,
                "links": "\n".join(download_links),
                "destinationFolder": destination_folder,
                "autostart": "true" if auto_start else "false"
            }
            print(f"Adding package: {package}")
            self.device.linkgrabber.add_links([package])
            self.logger.info(f"Added download package '{name}' with {len(download_links)} links")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add download package: {str(e)}")
            raise MyJDOperationError(f"Failed to add package: {str(e)}")
    
    def get_download_packages(self) -> List[DownloadPackage]:
        """
        Get all download packages with their status.
        
        Returns:
            List[DownloadPackage]: List of download packages
        """
        if not self.is_connected():
            raise MyJDConnectionError("Not connected to MyJDownloader")
        
        try:
            packages = self.device.downloads.query_packages()
            
            download_packages = []
            for pkg in packages:
                package = DownloadPackage(
                    name=pkg.get("name", "Unknown"),
                    bytes_total=pkg.get("bytesTotal", 0),
                    bytes_loaded=pkg.get("bytesLoaded", 0),
                    status=DownloadStatus.from_string(pkg.get("status", "unknown")),
                    package_id=pkg.get("uuid", ""),
                    eta=pkg.get("eta", -1),
                    speed=pkg.get("speed", 0)
                )
                download_packages.append(package)
            
            return download_packages
            
        except Exception as e:
            self.logger.error(f"Failed to get download packages: {str(e)}")
            raise MyJDOperationError(f"Failed to get packages: {str(e)}")
    
    def get_linkgrabber_packages(self) -> List[Dict]:
        """Get packages in linkgrabber (pending downloads)."""
        if not self.is_connected():
            raise MyJDConnectionError("Not connected to MyJDownloader")
        
        try:
            return self.device.linkgrabber.query_packages()
        except Exception as e:
            self.logger.error(f"Failed to get linkgrabber packages: {str(e)}")
            raise MyJDOperationError(f"Failed to get linkgrabber packages: {str(e)}")
    
    def start_downloads(self, package_ids: Optional[List[str]] = None) -> bool:
        """Start downloads for specific packages or all packages."""
        if not self.is_connected():
            raise MyJDConnectionError("Not connected to MyJDownloader")
        
        try:
            if package_ids:
                # Start specific packages (implementation depends on myjdapi capabilities)
                self.logger.info(f"Starting downloads for packages: {package_ids}")
            else:
                # Start all downloads
                self.device.downloadcontroller.start_downloads()
                self.logger.info("Started all downloads")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start downloads: {str(e)}")
            raise MyJDOperationError(f"Failed to start downloads: {str(e)}")
    
    def pause_downloads(self, package_ids: Optional[List[str]] = None) -> bool:
        """Pause downloads for specific packages or all packages."""
        if not self.is_connected():
            raise MyJDConnectionError("Not connected to MyJDownloader")
        
        try:
            if package_ids:
                # Pause specific packages
                self.logger.info(f"Pausing downloads for packages: {package_ids}")
            else:
                # Pause all downloads
                self.device.downloadcontroller.pause_downloads()
                self.logger.info("Paused all downloads")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause downloads: {str(e)}")
            raise MyJDOperationError(f"Failed to pause downloads: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
