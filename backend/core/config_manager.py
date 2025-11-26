"""
Configuration manager for system settings.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from database import SystemConfig


class ConfigManager:
    """Manage system configuration stored in database."""
    
    @staticmethod
    def get_config(db: Session) -> Dict[str, Any]:
        """
        Get all configuration as a dictionary.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary of configuration key-value pairs with proper types
        """
        configs = db.query(SystemConfig).all()
        result = {}
        
        for config in configs:
            # Convert values to appropriate types
            if config.key == "frame_interval_ms":
                result[config.key] = int(config.value)
            elif config.key == "recognition_threshold":
                result[config.key] = float(config.value)
            else:
                result[config.key] = config.value
        
        return result
    
    @staticmethod
    def update_config(db: Session, updates: Dict[str, Any]) -> None:
        """
        Update configuration values.
        
        Args:
            db: Database session
            updates: Dictionary of key-value pairs to update
        """
        for key, value in updates.items():
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            
            if config:
                # Update existing config
                config.value = str(value)
            else:
                # Create new config entry
                new_config = SystemConfig(key=key, value=str(value))
                db.add(new_config)
        
        db.commit()
    
    @staticmethod
    def get_value(db: Session, key: str, default: Any = None) -> Any:
        """
        Get a single configuration value.
        
        Args:
            db: Database session
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value with appropriate type
        """
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        
        if not config:
            return default
        
        # Convert to appropriate type
        if key == "frame_interval_ms":
            return int(config.value)
        elif key == "recognition_threshold":
            return float(config.value)
        else:
            return config.value
