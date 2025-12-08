import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from urllib.parse import urljoin
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class AccessibilityComplianceChecker(BaseTool):
    """
    A tool to perform a basic accessibility audit on a given URL.
    It checks for common accessibility issues like missing alt text, missing language declarations,
    and missing form labels.
    """
    def __init__(self, tool_name: str = "accessibility_compliance_checker", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Audits a website for common accessibility issues (a subset of WCAG)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the website to audit."
                }
            },
            "required": ["url"]
        }

    def execute(self, url: str, **kwargs: Any) -> str:
        """
        Fetches the content of a URL and performs a basic accessibility audit.
        """
        if not url.startswith('http'):
            url = 'http://' + url

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            return f"Error: Could not fetch URL '{url}'. Reason: {e}"

        soup = BeautifulSoup(response.content, 'html.parser')
        
        issues = []
        
        # 1. Check for HTML lang attribute
        if not soup.html or not soup.html.has_attr('lang'):
            issues.append("High Priority: The <html> tag is missing a 'lang' attribute.")

        # 2. Check for a <title> tag
        if not soup.title or not soup.title.string.strip():
            issues.append("High Priority: The page is missing a <title> tag or the title is empty.")

        # 3. Check <img> tags for alt attributes
        for img in soup.find_all('img'):
            if not img.has_attr('alt'):
                src = img.get('src', 'N/A')
                issues.append(f"Medium Priority: Image is missing an 'alt' attribute. (src: {src})")
            elif not img['alt'].strip():
                # This checks for decorative images, which is fine, but we can flag it for review.
                issues.append(f"Low Priority: Image has an empty 'alt' attribute. Verify if it's purely decorative. (src: {img.get('src', 'N/A')})")

        # 4. Check for form input labels
        for input_tag in soup.find_all(['input', 'textarea', 'select']):
            if input_tag.get('type') in ['hidden', 'submit', 'reset', 'button']:
                continue
            
            has_label = False
            # Check if it's wrapped by a label
            if input_tag.find_parent('label'):
                has_label = True
            # Check if it has an 'id' and a <label> with a 'for' attribute pointing to it
            elif input_tag.has_attr('id'):
                if soup.find('label', {'for': input_tag['id']}):
                    has_label = True
            # Check for aria-label or aria-labelledby
            elif input_tag.has_attr('aria-label') or input_tag.has_attr('aria-labelledby'):
                has_label = True

            if not has_label:
                input_id = input_tag.get('id', 'N/A')
                input_name = input_tag.get('name', 'N/A')
                issues.append(f"High Priority: Form element is missing a label. (Type: {input_tag.name}, Name: {input_name}, ID: {input_id})")

        # 5. Check for link text
        for a_tag in soup.find_all('a'):
            if not a_tag.get_text(strip=True):
                # Also check for aria-label or image with alt text inside
                if not a_tag.get('aria-label') and not a_tag.find('img', alt=lambda x: x and x.strip()):
                     href = a_tag.get('href', 'N/A')
                     issues.append(f"Medium Priority: Link has no discernible text. (href: {href})")

        if not issues:
            return f"Accessibility check for '{url}' completed. No major issues found based on this basic scan."
        else:
            report = f"Accessibility report for '{url}':\n\n" + "\n".join(f"- {issue}" for issue in issues)
            return report