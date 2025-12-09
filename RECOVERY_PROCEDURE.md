
# Disaster Recovery Procedure for MIC

**Last Updated: 22 November 2025**

## 1. Overview

This document outlines the standard procedure for restoring file system data from a backup in the event of data loss, corruption, or system failure. The process relies on the suite of backup and recovery tools built into the MIC system.

The core strategy involves two main steps:
1.  **Identifying a valid backup**: Use the `list_backups` tool to find a recent, completed backup.
2.  **Restoring the backup**: Use the `restore_backup` tool to extract the backup archive to a target location.

**Prerequisites:**
*   The MIC application environment must be running.
*   The backup archives and the `backup_manager.db` database file must be intact and accessible.

---

## 2. Step-by-Step Recovery Process

### Step 1: List Available Backups

First, you need to identify the `backup_id` of the backup you wish to restore. Use the `list_backups` tool to see a list of all recorded backups, sorted from newest to oldest.

**Command:**
```
list_backups
```

**Example Output:**
```json
{
  "total_backups": 2,
  "backups": [
    {
      "backup_id": "backup_20251122183005_451",
      "data_source": "E:\\mic\\documents",
      "destination_path": "E:\\mic\\db_backups_content\\backup_20251122183005_451.zip",
      "timestamp": "2025-11-22T18:30:05.123456",
      "status": "completed",
      "size_mb": 15.7,
      "backup_type": "full",
      "retention_policy": "30_days"
    },
    {
      "backup_id": "backup_20251121120000_123",
      "data_source": "E:\\mic\\documents",
      "destination_path": "E:\\mic\\db_backups_content\\backup_20251121120000_123.zip",
      "timestamp": "2025-11-21T12:00:00.000000",
      "status": "completed",
      "size_mb": 14.2,
      "backup_type": "full",
      "retention_policy": "30_days"
    }
  ]
}
```

From the output, choose the `backup_id` that represents the desired recovery point. For example, `backup_20251122183005_451`.

### Step 2: Restore the Backup

Once you have a `backup_id`, use the `restore_backup` tool to extract its contents. You must specify the `backup_id` and a `target_dir` where the files will be restored.

**Important**: Ensure the `target_dir` has sufficient disk space. The tool will restore all files from the backup into this directory. To avoid overwriting live data, it is best practice to restore to a new, empty directory first for verification.

**Command:**
```
restore_backup(backup_id="<your_backup_id>", target_dir="<absolute_path_to_restore_directory>")
```

**Example Usage:**
```
restore_backup(backup_id="backup_20251122183005_451", target_dir="E:\\mic\\restored_documents")
```

**Example Output:**
```json
{
  "message": "Data from backup 'backup_20251122183005_451' successfully restored to 'E:\\mic\\restored_documents'."
}
```

### Step 3: Verify the Restored Data

After the restore operation is complete, navigate to the `target_dir` (e.g., `E:\mic\restored_documents`) and manually inspect the files and directories to ensure the data is intact and correct.

Once verified, you can move the data to its final production location.

---

## 3. In Case of Failure

If the `restore_backup` tool fails:
1.  Check the error message provided by the tool.
2.  Ensure the backup archive file (e.g., `E:\mic\db_backups_content\backup_20251122183005_451.zip`) exists and is not corrupted.
3.  Verify that the application has the necessary read permissions for the backup archive and write permissions for the target directory.
4.  Check for sufficient disk space in the target location.
