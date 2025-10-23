import os
import logging
from typing import List, Dict, Optional
from myjdapi import Myjdapi
from myjdapi.exception import MYJDTokenInvalidException

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
    
    def _refresh_connection(self) -> bool:
        """
        Refresh the connection token using reconnect.
        
        Returns:
            bool: True if reconnection was successful, False otherwise.
        """
        try:
            self.logger.info("Attempting to refresh expired token...")
            self.jd.reconnect()
            self.logger.info("Token refreshed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to refresh token: {str(e)}")
            # If reconnect fails, try a full reconnect
            try:
                self.logger.info("Reconnect failed, attempting full connection...")
                self.connect()
                return True
            except Exception as connect_error:
                self.logger.error(f"Full connection also failed: {str(connect_error)}")
                return False
    
    def add_download_package(
        self,
        name: str,
        download_links: List[str],
        category: str = "other",
        auto_start: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        Add a download package to MyJDownloader.
        
        Args:
            name: Package name
            download_links: List of download URLs
            category: Download category (must be in allowed_categories)
            auto_start: Whether to auto-start the download
            
        Returns:
            dict: Result with 'success' and 'message' keys
        """
        result = {
            "success": False,
            "message": ""
        }
        try:
            if not self.is_connected():
                self.connect()
        except MyJDConnectionError as e:
            self.logger.error(f"Cannot add download package, connection error: {str(e)}")
            result["message"] = f"Connection error: {str(e)}"
            return result
        if not self.is_connected():
            self.logger.warning("Not connected to MyJDownloader")
            result["message"] = "Not connected to MyJDownloader"
        elif not download_links:
            self.logger.warning("No download links provided")
            result["message"] = "No download links provided"
        elif category not in self.config.allowed_categories:
            self.logger.warning(f"Invalid category provided [{category}]. Cannot request download")
            result["message"] = "Invalid category"
        else:
            try:
                destination_folder = os.path.join(self.config.base_path, category)
                package = {
                    "packageName": name,
                    "links": "\n".join(download_links),
                    "destinationFolder": destination_folder,
                    "autostart": "true" if auto_start else "false"
                }
                print(f"Adding package: {package}")
                self._add_links_with_retry(package)
                self.logger.info(f"Added download package '{name}' with {len(download_links)} links")
                result["success"] = True
                result["message"] = f"Package '{name}' added successfully"
            except Exception as e:
                self.logger.error(f"Failed to add download package: {str(e)}")
                raise MyJDOperationError(f"Failed to add package: {str(e)}")
        return result
    
    def _add_links_with_retry(self, package: dict, retry_count: int = 0) -> None:
        """
        Add links to linkgrabber with automatic retry on token expiration.
        
        Args:
            package: Package dictionary with links and metadata
            retry_count: Current retry attempt (used internally)
            
        Raises:
            MyJDOperationError: If the operation fails after retry
        """
        try:
            self.device.linkgrabber.add_links([package])
        except MYJDTokenInvalidException as e:
            if retry_count == 0:
                self.logger.warning(f"Token invalid error detected: {str(e)}")
                if self._refresh_connection():
                    self.logger.info("Retrying add_links after token refresh...")
                    self._add_links_with_retry(package, retry_count=1)
                else:
                    raise MyJDOperationError("Failed to refresh connection after token expiration")
            else:
                self.logger.error("Token still invalid after refresh attempt")
                raise MyJDOperationError(f"Token invalid even after reconnection: {str(e)}")
            

    
    def get_download_packages(self) -> List[DownloadPackage]:
        """
        Get all download packages with their status.
        
        Returns:
            List[DownloadPackage]: List of download packages
        """
        if not self.is_connected():
            raise MyJDConnectionError("Not connected to MyJDownloader")
        
        try:
            packages = self._query_packages_with_retry()
            
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
    
    def _query_packages_with_retry(self, retry_count: int = 0) -> List[Dict]:
        """
        Query download packages with automatic retry on token expiration.
        
        Args:
            retry_count: Current retry attempt (used internally)
            
        Returns:
            List[Dict]: List of package dictionaries
            
        Raises:
            MyJDOperationError: If the operation fails after retry
        """
        try:
            return self.device.downloads.query_packages()
        except MYJDTokenInvalidException as e:
            if retry_count == 0:
                self.logger.warning(f"Token invalid error detected in query_packages: {str(e)}")
                if self._refresh_connection():
                    self.logger.info("Retrying query_packages after token refresh...")
                    return self._query_packages_with_retry(retry_count=1)
                else:
                    raise MyJDOperationError("Failed to refresh connection after token expiration")
            else:
                self.logger.error("Token still invalid after refresh attempt")
                raise MyJDOperationError(f"Token invalid even after reconnection: {str(e)}")
    
    def get_linkgrabber_packages(self) -> List[Dict]:
        """Get packages in linkgrabber (pending downloads)."""
        if not self.is_connected():
            raise MyJDConnectionError("Not connected to MyJDownloader")
        
        try:
            return self._query_linkgrabber_with_retry()
        except Exception as e:
            self.logger.error(f"Failed to get linkgrabber packages: {str(e)}")
            raise MyJDOperationError(f"Failed to get linkgrabber packages: {str(e)}")
    
    def _query_linkgrabber_with_retry(self, retry_count: int = 0) -> List[Dict]:
        """
        Query linkgrabber packages with automatic retry on token expiration.
        
        Args:
            retry_count: Current retry attempt (used internally)
            
        Returns:
            List[Dict]: List of linkgrabber package dictionaries
            
        Raises:
            MyJDOperationError: If the operation fails after retry
        """
        try:
            return self.device.linkgrabber.query_packages()
        except MYJDTokenInvalidException as e:
            if retry_count == 0:
                self.logger.warning(f"Token invalid error detected in linkgrabber query: {str(e)}")
                if self._refresh_connection():
                    self.logger.info("Retrying linkgrabber query after token refresh...")
                    return self._query_linkgrabber_with_retry(retry_count=1)
                else:
                    raise MyJDOperationError("Failed to refresh connection after token expiration")
            else:
                self.logger.error("Token still invalid after refresh attempt")
                raise MyJDOperationError(f"Token invalid even after reconnection: {str(e)}")
    
    def start_downloads(self, package_ids: Optional[List[str]] = None) -> bool:
        """Start downloads for specific packages or all packages."""
        if not self.is_connected():
            raise MyJDConnectionError("Not connected to MyJDownloader")
        
        try:
            self._start_downloads_with_retry(package_ids)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start downloads: {str(e)}")
            raise MyJDOperationError(f"Failed to start downloads: {str(e)}")
    
    def _start_downloads_with_retry(self, package_ids: Optional[List[str]] = None, retry_count: int = 0) -> None:
        """
        Start downloads with automatic retry on token expiration.
        
        Args:
            package_ids: Optional list of package IDs to start
            retry_count: Current retry attempt (used internally)
            
        Raises:
            MyJDOperationError: If the operation fails after retry
        """
        try:
            if package_ids:
                # Start specific packages (implementation depends on myjdapi capabilities)
                self.logger.info(f"Starting downloads for packages: {package_ids}")
            else:
                # Start all downloads
                self.device.downloadcontroller.start_downloads()
                self.logger.info("Started all downloads")
        except MYJDTokenInvalidException as e:
            if retry_count == 0:
                self.logger.warning(f"Token invalid error detected in start_downloads: {str(e)}")
                if self._refresh_connection():
                    self.logger.info("Retrying start_downloads after token refresh...")
                    self._start_downloads_with_retry(package_ids, retry_count=1)
                else:
                    raise MyJDOperationError("Failed to refresh connection after token expiration")
            else:
                self.logger.error("Token still invalid after refresh attempt")
                raise MyJDOperationError(f"Token invalid even after reconnection: {str(e)}")
    
    def pause_downloads(self, package_ids: Optional[List[str]] = None) -> bool:
        """Pause downloads for specific packages or all packages."""
        if not self.is_connected():
            raise MyJDConnectionError("Not connected to MyJDownloader")
        
        try:
            self._pause_downloads_with_retry(package_ids)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause downloads: {str(e)}")
            raise MyJDOperationError(f"Failed to pause downloads: {str(e)}")
    
    def _pause_downloads_with_retry(self, package_ids: Optional[List[str]] = None, retry_count: int = 0) -> None:
        """
        Pause downloads with automatic retry on token expiration.
        
        Args:
            package_ids: Optional list of package IDs to pause
            retry_count: Current retry attempt (used internally)
            
        Raises:
            MyJDOperationError: If the operation fails after retry
        """
        try:
            if package_ids:
                # Pause specific packages
                self.logger.info(f"Pausing downloads for packages: {package_ids}")
            else:
                # Pause all downloads
                self.device.downloadcontroller.pause_downloads()
                self.logger.info("Paused all downloads")
        except MYJDTokenInvalidException as e:
            if retry_count == 0:
                self.logger.warning(f"Token invalid error detected in pause_downloads: {str(e)}")
                if self._refresh_connection():
                    self.logger.info("Retrying pause_downloads after token refresh...")
                    self._pause_downloads_with_retry(package_ids, retry_count=1)
                else:
                    raise MyJDOperationError("Failed to refresh connection after token expiration")
            else:
                self.logger.error("Token still invalid after refresh attempt")
                raise MyJDOperationError(f"Token invalid even after reconnection: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
