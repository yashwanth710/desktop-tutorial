import re
import logging
from pathlib import Path
import base64
import io
import json
from openai import AzureOpenAI
from utils.settings import settings

# ------------------------
# Logger Setup
# ------------------------
def setup_logger():
    """
    Basic logging setup. Call once at app start.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


# ------------------------
# Markdown Cleaning
# ------------------------
def clean_markdown_to_html(text: str) -> str:
    """
    Convert simple markdown to HTML (bold and italics).
    ReportLab's Paragraph supports <b> and <i>.
    """
    if not isinstance(text, str):
        return text
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)  # Bold
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)      # Italics
    return text


# ------------------------
# Template Management
# ------------------------
TEMPLATES_DIR = Path("templates")

def get_available_templates():
    """
    Return dict of template_name -> Path for all .png files in templates/.
    """
    if not TEMPLATES_DIR.exists():
        TEMPLATES_DIR.mkdir(exist_ok=True)
        return {}
    templates = {}
    for template_file in TEMPLATES_DIR.glob("*.png"):
        templates[template_file.stem.lower()] = template_file
    return templates

# def detect_template_request(query: str):
#     """
#     Detect if query contains any template name (substring match).
#     Returns template_name or None.
#     """
#     if not isinstance(query, str):
#         return None
#     query_lower = query.lower()
#     templates = get_available_templates()
#     for template_name in templates.keys():
#         if template_name in query_lower:
#             return template_name
#     return None

def agentic_template_selector(query: str) -> str:
    """
    Use LLM function-calling to decide the most relevant template
    instead of substring matching.
    """
    client = AzureOpenAI(
        api_key=settings.azure_openai_key,
        api_version=settings.llm_api_version,
        azure_endpoint=settings.azure_endpoint
        )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "select_template",
                "description": "Choose the most relevant template for the user query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "template_name": {
                            "type": "string",
                            "enum": ["transformer", "cable", "switchgear", "gis", "none"],
                            "description": "Best matching template or 'none'"
                        }
                    },
                    "required": ["template_name"]
                },
            },
        }
    ]

    response = client.chat.completions.create(
        model= settings.deployment_name,
        messages=[
            {"role": "system", "content": "You are a proposal assistant. Pick the correct template if query relates to transformers, cables, switches, or GIS."},
            {"role": "user", "content": query},
        ],
        tools=tools,
        tool_choice="auto"
    )

    if response.choices[0].message.tool_calls:
        args = response.choices[0].message.tool_calls[0].function.arguments
        return json.loads(args).get("template_name", "none")

    return "none"


def append_template_context(query: str, template_name: str) -> str:
    """
    Append a short instruction to the prompt so RAG/LLM knows to include template specifics.
    """
    if not template_name:
        return query
    template_context = (
        f"\n\n[Template Request: Please provide information relevant to {template_name} template "
        f"and include the corresponding template image in your response.]"
    )
    return (query or "") + template_context

# def append_template_context(query: str, template_name: str) -> str:
#     if not template_name:
#         return query or ""

#     template_context = (
#         f"[Template Request: Please provide information relevant to {template_name} template "
#         f"and include the corresponding template image in your response.]"
#     )

#     # if query already mentions "with the X template" → replace
#     if f"with the {template_name}" in (query or "").lower():
#         return template_context

#     return (query or "") + "\n\n" + template_context


def insert_template(response_text: str, template_name: str, width: int = 400) -> str:
    """
    Embed template as base64 <img> appended to HTML response_text.
    Returns HTML string safe to render with unsafe_allow_html=True.
    """
    templates = get_available_templates()
    if not template_name or template_name not in templates:
        return response_text or ""
    template_path = templates[template_name]
    try:
        with open(template_path, "rb") as img_file:
            encoded_img = base64.b64encode(img_file.read()).decode("utf-8")
        img_tag = f'<br><br><img src="data:image/png;base64,{encoded_img}" alt="{template_name} template" width="{width}"/>'
        return (response_text or "") + img_tag
    except Exception:
        return response_text or ""


# ------------------------
# PDF Generation Helpers
# ------------------------
def create_enhanced_pdf(draft_text: str, used_templates: list):
    """
    Create an enhanced PDF (templates on first page(s), proposal text on following pages).
    Returns io.BytesIO.
    Raises ImportError if reportlab or pillow are missing.
    """
    # Lazy imports (so module import doesn't fail if packages missing)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.lib.units import inch
        from PIL import Image as PILImage
    except Exception as e:
        raise ImportError("reportlab and pillow are required for enhanced PDF generation.") from e

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=1 * inch, bottomMargin=1 * inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor='black'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor='black'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_LEFT,
        textColor='black'
    )

    story = []

    # Page 1: Templates only (each template scaled to fit)
    templates_dict = get_available_templates()
    if used_templates:
        for template_name in used_templates:
            template_path = templates_dict.get(template_name)
            if template_path and template_path.exists():
                try:
                    img = PILImage.open(template_path)
                    img_width, img_height = img.size

                    max_width = 6 * inch
                    scale_factor = min(max_width / img_width, 1.0)
                    new_width = img_width * scale_factor
                    new_height = img_height * scale_factor

                    rl_img = RLImage(str(template_path), width=new_width, height=new_height)
                    story.append(rl_img)
                    story.append(Spacer(1, 20))
                except Exception as e:
                    story.append(Paragraph(f"Error loading template {template_name}: {str(e)}", body_style))
        story.append(PageBreak())

    # Page 2+: Proposal content
    paragraphs = (draft_text or "").split('\n\n')
    for para in paragraphs:
        if para.strip():
            clean_para = clean_markdown_to_html(para.strip())
            story.append(Paragraph(clean_para, body_style))
            story.append(Spacer(1, 6))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def create_basic_pdf(draft_text: str):
    """
    Create a basic text-only PDF fallback (uses reportlab.canvas).
    Returns io.BytesIO.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception as e:
        raise ImportError("reportlab is required for basic PDF generation.") from e

    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "RUGGED MONITORING - PROPOSAL")

    # Body
    c.setFont("Helvetica", 10)
    y_position = height - 80
    lines = (draft_text or "").split("\n")
    for line in lines:
        if y_position < 50:  # new page
            c.showPage()
            y_position = height - 50
            c.setFont("Helvetica", 10)
        # Wrap long lines roughly (80 chars)
        for i in range(0, len(line), 90):
            chunk = line[i:i+90]
            c.drawString(50, y_position, chunk)
            y_position -= 14
            if y_position < 50:
                c.showPage()
                y_position = height - 50
                c.setFont("Helvetica", 10)

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer
