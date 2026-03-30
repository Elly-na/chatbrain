"""
file_handler.py
Handles all uploaded file types:
- PDF (lab manuals, notes)
- Images (network diagrams, screenshots)
- Text/Config files (.txt, .cfg)
- Word documents (.docx)
"""

import os
import base64
from werkzeug.utils import secure_filename

# Try importing optional libraries with helpful error messages
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("⚠️  PyPDF2 not installed. PDF support disabled. Run: pip install PyPDF2")

try:
    from PIL import Image
    IMAGE_SUPPORT = True
except ImportError:
    IMAGE_SUPPORT = False
    print("⚠️  Pillow not installed. Image processing limited. Run: pip install Pillow")

try:
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False
    print("⚠️  python-docx not installed. DOCX support disabled. Run: pip install python-docx")


# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt', 'cfg', 'docx'}

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_extension(filename):
    """Get file extension in lowercase"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def extract_pdf_text(file_path):
    """Extract text from PDF files (lab manuals, notes)"""
    if not PDF_SUPPORT:
        return "PDF reading not available. Please install PyPDF2: pip install PyPDF2"

    try:
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)

            # Limit to first 20 pages to avoid huge API costs
            pages_to_read = min(total_pages, 20)

            for i in range(pages_to_read):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text += f"\n--- Page {i+1} ---\n{page_text}"

            if total_pages > 20:
                text += f"\n\n[Note: Only first 20 of {total_pages} pages were read]"

        return text.strip() if text.strip() else "Could not extract text from PDF (may be scanned image)"

    except Exception as e:
        return f"Error reading PDF: {str(e)}"


def extract_docx_text(file_path):
    """Extract text from Word documents"""
    if not DOCX_SUPPORT:
        return "Word document reading not available. Please install python-docx: pip install python-docx"

    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text + "\n"
        return text.strip() if text.strip() else "Empty document"
    except Exception as e:
        return f"Error reading Word document: {str(e)}"


def extract_config_text(file_path):
    """Read Cisco config files (.txt, .cfg)"""
    try:
        # Try UTF-8 first, fall back to latin-1
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def encode_image_to_base64(file_path):
    """Convert image to base64 string for Claude API"""
    try:
        # Resize large images to save API costs
        if IMAGE_SUPPORT:
            img = Image.open(file_path)

            # Convert RGBA to RGB if needed (for PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Resize if too large (max 1500px on longest side)
            max_size = 1500
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Save resized image to temp path
            temp_path = file_path + "_resized.jpg"
            img.save(temp_path, 'JPEG', quality=85)

            with open(temp_path, 'rb') as f:
                encoded = base64.standard_b64encode(f.read()).decode('utf-8')

            os.remove(temp_path)
            return encoded, "image/jpeg"

        else:
            # No Pillow — just encode as-is
            with open(file_path, 'rb') as f:
                encoded = base64.standard_b64encode(f.read()).decode('utf-8')

            ext = get_file_extension(file_path)
            mime = "image/png" if ext == 'png' else "image/jpeg"
            return encoded, mime

    except Exception as e:
        return None, f"Error processing image: {str(e)}"


def process_uploaded_file(file_path, filename):
    """
    Main function — automatically detect file type and process it.
    
    Returns:
    - (file_content, None, None) for text-based files
    - (None, image_data, image_type) for image files
    - (error_message, None, None) on error
    """
    ext = get_file_extension(filename)

    if ext == 'pdf':
        content = extract_pdf_text(file_path)
        return content, None, None

    elif ext == 'docx':
        content = extract_docx_text(file_path)
        return content, None, None

    elif ext in ('txt', 'cfg'):
        content = extract_config_text(file_path)
        return content, None, None

    elif ext in ('png', 'jpg', 'jpeg'):
        image_data, image_type = encode_image_to_base64(file_path)
        if image_data:
            return None, image_data, image_type
        else:
            return image_type, None, None  # image_type contains error message here

    else:
        return f"Unsupported file type: .{ext}", None, None


def save_uploaded_file(file, upload_folder):
    """
    Safely save an uploaded file.
    Returns (filepath, filename) or (None, error_message)
    """
    if not file or not file.filename:
        return None, "No file provided"

    filename = secure_filename(file.filename)

    if not allowed_file(filename):
        ext = get_file_extension(filename)
        return None, f"File type '.{ext}' not allowed. Allowed: PDF, PNG, JPG, TXT, CFG, DOCX"

    # Create upload folder if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)

    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    # Check file size after saving
    if os.path.getsize(filepath) > MAX_FILE_SIZE:
        os.remove(filepath)
        return None, "File too large. Maximum size is 10MB"

    return filepath, filename


def cleanup_file(filepath):
    """Delete file after processing (save storage space)"""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass  # Silent fail — not critical
