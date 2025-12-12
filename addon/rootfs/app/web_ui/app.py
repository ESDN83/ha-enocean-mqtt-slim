"""
Web UI Application
FastAPI-based web interface for device management
"""
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import sys
sys.path.append('/app')

from service_state import service_state

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="EnOcean MQTT Slim")

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


# Pydantic models for API
class DeviceCreate(BaseModel):
    id: str
    name: str
    eep: str
    manufacturer: str = "EnOcean"


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    eep: Optional[str] = None
    manufacturer: Optional[str] = None
    enabled: Optional[bool] = None


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse("dashboard_full.html", {
        "request": request,
        "title": "EnOcean MQTT Slim",
        "status": "Running"
    })


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/api/status")
async def get_status():
    """Get service status"""
    logger.info("=== API /api/status called ===")
    try:
        logger.info(f"service_state.service exists: {service_state.service is not None}")
        if service_state.service:
            logger.info(f"  eep_loader: {service_state.service.eep_loader is not None}")
            logger.info(f"  device_manager: {service_state.service.device_manager is not None}")
            logger.info(f"  mqtt_handler: {service_state.service.mqtt_handler is not None}")
        
        status = service_state.get_status()
        logger.info(f"Status returned: {status}")
        return status
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        return {
            "status": "error",
            "eep_profiles": 0,
            "devices": 0,
            "gateway_connected": False,
            "mqtt_connected": False
        }


@app.get("/api/gateway-info")
async def get_gateway_info():
    """Get gateway information"""
    try:
        gateway_info = service_state.get_gateway_info()
        if not gateway_info:
            return {
                "base_id": "Not available",
                "version": "Not available",
                "chip_id": "Not available",
                "description": "Gateway not connected"
            }
        return gateway_info
    except Exception as e:
        logger.error(f"Error getting gateway info: {e}", exc_info=True)
        return {
            "base_id": "Error",
            "version": "Error",
            "chip_id": "Error",
            "description": str(e)
        }


@app.get("/api/eep-profiles")
async def get_eep_profiles():
    """Get list of available EEP profiles"""
    logger.info("=== API /api/eep-profiles called ===")
    try:
        eep_loader = service_state.get_eep_loader()
        logger.info(f"eep_loader exists: {eep_loader is not None}")
        if not eep_loader:
            logger.warning("EEP loader not available yet")
            return {"profiles": []}
        
        profiles = eep_loader.list_profiles()
        logger.info(f"Returning {len(profiles)} EEP profiles")
        logger.info(f"First profile: {profiles[0] if profiles else 'None'}")
        return {"profiles": profiles}
    except Exception as e:
        logger.error(f"Error getting EEP profiles: {e}", exc_info=True)
        return {"profiles": []}


@app.get("/api/devices")
async def get_devices():
    """Get list of configured devices"""
    logger.info("=== API /api/devices called ===")
    try:
        device_manager = service_state.get_device_manager()
        logger.info(f"device_manager exists: {device_manager is not None}")
        if not device_manager:
            logger.warning("Device manager not available yet")
            return {"devices": []}
        
        devices = device_manager.list_devices()
        logger.info(f"Returning {len(devices)} devices")
        return {"devices": devices}
    except Exception as e:
        logger.error(f"Error getting devices: {e}", exc_info=True)
        return {"devices": []}


@app.post("/api/devices")
async def create_device(device: DeviceCreate):
    """Create a new device"""
    device_manager = service_state.get_device_manager()
    if not device_manager:
        raise HTTPException(status_code=503, detail="Device manager not available")
    
    # Check if device already exists
    if device_manager.get_device(device.id):
        raise HTTPException(status_code=400, detail="Device already exists")
    
    # Validate EEP profile exists
    eep_loader = service_state.get_eep_loader()
    if eep_loader and not eep_loader.get_profile(device.eep):
        raise HTTPException(status_code=400, detail=f"EEP profile {device.eep} not found")
    
    # Add device
    success = device_manager.add_device(
        device.id,
        device.name,
        device.eep,
        device.manufacturer
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add device")
    
    # Publish MQTT discovery if service is available
    if service_state.service:
        try:
            import asyncio
            device_dict = device_manager.get_device(device.id)
            await service_state.service.publish_device_discovery(device_dict)
        except Exception as e:
            logger.error(f"Error publishing discovery: {e}")
    
    return {"success": True, "device_id": device.id}


@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """Get a specific device"""
    device_manager = service_state.get_device_manager()
    if not device_manager:
        raise HTTPException(status_code=503, detail="Device manager not available")
    
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device


@app.put("/api/devices/{device_id}")
async def update_device(device_id: str, update: DeviceUpdate):
    """Update a device"""
    device_manager = service_state.get_device_manager()
    if not device_manager:
        raise HTTPException(status_code=503, detail="Device manager not available")
    
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update fields
    if update.name is not None:
        device['name'] = update.name
    if update.eep is not None:
        # Validate EEP profile
        eep_loader = service_state.get_eep_loader()
        if eep_loader and not eep_loader.get_profile(update.eep):
            raise HTTPException(status_code=400, detail=f"EEP profile {update.eep} not found")
        device['eep'] = update.eep
    if update.manufacturer is not None:
        device['manufacturer'] = update.manufacturer
    if update.enabled is not None:
        device_manager.enable_device(device_id, update.enabled)
    
    device_manager.devices[device_id] = device
    device_manager.save_devices()
    
    return {"success": True}


@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: str):
    """Delete a device"""
    device_manager = service_state.get_device_manager()
    if not device_manager:
        raise HTTPException(status_code=503, detail="Device manager not available")
    
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Remove from MQTT/HA
    mqtt_handler = service_state.get_mqtt_handler()
    eep_loader = service_state.get_eep_loader()
    if mqtt_handler and eep_loader:
        try:
            profile = eep_loader.get_profile(device['eep'])
            if profile:
                entities = profile.get_entities()
                mqtt_handler.remove_device(device_id, entities)
        except Exception as e:
            logger.error(f"Error removing device from MQTT: {e}")
    
    # Remove from device manager
    success = device_manager.remove_device(device_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove device")
    
    return {"success": True}


@app.post("/api/devices/{device_id}/enable")
async def enable_device(device_id: str):
    """Enable a device"""
    device_manager = service_state.get_device_manager()
    if not device_manager:
        raise HTTPException(status_code=503, detail="Device manager not available")
    
    success = device_manager.enable_device(device_id, True)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {"success": True}


@app.post("/api/devices/{device_id}/disable")
async def disable_device(device_id: str):
    """Disable a device"""
    device_manager = service_state.get_device_manager()
    if not device_manager:
        raise HTTPException(status_code=503, detail="Device manager not available")
    
    success = device_manager.enable_device(device_id, False)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {"success": True}
