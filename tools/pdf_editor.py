

import logging
import os
import json
from typing import List, Dict, Any, Union

from tools.base_tool import BaseTool
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.errors import PdfReadError

logger = logging.getLogger(__name__)

class PDFEditorTool(BaseTool):
    """
    A tool for editing PDF files, allowing for text extraction, merging,
    and splitting of PDF documents.
    """

    def __init__(self, tool_name: str = "PDFEditor", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Edits PDF files: extracts text, merges multiple PDFs, and splits PDFs by page ranges."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["extract_text", "merge_pdfs", "split_pdf"]},
                "file_path": {"type": "string", "description": "Absolute path to the PDF file."},
                "input_files": {"type": "array", "items": {"type": "string"}, "description": "List of absolute paths to PDF files to merge."},
                "output_path": {"type": "string", "description": "Absolute path for the output PDF file."},
                "page_ranges": {"type": "string", "description": "Page ranges to split (e.g., '1-3, 5, 7-9')."}
            },
            "required": ["operation"]
        }

    def _check_paths(self, file_paths: Union[str, List[str]], is_output: bool = False):
        """Checks if input and output paths are valid."""
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        for file_path in file_paths:
            if not os.path.isabs(file_path):
                raise ValueError(f"Path must be an absolute path: '{file_path}'")
            if not is_output and not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found at '{file_path}'")

    def extract_text(self, file_path: str) -> Dict[str, Any]:
        """Extracts text from a PDF file."""
        self._check_paths(file_path)
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return {"status": "success", "file_path": file_path, "extracted_text": text}
        except PdfReadError as e:
            raise ValueError(f"Error reading PDF file '{file_path}': {e}")

    def merge_pdfs(self, input_files: List[str], output_path: str) -> Dict[str, Any]:
        """Merges multiple PDF files into one."""
        self._check_paths(input_files)
        self._check_paths(output_path, is_output=True)

        merger = PdfWriter()
        for pdf_file in input_files:
            merger.append(pdf_file)
        
        with open(output_path, "wb") as f:
            merger.write(f)
        merger.close()
        return {"status": "success", "message": f"Successfully merged {len(input_files)} files into '{output_path}'."}

    def split_pdf(self, file_path: str, page_ranges: str, output_path: str) -> Dict[str, Any]:
        """Splits a PDF file into a new PDF containing specified page ranges."""
        self._check_paths(file_path)
        self._check_paths(output_path, is_output=True)
        if not page_ranges: raise ValueError("'page_ranges' is required for 'split_pdf' operation.")

        reader = PdfReader(file_path)
        writer = PdfWriter()
        
        pages_to_keep = []
        for part in page_ranges.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages_to_keep.extend(range(start - 1, end))
            else:
                pages_to_keep.append(int(part) - 1)
        
        for i in pages_to_keep:
            if 0 <= i < len(reader.pages):
                writer.add_page(reader.pages[i])
            else:
                self.logger.warning(f"Page {i+1} is out of bounds for '{file_path}'. Skipping.")

        with open(output_path, "wb") as f:
            writer.write(f)
        
        return {"status": "success", "message": f"Successfully split pages '{page_ranges}' from '{os.path.basename(file_path)}' to '{output_path}'."}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        try:
            if operation == "extract_text":
                return self.extract_text(kwargs['file_path'])
            elif operation == "merge_pdfs":
                return self.merge_pdfs(kwargs['input_files'], kwargs['output_path'])
            elif operation == "split_pdf":
                return self.split_pdf(kwargs['file_path'], kwargs['page_ranges'], kwargs['output_path'])
            else:
                raise ValueError(f"Invalid operation '{operation}'.")
        except (ValueError, FileNotFoundError, PdfReadError) as e:
            self.logger.error(f"An error occurred: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            return {"status": "error", "message": f"An unexpected error occurred: {e}"}

if __name__ == '__main__':
    print("Demonstrating PDFEditorTool functionality...")
    temp_dir = "temp_pdf_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    pdf_tool = PDFEditorTool()
    
    # Create dummy PDF files for demonstration
    dummy_pdf_1_path = os.path.join(temp_dir, "dummy_1.pdf")
    dummy_pdf_2_path = os.path.join(temp_dir, "dummy_2.pdf")
    dummy_pdf_3_path = os.path.join(temp_dir, "dummy_3.pdf")
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create dummy_1.pdf (3 pages)
        c = canvas.Canvas(dummy_pdf_1_path, pagesize=letter)
        c.drawString(100, 750, "Page 1 of Dummy 1")
        c.showPage()
        c.drawString(100, 750, "Page 2 of Dummy 1")
        c.showPage()
        c.drawString(100, 750, "Page 3 of Dummy 1")
        c.save()

        # Create dummy_2.pdf (2 pages)
        c = canvas.Canvas(dummy_pdf_2_path, pagesize=letter)
        c.drawString(100, 750, "Page 1 of Dummy 2")
        c.showPage()
        c.drawString(100, 750, "Page 2 of Dummy 2")
        c.save()

        # Create dummy_3.pdf (1 page)
        c = canvas.Canvas(dummy_pdf_3_path, pagesize=letter)
        c.drawString(100, 750, "Page 1 of Dummy 3")
        c.save()

        print("Dummy PDF files created.")

        # 1. Extract text
        print("\n--- Extracting text from dummy_1.pdf ---")
        text_result = pdf_tool.execute(operation="extract_text", file_path=dummy_pdf_1_path)
        print(json.dumps(text_result, indent=2))

        # 2. Merge PDFs
        print("\n--- Merging dummy_1.pdf and dummy_2.pdf ---")
        merged_pdf_path = os.path.join(temp_dir, "merged.pdf")
        merge_result = pdf_tool.execute(operation="merge_pdfs", input_files=[dummy_pdf_1_path, dummy_pdf_2_path], output_path=merged_pdf_path)
        print(json.dumps(merge_result, indent=2))

        # 3. Split PDF
        print("\n--- Splitting merged.pdf (pages 1, 3-4) ---")
        split_pdf_path = os.path.join(temp_dir, "split.pdf")
        split_result = pdf_tool.execute(operation="split_pdf", file_path=merged_pdf_path, page_ranges="1, 3-4", output_path=split_pdf_path)
        print(json.dumps(split_result, indent=2))

    except ImportError:
        print("\nSkipping PDF creation demo: 'reportlab' is not installed. Please install it to run the full demo.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")

