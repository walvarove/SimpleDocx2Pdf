import mammoth
import logging
import os
import base64
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def docx_to_html(docx_path, output_html_path=None, embed_images=True):
    """Convert DOCX to HTML using Mammoth
    
    Args:
        docx_path: Path to input DOCX file
        output_html_path: Path to output HTML file (optional)
        embed_images: Whether to embed images as base64 (default True)
        
    Returns:
        HTML content as string
    """
    try:
        # Configure Mammoth options
        style_map = """
            p[style-name='List Paragraph'] => ul > li:fresh
            p[style-name='Normal'] => p:fresh
            b => b
            i => i
            u => u
            strike => s
            r[style-name='Strong'] => b
            r[style-name='Emphasis'] => i
        """

        # Convert images to base64 if embed_images is True
        image_handler = None
        if embed_images:
            def handle_image(image):
                with image.open() as image_bytes:
                    data = image_bytes.read()
                    encoded_data = base64.b64encode(data).decode('utf-8')
                    return {'src': f"data:{image.content_type};base64,{encoded_data}"}
            image_handler = handle_image

        # Convert DOCX to HTML
        with open(docx_path, 'rb') as docx_file:
            result = mammoth.convert_to_html(
                docx_file,
                style_map=style_map,
                convert_image=image_handler
            )

        # Get the HTML content
        html_content = result.value

        # Add custom styles
        soup = BeautifulSoup(f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    margin: 20px; 
                }}
                ul {{ 
                    list-style-type: disc; 
                    padding-left: 2em; 
                }}
                ol {{ 
                    list-style-type: decimal; 
                    padding-left: 2em; 
                }}
                img {{ 
                    max-width: 100%; 
                }}
                table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                }}
                td, th {{ 
                    border: 1px solid #ddd; 
                    padding: 8px; 
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """, 'html.parser')

        # Pretty print the HTML
        html_content = soup.prettify()

        # Write to file if output path is provided
        if output_html_path:
            with open(output_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML file created: {output_html_path}")

        # Log any warnings
        if result.messages:
            for message in result.messages:
                logger.warning(message)

        return html_content

    except Exception as e:
        logger.error(f"Error converting DOCX to HTML: {str(e)}")
        raise