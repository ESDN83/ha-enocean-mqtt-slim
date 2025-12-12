"""
Web UI Application
FastAPI-based web interface for device management
"""
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
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
    status = service_state.get_status()
    return JSONResponse(content=status)


@app.get("/api/gateway-info")
async def get_gateway_info():
    """Get gateway information"""
    gateway_info = service_state.get_gateway_info()
    if not gateway_info:
        return JSONResponse(content={
            "base_id": "Not available",
            "version": "Not available",
            "chip_id": "Not available",
            "description": "Gateway not connected"
        })
    return JSONResponse(content=gateway_info)


@app.get("/api/eep-profiles")
async def get_eep_profiles():
    """Get list of available EEP profiles"""
    eep_loader = service_state.get_eep_loader()
    if not eep_loader:
        return JSONResponse(content={"profiles": []})
    
    profiles = eep_loader.list_profiles()
    return JSONResponse(content={"profiles": profiles})


@app.get("/api/devices")
async def get_devices():
    """Get list of configured devices"""
    device_manager = service_state.get_device_manager()
    if not device_manager:
        return JSONResponse(content={"devices": []})
    
    devices = device_manager.list_devices()
    return JSONResponse(content={"devices": devices})


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
    
    return JSONResponse(content={"success": True, "device_id": device.id})


@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """Get a specific device"""
    device_manager = service_state.get_device_manager()
    if not device_manager:
        raise HTTPException(status_code=503, detail="Device manager not available")
    
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return JSONResponse(content=device)


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
    
    return JSONResponse(content={"success": True})


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
    
    return JSONResponse(content={"success": True})


@app.post("/api/devices/{device_id}/enable")
async def enable_device(device_id: str):
    """Enable a device"""
    device_manager = service_state.get_device_manager()
    if not device_manager:
        raise HTTPException(status_code=503, detail="Device manager not available")
    
    success = device_manager.enable_device(device_id, True)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return JSONResponse(content={"success": True})


@app.post("/api/devices/{device_id}/disable")
async def disable_device(device_id: str):
    """Disable a device"""
    device_manager = service_state.get_device_manager()
    if not device_manager:
        raise HTTPException(status_code=503, detail="Device manager not available")
    
    success = device_manager.enable_device(device_id, False)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return JSONResponse(content={"success": True})
