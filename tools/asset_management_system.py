import logging
import json
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import Asset
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class AddAssetTool(BaseTool):
    """Adds a new asset to the persistent database."""
    def __init__(self, tool_name="add_asset"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a new asset to the asset management database."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "A unique identifier for the asset (e.g., a serial number)."},
                "asset_name": {"type": "string", "description": "The name of the asset."},
                "asset_type": {"type": "string", "description": "The type of asset (e.g., 'laptop', 'server', 'vehicle')."},
                "location": {"type": "string", "description": "The current physical location of the asset."},
                "purchase_date": {"type": "string", "description": "The date of purchase (YYYY-MM-DD)."}
            },
            "required": ["asset_id", "asset_name", "asset_type", "location", "purchase_date"]
        }

    def execute(self, asset_id: str, asset_name: str, asset_type: str, location: str, purchase_date: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            new_asset = Asset(
                asset_id=asset_id,
                name=asset_name,
                type=asset_type,
                location=location,
                status="active", # Default status
                purchase_date=purchase_date
            )
            db.add(new_asset)
            db.commit()
            db.refresh(new_asset)
            report = {"message": f"Asset '{asset_name}' (ID: {asset_id}) added successfully."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Asset with ID '{asset_id}' already exists."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding asset: {e}")
            report = {"error": f"Failed to add asset: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GetAssetDetailsTool(BaseTool):
    """Retrieves details of an asset from the database."""
    def __init__(self, tool_name="get_asset_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves detailed information about a specific asset from the database using its unique ID."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"asset_id": {"type": "string", "description": "The unique ID of the asset to retrieve."}},
            "required": ["asset_id"]
        }

    def execute(self, asset_id: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
            if asset:
                return json.dumps({
                    "asset_id": asset.asset_id,
                    "name": asset.name,
                    "type": asset.type,
                    "location": asset.location,
                    "status": asset.status,
                    "purchase_date": asset.purchase_date
                }, indent=2)
            else:
                return json.dumps({"error": f"Asset with ID '{asset_id}' not found."})
        except Exception as e:
            logger.error(f"Error getting asset details: {e}")
            return json.dumps({"error": f"Failed to get asset details: {e}"})
        finally:
            db.close()

class UpdateAssetStatusTool(BaseTool):
    """Updates the status of an asset in the database."""
    def __init__(self, tool_name="update_asset_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Updates the status of an asset in the database (e.g., 'active', 'in_repair', 'retired')."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "The ID of the asset to update."},
                "status": {"type": "string", "description": "The new status for the asset."}
            },
            "required": ["asset_id", "status"]
        }

    def execute(self, asset_id: str, status: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
            if asset:
                asset.status = status
                db.commit()
                db.refresh(asset)
                report = {"message": f"Status for asset '{asset_id}' updated to '{status}'."}
            else:
                report = {"error": f"Asset with ID '{asset_id}' not found."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating asset status: {e}")
            report = {"error": f"Failed to update asset status: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class SearchAssetsByTypeTool(BaseTool):
    """Searches for assets of a specific type in the database."""
    def __init__(self, tool_name="search_assets_by_type"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Searches for and retrieves all assets of a specific type from the database."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"asset_type": {"type": "string", "description": "The type of asset to search for (e.g., 'laptop')."}},
            "required": ["asset_type"]
        }

    def execute(self, asset_type: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            assets = db.query(Asset).filter(Asset.type == asset_type).all()
            asset_list = [{
                "asset_id": asset.asset_id,
                "name": asset.name,
                "type": asset.type,
                "location": asset.location,
                "status": asset.status,
                "purchase_date": asset.purchase_date
            } for asset in assets]
            report = {
                "asset_type": asset_type,
                "count": len(asset_list),
                "assets": asset_list
            }
        except Exception as e:
            logger.error(f"Error searching assets by type: {e}")
            report = {"error": f"Failed to search assets by type: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
