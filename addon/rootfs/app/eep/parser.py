"""
EEP Parser
Parses EnOcean telegrams using EEP profile definitions
"""
import logging
from typing import Dict, Any, Optional
from .loader import EEPProfile

logger = logging.getLogger(__name__)


class EEPParser:
    """Parse EnOcean telegrams using EEP profiles"""
    
    @staticmethod
    def extract_bits(data: bytes, bitoffs: int, bitsize: int) -> int:
        """
        Extract bits from byte array
        
        Args:
            data: Byte array
            bitoffs: Bit offset from start (0 = MSB of first byte)
            bitsize: Number of bits to extract
            
        Returns:
            Extracted value as integer
        """
        # Convert bytes to bit string
        bit_string = ''.join(format(byte, '08b') for byte in data)
        
        # Extract bits
        extracted_bits = bit_string[bitoffs:bitoffs + bitsize]
        
        # Convert to integer
        if extracted_bits:
            return int(extracted_bits, 2)
        return 0
    
    @staticmethod
    def apply_formula(value: int, formula: Any) -> Any:
        """
        Apply formula/transformation to value
        
        Args:
            value: Input value
            formula: Formula definition (can be dict with operations or direct value)
            
        Returns:
            Transformed value
        """
        # Handle simple equality check
        if isinstance(formula, dict):
            if '==' in formula:
                # Equality check: {"==": [{"var": "value"}, 1]}
                operands = formula['==']
                if len(operands) == 2:
                    left = operands[0]
                    right = operands[1]
                    if isinstance(left, dict) and 'var' in left:
                        return 1 if value == right else 0
            
            # Handle arithmetic operations
            if '+' in formula:
                # Addition
                result = 0
                for operand in formula['+']:
                    if isinstance(operand, dict):
                        result += EEPParser.apply_formula(value, operand)
                    else:
                        result += operand
                return result
            
            if '*' in formula:
                # Multiplication
                result = 1
                for operand in formula['*']:
                    if isinstance(operand, dict):
                        result *= EEPParser.apply_formula(value, operand)
                    else:
                        result *= operand
                return result
            
            if '-' in formula:
                # Subtraction
                operands = formula['-']
                if len(operands) == 2:
                    left = operands[0]
                    right = operands[1]
                    if isinstance(left, dict) and 'var' in left:
                        return value - right
                    return left - right
            
            if 'var' in formula:
                # Variable reference
                return value
        
        return value
    
    def parse_telegram(self, data_bytes: bytes, profile: EEPProfile) -> Dict[str, Any]:
        """
        Parse telegram data using EEP profile
        
        Args:
            data_bytes: Data bytes from telegram (without sender ID and status)
            profile: EEP profile to use for parsing
            
        Returns:
            Dictionary with parsed values
        """
        result = {}
        
        try:
            datafields = profile.get_datafields()
            
            for datafield in datafields:
                shortcut = datafield.get('shortcut')
                bitoffs = datafield.get('bitoffs')
                bitsize = datafield.get('bitsize')
                
                if shortcut is None or bitoffs is None or bitsize is None:
                    continue
                
                # Extract raw value
                raw_value = self.extract_bits(data_bytes, bitoffs, bitsize)
                
                # Apply inversion if specified
                if datafield.get('invert'):
                    raw_value = 1 - raw_value
                
                # Apply formula if specified
                if 'value' in datafield:
                    value = self.apply_formula(raw_value, datafield['value'])
                else:
                    value = raw_value
                
                # Apply decimals if specified
                if 'decimals' in datafield and isinstance(value, (int, float)):
                    decimals = datafield['decimals']
                    value = round(value, decimals)
                
                result[shortcut] = value
                logger.debug(f"Parsed {shortcut}: {value} (raw: {raw_value})")
            
        except Exception as e:
            logger.error(f"Error parsing telegram with profile {profile.eep}: {e}")
        
        return result
    
    def parse_telegram_with_full_data(self, full_data: bytes, profile: EEPProfile) -> Dict[str, Any]:
        """
        Parse telegram with full data including RORG, sender ID, and status
        
        Args:
            full_data: Full telegram data from ESP3 packet
            profile: EEP profile to use for parsing
            
        Returns:
            Dictionary with parsed values
        """
        # For 4BS telegrams (RORG 0xA5), data structure is:
        # [RORG, Sender ID (4 bytes), Data (4 bytes), Status]
        # We need bytes 5-8 (the 4 data bytes)
        
        logger.info(f"   📊 Parsing telegram with profile {profile.eep}")
        logger.info(f"   Full data length: {len(full_data)} bytes")
        logger.info(f"   Full data hex: {' '.join(f'{b:02x}' for b in full_data)}")
        
        if len(full_data) >= 9:
            data_bytes = full_data[5:9]
            logger.info(f"   Data bytes (5-8): {' '.join(f'{b:02x}' for b in data_bytes)}")
            result = self.parse_telegram(data_bytes, profile)
            logger.info(f"   Parsed result: {result}")
            return result
        else:
            logger.warning(f"Telegram data too short: {len(full_data)} bytes")
            return {}
