"""
Command Tracker
Tracks pending commands and matches them with device confirmation telegrams
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PendingCommand:
    """Represents a pending command waiting for confirmation"""
    
    def __init__(self, device_id: str, entity: str, command: dict, expected_state: dict):
        """
        Initialize pending command
        
        Args:
            device_id: Device ID
            entity: Entity name
            command: Original command dict
            expected_state: Expected state after command execution
        """
        self.device_id = device_id
        self.entity = entity
        self.command = command
        self.expected_state = expected_state
        self.timestamp = datetime.now()
        self.timeout_seconds = 5.0  # Default 5 second timeout
        self.confirmed = False
        self.timed_out = False
        self.callback = None
    
    def is_expired(self) -> bool:
        """Check if command has timed out"""
        return datetime.now() - self.timestamp > timedelta(seconds=self.timeout_seconds)
    
    def matches_state(self, state_data: dict) -> bool:
        """
        Check if received state matches expected state
        
        Args:
            state_data: Received state data
            
        Returns:
            True if state matches expected state
        """
        for key, expected_value in self.expected_state.items():
            if key not in state_data:
                continue
            
            received_value = state_data[key]
            
            # For numeric values, allow small tolerance
            if isinstance(expected_value, (int, float)) and isinstance(received_value, (int, float)):
                # Allow 5% tolerance for brightness/position values
                tolerance = abs(expected_value * 0.05) if expected_value > 0 else 1
                if abs(received_value - expected_value) <= tolerance:
                    return True
            else:
                # Exact match for other types
                if received_value == expected_value:
                    return True
        
        return False


class CommandTracker:
    """Track pending commands and match with confirmation telegrams"""
    
    def __init__(self):
        """Initialize command tracker"""
        self.pending_commands: Dict[str, list[PendingCommand]] = {}
        self.confirmation_callback: Optional[Callable] = None
        self.timeout_callback: Optional[Callable] = None
        self._cleanup_task = None
        self._running = False
    
    def start(self):
        """Start the command tracker"""
        if not self._running:
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("✓ Command tracker started")
    
    def stop(self):
        """Stop the command tracker"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
        logger.info("Command tracker stopped")
    
    def set_confirmation_callback(self, callback: Callable):
        """
        Set callback for command confirmation
        
        Args:
            callback: async function(device_id, entity, command, state_data)
        """
        self.confirmation_callback = callback
    
    def set_timeout_callback(self, callback: Callable):
        """
        Set callback for command timeout
        
        Args:
            callback: async function(device_id, entity, command)
        """
        self.timeout_callback = callback
    
    def add_pending_command(self, device_id: str, entity: str, command: dict, 
                           expected_state: dict, timeout: float = 5.0):
        """
        Add a pending command to track
        
        Args:
            device_id: Device ID
            entity: Entity name
            command: Command dictionary
            expected_state: Expected state after execution
            timeout: Timeout in seconds (default: 5.0)
        """
        pending = PendingCommand(device_id, entity, command, expected_state)
        pending.timeout_seconds = timeout
        
        if device_id not in self.pending_commands:
            self.pending_commands[device_id] = []
        
        self.pending_commands[device_id].append(pending)
        
        logger.debug(f"📋 Tracking command for {device_id}/{entity}: {command}")
        logger.debug(f"   Expected state: {expected_state}")
        logger.debug(f"   Timeout: {timeout}s")
    
    async def check_telegram(self, device_id: str, state_data: dict):
        """
        Check if received telegram confirms any pending commands
        
        Args:
            device_id: Device ID
            state_data: Received state data
        """
        if device_id not in self.pending_commands:
            return
        
        pending_list = self.pending_commands[device_id]
        confirmed_commands = []
        
        for pending in pending_list:
            if pending.confirmed or pending.timed_out:
                continue
            
            # Check if state matches expected state
            if pending.matches_state(state_data):
                pending.confirmed = True
                confirmed_commands.append(pending)
                
                elapsed = (datetime.now() - pending.timestamp).total_seconds()
                logger.info("=" * 80)
                logger.info(f"✅ COMMAND CONFIRMED")
                logger.info(f"   Device: {device_id}")
                logger.info(f"   Entity: {pending.entity}")
                logger.info(f"   Command: {pending.command}")
                logger.info(f"   Response time: {elapsed:.2f}s")
                logger.info(f"   Confirmed state: {state_data}")
                logger.info("=" * 80)
                
                # Call confirmation callback
                if self.confirmation_callback:
                    try:
                        await self.confirmation_callback(
                            device_id, 
                            pending.entity, 
                            pending.command, 
                            state_data
                        )
                    except Exception as e:
                        logger.error(f"Error in confirmation callback: {e}")
        
        # Remove confirmed commands
        if confirmed_commands:
            self.pending_commands[device_id] = [
                p for p in pending_list if p not in confirmed_commands
            ]
            
            # Clean up empty lists
            if not self.pending_commands[device_id]:
                del self.pending_commands[device_id]
    
    async def _cleanup_loop(self):
        """Background task to clean up timed out commands"""
        while self._running:
            try:
                await asyncio.sleep(1.0)  # Check every second
                await self._check_timeouts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _check_timeouts(self):
        """Check for and handle timed out commands"""
        timed_out_commands = []
        
        for device_id, pending_list in list(self.pending_commands.items()):
            for pending in pending_list:
                if pending.confirmed or pending.timed_out:
                    continue
                
                if pending.is_expired():
                    pending.timed_out = True
                    timed_out_commands.append((device_id, pending))
                    
                    logger.warning("=" * 80)
                    logger.warning(f"⏱️  COMMAND TIMEOUT")
                    logger.warning(f"   Device: {device_id}")
                    logger.warning(f"   Entity: {pending.entity}")
                    logger.warning(f"   Command: {pending.command}")
                    logger.warning(f"   Timeout: {pending.timeout_seconds}s")
                    logger.warning(f"   No confirmation received from device")
                    logger.warning("=" * 80)
                    
                    # Call timeout callback
                    if self.timeout_callback:
                        try:
                            await self.timeout_callback(
                                device_id,
                                pending.entity,
                                pending.command
                            )
                        except Exception as e:
                            logger.error(f"Error in timeout callback: {e}")
        
        # Clean up timed out commands
        for device_id, pending in timed_out_commands:
            if device_id in self.pending_commands:
                self.pending_commands[device_id] = [
                    p for p in self.pending_commands[device_id] 
                    if not (p.confirmed or p.timed_out)
                ]
                
                # Clean up empty lists
                if not self.pending_commands[device_id]:
                    del self.pending_commands[device_id]
    
    def get_pending_count(self, device_id: Optional[str] = None) -> int:
        """
        Get count of pending commands
        
        Args:
            device_id: Optional device ID to filter by
            
        Returns:
            Number of pending commands
        """
        if device_id:
            return len(self.pending_commands.get(device_id, []))
        else:
            return sum(len(cmds) for cmds in self.pending_commands.values())
    
    def get_pending_commands(self, device_id: str) -> list[PendingCommand]:
        """
        Get list of pending commands for a device
        
        Args:
            device_id: Device ID
            
        Returns:
            List of pending commands
        """
        return self.pending_commands.get(device_id, [])
    
    def clear_device_commands(self, device_id: str):
        """
        Clear all pending commands for a device
        
        Args:
            device_id: Device ID
        """
        if device_id in self.pending_commands:
            count = len(self.pending_commands[device_id])
            del self.pending_commands[device_id]
            logger.info(f"Cleared {count} pending command(s) for {device_id}")
    
    def get_stats(self) -> dict:
        """
        Get tracker statistics
        
        Returns:
            Dictionary with statistics
        """
        total_pending = 0
        total_confirmed = 0
        total_timed_out = 0
        
        for pending_list in self.pending_commands.values():
            for pending in pending_list:
                total_pending += 1
                if pending.confirmed:
                    total_confirmed += 1
                elif pending.timed_out:
                    total_timed_out += 1
        
        return {
            'total_pending': total_pending,
            'total_confirmed': total_confirmed,
            'total_timed_out': total_timed_out,
            'devices_with_pending': len(self.pending_commands)
        }
