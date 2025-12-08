import logging
import os
import shutil
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DocumentManagementSystemTool(BaseTool):
    """
    A tool for simulating a Document Management System (DMS).
    """

    def __init__(self, tool_name: str = "document_management_system"):
        super().__init__(tool_name)
        self.metadata_file = "documents_metadata.json"
        self.content_dir = "documents_content"
        self.documents_metadata: Dict[str, Dict[str, Any]] = self._load_documents_metadata()
        os.makedirs(self.content_dir, exist_ok=True)

    @property
    def description(self) -> str:
        return "Simulates a Document Management System (DMS): uploads, retrieves, searches, downloads, deletes, and versions documents."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The document management operation to perform.",
                    "enum": ["upload_document", "get_document_details", "search_documents", "download_document", "delete_document", "create_new_version", "list_documents"]
                },
                "document_id": {"type": "string"},
                "document_name": {"type": "string"},
                "file_path": {"type": "string", "description": "Absolute path to the source file for upload."},
                "metadata": {"type": "object"},
                "query": {"type": "string"},
                "metadata_filters": {"type": "object"},
                "destination_path": {"type": "string", "description": "Absolute path to save the downloaded document."},
                "new_file_path": {"type": "string", "description": "Absolute path to the file for the new version."},
                "commit_message": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_documents_metadata(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted metadata file '{self.metadata_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_documents_metadata(self) -> None:
        with open(self.metadata_file, 'w') as f:
            json.dump(self.documents_metadata, f, indent=4)

    def _get_document_storage_path(self, document_id: str, file_name: str) -> str:
        doc_dir = os.path.join(self.content_dir, document_id)
        os.makedirs(doc_dir, exist_ok=True)
        return os.path.join(doc_dir, file_name)

    def _upload_document(self, document_id: str, document_name: str, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not all([document_id, document_name, file_path]): raise ValueError("Document ID, name, and file path cannot be empty.")
        if not os.path.isabs(file_path): raise ValueError("File path must be an absolute path.")
        if not os.path.exists(file_path) or not os.path.isfile(file_path): raise FileNotFoundError(f"Source file not found at '{file_path}'.")
        if document_id in self.documents_metadata: raise ValueError(f"Document '{document_id}' already exists.")

        file_name = os.path.basename(file_path)
        stored_file_path = self._get_document_storage_path(document_id, file_name)

        shutil.copy2(file_path, stored_file_path)
        
        new_document = {
            "document_id": document_id, "document_name": document_name, "original_file_name": file_name,
            "stored_file_path": os.path.abspath(stored_file_path), "metadata": metadata or {},
            "versions": [{
                "version_id": "v1", "timestamp": datetime.now().isoformat(),
                "content_path": os.path.abspath(stored_file_path), "commit_message": "Initial upload"
            }],
            "uploaded_at": datetime.now().isoformat(), "current_version": "v1"
        }
        self.documents_metadata[document_id] = new_document
        self._save_documents_metadata()
        return new_document

    def _get_document_details(self, document_id: str) -> Optional[Dict[str, Any]]:
        return self.documents_metadata.get(document_id)

    def _search_documents(self, query: str, metadata_filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not query and not metadata_filters: return []
        query_lower = query.lower()
        results = []
        
        for doc_id, doc_details in self.documents_metadata.items():
            match = False
            if query_lower in doc_details["document_name"].lower(): match = True
            elif "content_path" in doc_details:
                try:
                    with open(doc_details["stored_file_path"], 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if query_lower in content.lower(): match = True
                except Exception as e:
                    logger.warning(f"Could not read file {doc_details['stored_file_path']} during search: {e}")
            
            if metadata_filters:
                metadata_match = True
                for key, value in metadata_filters.items():
                    if doc_details["metadata"].get(key) != value: metadata_match = False; break
                if not metadata_match: match = False

            if match: results.append(doc_details)
        return results

    def _download_document(self, document_id: str, destination_path: str) -> Dict[str, Any]:
        if not all([document_id, destination_path]): raise ValueError("Document ID and destination path cannot be empty.")
        if not os.path.isabs(destination_path): raise ValueError("Destination path must be an absolute path.")
        document = self.documents_metadata.get(document_id)
        if not document: raise ValueError(f"Document '{document_id}' not found.")
        
        source_file_path = document["stored_file_path"]
        if not os.path.exists(source_file_path): raise FileNotFoundError(f"Stored document file not found at '{source_file_path}'.")

        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        shutil.copy2(source_file_path, destination_path)
        
        download_result = {
            "document_id": document_id, "document_name": document["document_name"],
            "downloaded_to": os.path.abspath(destination_path), "downloaded_at": datetime.now().isoformat(),
            "status": "completed"
        }
        return download_result

    def _delete_document(self, document_id: str) -> Dict[str, Any]:
        document = self.documents_metadata.get(document_id)
        if not document: raise ValueError(f"Document '{document_id}' not found.")
        
        stored_file_path = document["stored_file_path"]
        document_content_dir = os.path.dirname(stored_file_path)

        if os.path.exists(document_content_dir): shutil.rmtree(document_content_dir)
        
        del self.documents_metadata[document_id]
        self._save_documents_metadata()
        return {"document_id": document_id, "status": "deleted", "message": "Document and all versions deleted."}

    def _create_new_version(self, document_id: str, new_file_path: str, commit_message: str) -> Dict[str, Any]:
        if not all([document_id, new_file_path, commit_message]): raise ValueError("Document ID, new file path, and commit message cannot be empty.")
        if not os.path.isabs(new_file_path): raise ValueError("New file path must be an absolute path.")
        if not os.path.exists(new_file_path) or not os.path.isfile(new_file_path): raise FileNotFoundError(f"New version file not found at '{new_file_path}'.")

        document = self.documents_metadata.get(document_id)
        if not document: raise ValueError(f"Document '{document_id}' not found.")
        
        version_id = f"v{len(document['versions']) + 1}"
        file_name = os.path.basename(new_file_path)
        stored_file_path = self._get_document_storage_path(document_id, f"{version_id}_{file_name}")

        shutil.copy2(new_file_path, stored_file_path)
        
        new_version = {
            "version_id": version_id, "timestamp": datetime.now().isoformat(),
            "content_path": os.path.abspath(stored_file_path), "commit_message": commit_message
        }
        document["versions"].append(new_version)
        document["current_version"] = version_id
        document["stored_file_path"] = os.path.abspath(stored_file_path)
        self._save_documents_metadata()
        return new_version

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "upload_document":
            return self._upload_document(kwargs.get("document_id"), kwargs.get("document_name"), kwargs.get("file_path"), kwargs.get("metadata"))
        elif operation == "get_document_details":
            return self._get_document_details(kwargs.get("document_id"))
        elif operation == "search_documents":
            return self._search_documents(kwargs.get("query"), kwargs.get("metadata_filters"))
        elif operation == "download_document":
            return self._download_document(kwargs.get("document_id"), kwargs.get("destination_path"))
        elif operation == "delete_document":
            return self._delete_document(kwargs.get("document_id"))
        elif operation == "create_new_version":
            return self._create_new_version(kwargs.get("document_id"), kwargs.get("new_file_path"), kwargs.get("commit_message"))
        elif operation == "list_documents":
            return list(self.documents_metadata.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DocumentManagementSystemTool functionality...")
    tool = DocumentManagementSystemTool()
    
    dummy_file_1_path = os.path.abspath("report_v1.txt")
    download_dir = os.path.abspath("downloaded_docs")

    try:
        with open(dummy_file_1_path, "w") as f: f.write("Initial report content.")
        os.makedirs(download_dir, exist_ok=True)

        print("\n--- Uploading Document ---")
        asset_result = tool.execute(operation="upload_document", document_id="proj_report_001", document_name="Project Status Report", file_path=dummy_file_1_path, metadata={"author": "Jane Doe"})
        print(json.dumps(asset_result, indent=2))
        document_id = asset_result["document_id"]

        print("\n--- Searching Documents ---")
        search_results = tool.execute(operation="search_documents", query="report")
        print(json.dumps(search_results, indent=2))

        print("\n--- Downloading Document ---")
        download_path = os.path.join(download_dir, "downloaded_report.txt")
        download_result = tool.execute(operation="download_document", document_id=document_id, destination_path=download_path)
        print(json.dumps(download_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(dummy_file_1_path): os.remove(dummy_file_1_path)
        if os.path.exists(tool.metadata_file): os.remove(tool.metadata_file)
        if os.path.exists(tool.content_dir): shutil.rmtree(tool.content_dir)
        if os.path.exists(download_dir): shutil.rmtree(download_dir)
        print("\nCleanup complete.")