"""
State Persistence Manager
Saves and restores device states to prevent unavailability after restarts
"""
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class StatePersistence:
    """Manage device state persistence across restarts"""
    
    def __init__(self, state_file: str = "/data/device_states.json"):
        """
        Initialize state persistence manager
        
        Args:
            state_file: Path to state file
        """
        self.state_file = state_file
        self.states: Dict[str, Dict[str, Any]] = {}
        self._load_states()
    
    def _load_states(self):
        """Load states from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    self.states = json.load(f)
                logger.info(f"Loaded {len(self.states)} device states from {self.state_file}")
            else:
                logger.info("No previous state file found, starting fresh")
                self.states = {}
        except Exception as e:
            logger.error(f"Error loading states: {e}")
            self.states = {}
    
    def _save_states(self):
        """Save states to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            with open(self.state_file, 'w') as f:
                json.dump(self.states, f, indent=2)
            logger.debug(f"Saved {len(self.states)} device states to {self.state_file}")
        except Exception as e:
            logger.error(f"Error saving states: {e}")
    
    def save_state(self, device_id: str, state_data: Dict[str, Any]):
        """
        Save device state
        
        Args:
            device_id: Device ID
            state_data: State data dictionary
        """
        try:
            # Store state with timestamp
            self.states[device_id] = {
                "state": state_data,
                "saved_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            self._save_states()
            logger.debug(f"Saved state for device {device_id}")
        except Exception as e:
            logger.error(f"Error saving state for {device_id}: {e}")
    
    def get_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get saved state for device
        
        Args:
            device_id: Device ID
            
        Returns:
            State data dictionary or None if not found
        """
        try:
            if device_id in self.states:
                return self.states[device_id].get("state")
            return None
        except Exception as e:
            logger.error(f"Error getting state for {device_id}: {e}")
            return None
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all saved states
        
        Returns:
            Dictionary of device_id -> state_data
        """
        try:
            return {device_id: data.get("state") for device_id, data in self.states.items()}
        except Exception as e:
            logger.error(f"Error getting all states: {e}")
            return {}
    
    def remove_state(self, device_id: str):
        """
        Remove saved state for device
        
        Args:
            device_id: Device ID
        """
        try:
            if device_id in self.states:
                del self.states[device_id]
                self._save_states()
                logger.debug(f"Removed state for device {device_id}")
        except Exception as e:
            logger.error(f"Error removing state for {device_id}: {e}")
    
    def clear_all_states(self):
        """Clear all saved states"""
        try:
            self.states = {}
            self._save_states()
            logger.info("Cleared all saved states")
        except Exception as e:
            logger.error(f"Error clearing states: {e}")
