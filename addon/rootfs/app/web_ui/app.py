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


@app.get("/api/eep-profiles/{eep_code}")
async def get_eep_profile(eep_code: str):
    """Get detailed information about a specific EEP profile"""
    logger.info(f"=== API /api/eep-profiles/{eep_code} called ===")
    try:
        eep_loader = service_state.get_eep_loader()
        if not eep_loader:
            raise HTTPException(status_code=503, detail="EEP loader not available")
        
        profile = eep_loader.get_profile(eep_code)
        if not profile:
            raise HTTPException(status_code=404, detail=f"EEP profile {eep_code} not found")
        
        # Return full profile data
        return {
            "eep": profile.eep,
            "title": profile.type_title,
            "description": profile.description,
            "telegram": getattr(profile, 'telegram', 'N/A'),
            "rorg_number": profile.rorg_number,
            "func_number": profile.func_number,
            "type_number": profile.type_number,
            "manufacturer": profile.manufacturer,
            "bidirectional": profile.bidirectional,
            "objects": profile.objects,
            "case": profile.case
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting EEP profile {eep_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
    
    # Publish MQTT discovery immediately if service is available
    if service_state.service:
        try:
            device_dict = device_manager.get_device(device.id)
            logger.info(f"Publishing MQTT discovery for new device {device.id}")
            await service_state.service.publish_device_discovery(device_dict)
            logger.info(f"MQTT discovery published successfully for {device.id}")
            
            # Mark discovery as published to prevent republishing on first telegram
            device_dict['discovery_published'] = True
            device_manager.devices[device.id] = device_dict
            
        except Exception as e:
            logger.error(f"Error publishing discovery for {device.id}: {e}", exc_info=True)
            # Don't fail the request, but log the error
    else:
        logger.warning(f"Service not available, MQTT discovery not published for {device.id}")
    
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
    
    # Track if EEP changed (requires republishing discovery)
    eep_changed = False
    
    # Update fields
    if update.name is not None:
        device['name'] = update.name
    if update.eep is not None:
        # Validate EEP profile
        eep_loader = service_state.get_eep_loader()
        if eep_loader and not eep_loader.get_profile(update.eep):
            raise HTTPException(status_code=400, detail=f"EEP profile {update.eep} not found")
        if device['eep'] != update.eep:
            eep_changed = True
        device['eep'] = update.eep
    if update.manufacturer is not None:
        device['manufacturer'] = update.manufacturer
    if update.enabled is not None:
        device_manager.enable_device(device_id, update.enabled)
    
    device_manager.devices[device_id] = device
    device_manager.save_devices()
    
    # Republish MQTT discovery if EEP changed
    if eep_changed and service_state.service:
        try:
            logger.info(f"EEP changed for device {device_id}, republishing MQTT discovery")
            await service_state.service.publish_device_discovery(device)
            logger.info(f"MQTT discovery republished successfully for {device_id}")
        except Exception as e:
            logger.error(f"Error republishing discovery for {device_id}: {e}", exc_info=True)
    
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


@app.get("/api/suggest-profiles/{device_id}")
async def suggest_profiles(device_id: str):
    """
    Suggest compatible EEP profiles for a device ID
    Returns profiles that were detected during teach-in
    """
    logger.info(f"=== API /api/suggest-profiles/{device_id} called ===")
    try:
        # Normalize device ID to lowercase for lookup (telegrams use lowercase)
        device_id_lower = device_id.lower()
        logger.info(f"Normalized device ID for lookup: {device_id_lower}")
        
        # Get cached detected profiles
        detected_eeps = service_state.get_detected_profiles(device_id_lower)
        
        if detected_eeps:
            # Get full profile information
            eep_loader = service_state.get_eep_loader()
            if eep_loader:
                suggested_profiles = []
                for eep in detected_eeps:
                    profile = eep_loader.get_profile(eep)
                    if profile:
                        suggested_profiles.append({
                            'eep': profile.eep,
                            'title': profile.type_title,
                            'description': profile.description,
                            'manufacturer': profile.manufacturer
                        })
                
                logger.info(f"Found {len(suggested_profiles)} suggested profiles for {device_id}")
                return {
                    "device_id": device_id,
                    "suggested_profiles": suggested_profiles,
                    "has_suggestions": True,
                    "message": f"Found {len(suggested_profiles)} compatible profiles from teach-in detection."
                }
        
        logger.info(f"No suggested profiles found for {device_id}")
        return {
            "device_id": device_id,
            "suggested_profiles": [],
            "has_suggestions": False,
            "message": "No teach-in data available. All profiles shown."
        }
        
    except Exception as e:
        logger.error(f"Error suggesting profiles for {device_id}: {e}", exc_info=True)
        return {
            "device_id": device_id,
            "suggested_profiles": [],
            "has_suggestions": False,
            "message": str(e)
        }
