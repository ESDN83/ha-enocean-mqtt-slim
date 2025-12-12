"""
EEP Profile Loader
Loads and manages EnOcean Equipment Profiles from JSON files
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class EEPProfile:
    """Represents an EnOcean Equipment Profile"""
    
    def __init__(self, data: dict):
        """Initialize EEP profile from JSON data"""
        self.eep = data.get('eep', '')
        self.rorg_number = data.get('rorg_number', '')
        self.func_number = data.get('func_number', '')
        self.type_number = data.get('type_number', '')
        self.type_title = data.get('type_title', '')
        self.manufacturer = data.get('manufacturer', 'EnOcean')
        self.description = data.get('description', '')
        self.bidirectional = data.get('bidirectional', False)
        self.objects = data.get('objects', {})
        self.case = data.get('case', [])
        
        # Parse RORG as integer
        if isinstance(self.rorg_number, str):
            self.rorg = int(self.rorg_number, 16)
        else:
            self.rorg = self.rorg_number
    
    def get_datafields(self) -> List[dict]:
        """Get datafield definitions from first case"""
        if self.case and len(self.case) > 0:
            return self.case[0].get('datafield', [])
        return []
    
    def get_entities(self) -> List[dict]:
        """Get Home Assistant entity definitions"""
        entities = []
        for shortcut, obj in self.objects.items():
            if shortcut == 'preDefined':
                continue
            entities.append({
                'shortcut': shortcut,
                'name': obj.get('name', shortcut),
                'component': obj.get('component', 'sensor'),
                'device_class': obj.get('device_class'),
                'icon': obj.get('icon'),
                'unit': obj.get('unit')
            })
        return entities
    
    def __repr__(self) -> str:
        return f"EEPProfile({self.eep}: {self.type_title})"


class EEPLoader:
    """Load and manage EEP profiles"""
    
    def __init__(self, definitions_path: str, custom_path: str = '/config/enocean_custom_profiles'):
        """
        Initialize EEP loader
        
        Args:
            definitions_path: Path to built-in EEP definitions directory
            custom_path: Path to custom/override EEP profiles directory
        """
        self.definitions_path = Path(definitions_path)
        self.custom_path = Path(custom_path)
        self.profiles: Dict[str, EEPProfile] = {}
        self.load_all_profiles()
    
    def load_all_profiles(self):
        """Load all EEP profiles from JSON files (built-in + custom overrides)"""
        if not self.definitions_path.exists():
            logger.error(f"EEP definitions path does not exist: {self.definitions_path}")
            return
        
        # Load built-in profiles first
        count = 0
        for json_file in self.definitions_path.rglob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    profile = EEPProfile(data)
                    self.profiles[profile.eep] = profile
                    count += 1
                    logger.debug(f"Loaded EEP profile: {profile.eep} - {profile.type_title}")
            except Exception as e:
                logger.error(f"Failed to load EEP profile from {json_file}: {e}")
        
        logger.info(f"Loaded {count} built-in EEP profiles")
        
        # Load custom/override profiles
        if self.custom_path.exists():
            custom_count = 0
            override_count = 0
            for json_file in self.custom_path.rglob('*.json'):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        profile = EEPProfile(data)
                        
                        if profile.eep in self.profiles:
                            logger.info(f"🔄 Overriding EEP profile: {profile.eep} with custom version")
                            override_count += 1
                        else:
                            logger.info(f"➕ Adding custom EEP profile: {profile.eep}")
                        
                        self.profiles[profile.eep] = profile
                        custom_count += 1
                except Exception as e:
                    logger.error(f"Failed to load custom EEP profile from {json_file}: {e}")
            
            if custom_count > 0:
                logger.info(f"Loaded {custom_count} custom profiles ({override_count} overrides, {custom_count - override_count} new)")
        else:
            logger.info(f"Custom profiles directory not found: {self.custom_path}")
            logger.info(f"To add custom EEP profiles, create JSON files in: {self.custom_path}")
    
    def get_profile(self, eep: str) -> Optional[EEPProfile]:
        """
        Get EEP profile by code
        
        Args:
            eep: EEP code (e.g., 'MV-01-01', 'A5-30-03')
            
        Returns:
            EEPProfile if found, None otherwise
        """
        return self.profiles.get(eep)
    
    def get_profile_by_rorg(self, rorg: int) -> List[EEPProfile]:
        """
        Get all profiles matching RORG
        
        Args:
            rorg: RORG value (e.g., 0xA5)
            
        Returns:
            List of matching profiles
        """
        return [p for p in self.profiles.values() if p.rorg == rorg]
    
    def list_profiles(self) -> List[dict]:
        """
        List all available profiles
        
        Returns:
            List of profile summaries
        """
        return [
            {
                'eep': p.eep,
                'title': p.type_title,
                'manufacturer': p.manufacturer,
                'description': p.description
            }
            for p in sorted(self.profiles.values(), key=lambda x: x.eep)
        ]
    
    def search_profiles(self, query: str) -> List[dict]:
        """
        Search profiles by name or EEP code
        
        Args:
            query: Search query
            
        Returns:
            List of matching profile summaries
        """
        query_lower = query.lower()
        results = []
        
        for profile in self.profiles.values():
            if (query_lower in profile.eep.lower() or
                query_lower in profile.type_title.lower() or
                query_lower in profile.manufacturer.lower()):
                results.append({
                    'eep': profile.eep,
                    'title': profile.type_title,
                    'manufacturer': profile.manufacturer,
                    'description': profile.description
                })
        
        return sorted(results, key=lambda x: x['eep'])
