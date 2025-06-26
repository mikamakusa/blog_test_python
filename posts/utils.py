import markdown
from typing import Optional

def markdown_to_html(markdown_content: str) -> str:
    """Convert markdown content to HTML."""
    md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc'])
    return md.convert(markdown_content)

def extract_media_urls(content: str) -> list[str]:
    """Extract media URLs from markdown content."""
    import re
    # Look for image patterns in markdown
    image_pattern = r'!\[.*?\]\((.*?)\)'
    urls = re.findall(image_pattern, content)
    return urls 