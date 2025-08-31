import os
import tomllib
from typing import List


class Config:
    """Configuration manager for the MyJDownloader API application."""
    
    def __init__(self, config_file: str = "config/config.toml"):
        self.config_file = config_file
        self._config_data = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from TOML file."""
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
            
            with open(self.config_file, 'rb') as f:
                self._config_data = tomllib.load(f)
                
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {str(e)}")
    
    @property
    def myjd_username(self) -> str:
        """Get MyJDownloader username."""
        return self._config_data.get('MyJD', {}).get('username', '')
    
    @property
    def myjd_password(self) -> str:
        """Get MyJDownloader password."""
        return self._config_data.get('MyJD', {}).get('password', '')
    
    @property
    def myjd_appkey(self) -> str:
        """Get MyJDownloader app key."""
        return self._config_data.get('MyJD', {}).get('appkey', '')
    
    @property
    def myjd_deviceid(self) -> str:
        """Get MyJDownloader device ID."""
        return self._config_data.get('MyJD', {}).get('deviceid', '')
    
    @property
    def base_path(self) -> str:
        """Get base download path."""
        return self._config_data.get('Downloads', {}).get('base_path', '/downloads')
    
    @property
    def allowed_categories(self) -> List[str]:
        """Get allowed download categories."""
        return self._config_data.get('Downloads', {}).get('allowed_categories', ['other'])
    
    def validate(self) -> bool:
        """Validate configuration completeness."""
        required_fields = [
            self.myjd_username,
            self.myjd_password,
            self.myjd_appkey,
            self.myjd_deviceid,
            self.base_path
        ]
        
        return all(field.strip() for field in required_fields if isinstance(field, str))
