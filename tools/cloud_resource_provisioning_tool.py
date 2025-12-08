import logging
import json
import random
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import CloudResource
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class ProvisionCloudResourceTool(BaseTool):
    """Provisions a new cloud resource and stores its metadata in a persistent database."""
    def __init__(self, tool_name="provision_cloud_resource"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Provisions a new cloud resource (e.g., VM, database, storage bucket) on a specified cloud provider and region, storing its metadata persistently."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "resource_type": {"type": "string", "description": "The type of resource to provision.", "enum": ["vm", "database", "storage"]},
                "resource_name": {"type": "string", "description": "A unique name for the resource."},
                "provider": {"type": "string", "description": "The cloud provider.", "enum": ["aws", "azure", "gcp"], "default": "aws"},
                "region": {"type": "string", "description": "The cloud region to provision the resource in.", "default": "us-east-1"},
                "count": {"type": "integer", "description": "The number of instances of the resource to provision.", "default": 1},
                "instance_type": {"type": "string", "description": "For VMs, the instance type (e.g., 't2.micro', 'Standard_D2s_v3').", "default": "default_instance"}
            },
            "required": ["resource_type", "resource_name"]
        }

    def execute(self, resource_type: str, resource_name: str, provider: str = "aws", region: str = "us-east-1", count: int = 1, instance_type: str = "default_instance", **kwargs: Any) -> str:
        db = next(get_db())
        try:
            ip_address = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}" # Simulated IP  # nosec B311
            now = datetime.now().isoformat() + "Z"
            new_resource = CloudResource(
                resource_name=resource_name,
                resource_type=resource_type,
                provider=provider,
                region=region,
                count=count,
                status="provisioned",
                ip_address=ip_address,
                instance_type=instance_type,
                created_at=now,
                configuration=json.dumps({})
            )
            db.add(new_resource)
            db.commit()
            db.refresh(new_resource)
            report = {"message": f"{count} '{resource_type}' resource(s) named '{resource_name}' provisioned successfully on '{provider}' in '{region}'. IP: {ip_address}."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Resource '{resource_name}' already exists. Please choose a unique name."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error provisioning cloud resource: {e}")
            report = {"error": f"Failed to provision cloud resource: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class DeprovisionCloudResourceTool(BaseTool):
    """Deprovisions an existing cloud resource from the persistent database."""
    def __init__(self, tool_name="deprovision_cloud_resource"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Deprovisions an existing cloud resource, removing it from the cloud environment and its metadata from the database."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"resource_name": {"type": "string", "description": "The name of the resource to deprovision."}},
            "required": ["resource_name"]
        }

    def execute(self, resource_name: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            resource = db.query(CloudResource).filter(CloudResource.resource_name == resource_name).first()
            if resource:
                db.delete(resource)
                db.commit()
                report = {"message": f"Cloud resource '{resource_name}' deprovisioned successfully."}
            else:
                report = {"error": f"Resource '{resource_name}' not found."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error deprovisioning cloud resource: {e}")
            report = {"error": f"Failed to deprovision cloud resource: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class ConfigureCloudResourceTool(BaseTool):
    """Simulates configuring a provisioned cloud resource."""
    def __init__(self, tool_name="configure_cloud_resource"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates configuring a provisioned cloud resource (e.g., setting firewall rules, attaching storage, updating settings)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "resource_name": {"type": "string", "description": "The name of the resource to configure."},
                "configuration_settings": {"type": "object", "description": "A dictionary of configuration settings to apply (e.g., {'port_80_open': True, 'attached_volume_id': 'vol-123'})."}
            },
            "required": ["resource_name", "configuration_settings"]
        }

    def execute(self, resource_name: str, configuration_settings: Dict[str, Any], **kwargs: Any) -> str:
        db = next(get_db())
        try:
            resource = db.query(CloudResource).filter(CloudResource.resource_name == resource_name).first()
            if not resource:
                return json.dumps({"error": f"Resource '{resource_name}' not found. Please provision it first."})
            
            current_config = json.loads(resource.configuration)
            current_config.update(configuration_settings)
            resource.configuration = json.dumps(current_config)
            db.commit()
            db.refresh(resource)
            report = {"message": f"Cloud resource '{resource_name}' configured successfully.", "new_configuration": current_config}
        except Exception as e:
            db.rollback()
            logger.error(f"Error configuring cloud resource: {e}")
            report = {"error": f"Failed to configure cloud resource: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GetCloudResourceDetailsTool(BaseTool):
    """Retrieves details of a specific cloud resource."""
    def __init__(self, tool_name="get_cloud_resource_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves details of a specific cloud resource, including its type, provider, region, status, IP address, and configuration."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"resource_name": {"type": "string", "description": "The name of the resource to retrieve details for."}},
            "required": ["resource_name"]
        }

    def execute(self, resource_name: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            resource = db.query(CloudResource).filter(CloudResource.resource_name == resource_name).first()
            if not resource:
                return json.dumps({"error": f"Resource '{resource_name}' not found."})
            
            report = {
                "resource_name": resource.resource_name,
                "resource_type": resource.resource_type,
                "provider": resource.provider,
                "region": resource.region,
                "count": resource.count,
                "status": resource.status,
                "ip_address": resource.ip_address,
                "instance_type": resource.instance_type,
                "created_at": resource.created_at,
                "configuration": json.loads(resource.configuration)
            }
        except Exception as e:
            logger.error(f"Error getting cloud resource details: {e}")
            report = {"error": f"Failed to get cloud resource details: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class ListCloudResourcesTool(BaseTool):
    """Lists all provisioned cloud resources."""
    def __init__(self, tool_name="list_cloud_resources"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all provisioned cloud resources, showing their name, type, provider, region, and status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            resources = db.query(CloudResource).order_by(CloudResource.created_at.desc()).all()
            resource_list = [{
                "resource_name": r.resource_name,
                "resource_type": r.resource_type,
                "provider": r.provider,
                "region": r.region,
                "status": r.status
            } for r in resources]
            report = {
                "total_resources": len(resource_list),
                "resources": resource_list
            }
        except Exception as e:
            logger.error(f"Error listing cloud resources: {e}")
            report = {"error": f"Failed to list cloud resources: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
