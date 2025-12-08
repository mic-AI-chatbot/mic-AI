import logging
import json
import random
import os
import shutil
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import Backup, ScheduledBackup
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class CreateBackupTool(BaseTool):
    """Creates a new backup for a specified data source to a destination."""
    def __init__(self, tool_name="create_backup"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new backup for a specified file system directory to a designated destination directory."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data_source": {"type": "string", "description": "The absolute path of the directory to back up."},
                "destination_dir": {"type": "string", "description": "The absolute path of the directory to store the backup archive in."},
                "backup_type": {"type": "string", "description": "The type of backup.", "enum": ["full"], "default": "full"},
                "retention_policy": {"type": "string", "description": "The retention policy for this backup (e.g., '30_days').", "default": "N/A"}
            },
            "required": ["data_source", "destination_dir"]
        }

    def execute(self, data_source: str, destination_dir: str, backup_type: str = "full", retention_policy: str = "N/A", **kwargs: Any) -> str:
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(100, 999)}"  # nosec B311
        
        if not os.path.isdir(data_source):
            return json.dumps({"error": f"Data source directory not found: {data_source}"})

        os.makedirs(destination_dir, exist_ok=True)
        
        archive_base_path = os.path.join(destination_dir, backup_id)
        
        try:
            archive_path = shutil.make_archive(archive_base_path, 'zip', data_source)
            size_bytes = os.path.getsize(archive_path)
            size_mb = size_bytes / (1024 * 1024)
        except Exception as e:
            logger.error(f"Failed to create backup archive for {data_source}: {e}")
            return json.dumps({"error": f"Failed to create backup archive: {e}"})

        db = next(get_db())
        try:
            new_backup = Backup(
                backup_id=backup_id,
                data_source=data_source,
                destination_path=archive_path,
                timestamp=datetime.now().isoformat(),
                status="completed",
                size_mb=size_mb,
                backup_type=backup_type,
                retention_policy=retention_policy
            )
            db.add(new_backup)
            db.commit()
            db.refresh(new_backup)
            report = {"message": f"Backup '{backup_id}' created successfully.", "backup_id": backup_id, "archive_path": os.path.abspath(archive_path)}
        except IntegrityError:
            db.rollback()
            report = {"error": "Failed to record backup metadata. Backup ID might already exist."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding backup metadata: {e}")
            report = {"error": f"Failed to record backup metadata: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class RestoreBackupTool(BaseTool):
    """Restores a data source from a backup."""
    def __init__(self, tool_name="restore_backup"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Restores a file system backup from a given backup ID to a target directory."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "backup_id": {"type": "string", "description": "The ID of the backup to restore from."},
                "target_dir": {"type": "string", "description": "The absolute path of the directory to restore the files to."}
            },
            "required": ["backup_id", "target_dir"]
        }

    def execute(self, backup_id: str, target_dir: str, **kwargs: Any) -> str:
        db = next(get_db())
        backup_metadata = db.query(Backup).filter(Backup.backup_id == backup_id).first()
        db.close()

        if not backup_metadata:
            return json.dumps({"error": f"Backup with ID '{backup_id}' not found."})
        
        archive_path = backup_metadata.destination_path
        if not os.path.isfile(archive_path):
            return json.dumps({"error": f"Backup archive file not found at path: {archive_path}"})

        os.makedirs(target_dir, exist_ok=True)
        
        try:
            shutil.unpack_archive(archive_path, target_dir)
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_id} to {target_dir}: {e}")
            return json.dumps({"error": f"Failed to unpack archive: {e}"})

        db = next(get_db())
        try:
            backup_metadata.status = "restored"
            db.commit()
            db.refresh(backup_metadata)
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating backup status after restore: {e}")
        finally:
            db.close()
        
        report = {"message": f"Data from backup '{backup_id}' successfully restored to '{os.path.abspath(target_dir)}'."}
        return json.dumps(report, indent=2)

class ScheduleBackupTool(BaseTool):
    """Schedules a recurring backup."""
    def __init__(self, tool_name="schedule_backup"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Schedules a recurring backup for a directory with specified frequency and retention policy."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "schedule_id": {"type": "string", "description": "A unique identifier for the backup schedule."},
                "data_source": {"type": "string", "description": "The directory to back up."},
                "destination_dir": {"type": "string", "description": "The backup destination directory."},
                "frequency": {"type": "string", "description": "How often the backup should run.", "enum": ["daily", "weekly", "monthly"]},
                "retention_policy": {"type": "string", "description": "How long backups should be kept (e.g., '30_days')."}
            },
            "required": ["schedule_id", "data_source", "destination_dir", "frequency", "retention_policy"]
        }

    def execute(self, schedule_id: str, data_source: str, destination_dir: str, frequency: str, retention_policy: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            new_schedule = ScheduledBackup(
                schedule_id=schedule_id,
                data_source=data_source,
                destination_dir=destination_dir,
                frequency=frequency,
                retention_policy=retention_policy,
                last_run="Never" # Initial status
            )
            db.add(new_schedule)
            db.commit()
            db.refresh(new_schedule)
            report = {"message": f"Backup schedule '{schedule_id}' created for '{data_source}' with '{frequency}' frequency and '{retention_policy}' retention."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Schedule with ID '{schedule_id}' already exists."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error scheduling backup: {e}")
            report = {"error": f"Failed to schedule backup: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class ListBackupsTool(BaseTool):
    """Lists all available backups."""
    def __init__(self, tool_name="list_backups"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all available backups with their details from the backup manager."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            backups = db.query(Backup).order_by(Backup.timestamp.desc()).all()
            backup_list = [{
                "backup_id": b.backup_id,
                "data_source": b.data_source,
                "destination_path": b.destination_path,
                "timestamp": b.timestamp,
                "status": b.status,
                "size_mb": b.size_mb,
                "backup_type": b.backup_type,
                "retention_policy": b.retention_policy
            } for b in backups]
            report = {
                "total_backups": len(backup_list),
                "backups": backup_list
            }
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            report = {"error": f"Failed to list backups: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)