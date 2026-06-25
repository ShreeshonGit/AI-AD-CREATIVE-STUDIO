import os
import requests
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
import html
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def clean_for_pdf(text) -> str:
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
    escaped = html.escape(text)
    escaped = escaped.replace("\r\n", "<br/>").replace("\n", "<br/>")
    return escaped

def build_pdf_export(detail):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'PDFTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'PDFH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'PDFH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0f766e'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'PDFBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )
    
    body_bold_style = ParagraphStyle(
        'PDFBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    bullet_style = ParagraphStyle(
        'PDFBullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    story = []
    
    prod_name = detail.get("product_name", "Campaign")
    story.append(Paragraph(clean_for_pdf(f"Campaign Brief & Creative Assets: {prod_name}"), title_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Campaign Information", h1_style))
    story.append(Paragraph(f"<b>Product:</b> {clean_for_pdf(detail.get('product_name', 'N/A'))}", body_style))
    story.append(Paragraph(f"<b>Category:</b> {clean_for_pdf(detail.get('category', 'N/A'))}", body_style))
    story.append(Paragraph(f"<b>Objective:</b> {clean_for_pdf(detail.get('campaign_objective', 'N/A'))}", body_style))
    story.append(Paragraph(f"<b>Audience:</b> {clean_for_pdf(detail.get('audience', 'N/A') or 'Inferred from context')}", body_style))
    story.append(Paragraph(f"<b>Offer / Hook Angle:</b> {clean_for_pdf(detail.get('offer_angle', 'N/A'))}", body_style))
    story.append(Paragraph(f"<b>Brand Voice:</b> {clean_for_pdf(detail.get('brand_voice', 'N/A'))}", body_style))
    story.append(Paragraph(f"<b>Target Platform:</b> {clean_for_pdf(detail.get('platform', 'N/A'))}", body_style))
    story.append(Spacer(1, 15))
    
    adset_creatives = detail.get("adset_creatives")
    if adset_creatives:
        for idx, ac in enumerate(adset_creatives, 1):
            story.append(PageBreak())
            story.append(Paragraph(f"Ad Set {idx}", h1_style))
            story.append(Paragraph(f"<b>Location:</b> {clean_for_pdf(ac.get('location', 'N/A'))}", body_style))
            story.append(Paragraph(f"<b>Age Group:</b> {clean_for_pdf(ac.get('age_group', 'N/A'))}", body_style))
            
            targeting = ac.get("detailed_targeting", [])
            targeting_str = ', '.join(targeting) if targeting else 'N/A'
            story.append(Paragraph(f"<b>Detailed Targeting:</b> {clean_for_pdf(targeting_str)}", body_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("Hooks:", h2_style))
            for h_idx, hook in enumerate(ac.get("hooks", []), 1):
                story.append(Paragraph(f"{h_idx}. {clean_for_pdf(hook)}", bullet_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("Headlines:", h2_style))
            for hl_idx, headline in enumerate(ac.get("headlines", []), 1):
                story.append(Paragraph(f"{hl_idx}. {clean_for_pdf(headline)}", bullet_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("Primary Texts (Body Copy):", h2_style))
            for pt_idx, pt in enumerate(ac.get("primary_texts", []), 1):
                story.append(Paragraph(f"<b>Option {pt_idx}:</b><br/>{clean_for_pdf(pt)}", body_style))
                story.append(Spacer(1, 5))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("CTAs:", h2_style))
            ctas = ac.get("ctas", [])
            story.append(Paragraph(clean_for_pdf("  •  ".join(ctas)) if ctas else "N/A", body_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("Video Script:", h2_style))
            v_script = ac.get("video_script")
            if v_script:
                if isinstance(v_script, str):
                    story.append(Paragraph(clean_for_pdf(v_script), body_style))
                else:
                    story.append(Paragraph(f"<b>Opening Hook (0-5s):</b> {clean_for_pdf(v_script.get('hook', 'N/A'))}", body_style))
                    for s_idx, scene in enumerate(v_script.get('scenes', []), 1):
                        story.append(Paragraph(f"<b>Scene {s_idx:02d}:</b>", body_bold_style))
                        story.append(Paragraph(f"Visual: {clean_for_pdf(scene.get('scene', 'N/A'))}", body_style))
                        story.append(Paragraph(f"Voiceover: {clean_for_pdf(scene.get('voiceover', 'N/A'))}", body_style))
                    story.append(Paragraph(f"<b>Closing CTA (25-30s):</b> {clean_for_pdf(v_script.get('cta', 'N/A'))}", body_style))
            else:
                story.append(Paragraph("Video script not requested.", body_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("Compliance Results:", h2_style))
            comp = ac.get("compliance_report")
            if comp:
                comp_status = comp.get("status", "safe").upper()
                story.append(Paragraph(f"<b>Compliance Status:</b> {clean_for_pdf(comp_status)}", body_style))
                issues = comp.get("issues", [])
                if issues:
                    for i_idx, issue in enumerate(issues, 1):
                        story.append(Paragraph(f"• <b>Issue {i_idx}:</b> [{clean_for_pdf(issue.get('type'))}] {clean_for_pdf(issue.get('text'))}<br/><i>Suggestion:</i> {clean_for_pdf(issue.get('suggestion'))}", body_style))
                else:
                    story.append(Paragraph("No compliance policy violations detected.", body_style))
            else:
                story.append(Paragraph("Compliance report not available.", body_style))
                
    else:
        story.append(Spacer(1, 10))
        
        story.append(Paragraph("Hooks:", h1_style))
        for h_idx, hook in enumerate(detail.get("hooks", []), 1):
            story.append(Paragraph(f"{h_idx}. {clean_for_pdf(hook)}", bullet_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("Headlines:", h1_style))
        for hl_idx, headline in enumerate(detail.get("headlines", []), 1):
            story.append(Paragraph(f"{hl_idx}. {clean_for_pdf(headline)}", bullet_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("Primary Texts (Body Copy):", h1_style))
        for pt_idx, pt in enumerate(detail.get("primary_texts", []), 1):
            story.append(Paragraph(f"<b>Option {pt_idx}:</b><br/>{clean_for_pdf(pt)}", body_style))
            story.append(Spacer(1, 5))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("CTAs:", h1_style))
        ctas = detail.get("ctas", [])
        story.append(Paragraph(clean_for_pdf("  •  ".join(ctas)) if ctas else "N/A", body_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("Video Script:", h1_style))
        v_script = detail.get("video_script")
        if v_script:
            if isinstance(v_script, str):
                story.append(Paragraph(clean_for_pdf(v_script), body_style))
            else:
                story.append(Paragraph(f"<b>Opening Hook (0-5s):</b> {clean_for_pdf(v_script.get('hook', 'N/A'))}", body_style))
                for s_idx, scene in enumerate(v_script.get('scenes', []), 1):
                    story.append(Paragraph(f"<b>Scene {s_idx:02d}:</b>", body_bold_style))
                    story.append(Paragraph(f"Visual: {clean_for_pdf(scene.get('scene', 'N/A'))}", body_style))
                    story.append(Paragraph(f"Voiceover: {clean_for_pdf(scene.get('voiceover', 'N/A'))}", body_style))
                story.append(Paragraph(f"<b>Closing CTA (25-30s):</b> {clean_for_pdf(v_script.get('cta', 'N/A'))}", body_style))
        else:
            story.append(Paragraph("Video script not requested.", body_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("Compliance Results:", h1_style))
        comp_status = detail.get("compliance_status", "safe").upper()
        story.append(Paragraph(f"<b>Compliance Status:</b> {clean_for_pdf(comp_status)}", body_style))
        issues = detail.get("compliance_issues", [])
        if issues:
            for i_idx, issue in enumerate(issues, 1):
                if hasattr(issue, 'dict'):
                    issue_dict = issue.dict()
                elif isinstance(issue, dict):
                    issue_dict = issue
                else:
                    issue_dict = {}
                story.append(Paragraph(f"• <b>Issue {i_idx}:</b> [{clean_for_pdf(issue_dict.get('type'))}] {clean_for_pdf(issue_dict.get('text'))}<br/><i>Suggestion:</i> {clean_for_pdf(issue_dict.get('suggestion'))}", body_style))
        else:
            story.append(Paragraph("No compliance policy violations detected.", body_style))

    doc.build(story)
    pdf_val = buffer.getvalue()
    buffer.close()
    return pdf_val

def build_txt_export(detail):
    lines = []
    lines.append("Campaign Information")
    lines.append("")
    lines.append(f"Product: {detail.get('product_name', 'N/A')}")
    lines.append(f"Category: {detail.get('category', 'N/A')}")
    lines.append(f"Objective: {detail.get('campaign_objective', 'N/A')}")
    lines.append(f"Audience: {detail.get('audience', 'N/A') or 'Inferred from context'}")
    lines.append("")
    
    adset_creatives = detail.get("adset_creatives")
    if adset_creatives:
        for idx, ac in enumerate(adset_creatives, 1):
            lines.append("---")
            lines.append("")
            lines.append(f"Ad Set {idx}")
            lines.append("")
            lines.append(f"Location: {ac.get('location', 'N/A')}")
            lines.append(f"Age Group: {ac.get('age_group', 'N/A')}")
            targeting = ac.get("detailed_targeting", [])
            lines.append(f"Detailed Targeting: {', '.join(targeting) if targeting else 'N/A'}")
            lines.append("")
            
            lines.append("Hooks:")
            for h_idx, hook in enumerate(ac.get("hooks", []), 1):
                lines.append(f"  {h_idx}. {hook}")
            lines.append("")
            
            lines.append("Headlines:")
            for hl_idx, headline in enumerate(ac.get("headlines", []), 1):
                lines.append(f"  {hl_idx}. {headline}")
            lines.append("")
            
            lines.append("Primary Texts:")
            for pt_idx, pt in enumerate(ac.get("primary_texts", []), 1):
                lines.append(f"  {pt_idx}. {pt}")
            lines.append("")
            
            lines.append("CTAs:")
            ctas = ac.get("ctas", [])
            lines.append(f"  {', '.join(ctas) if ctas else 'N/A'}")
            lines.append("")
            
            v_script = ac.get("video_script")
            if v_script:
                lines.append("Video Script:")
                if isinstance(v_script, str):
                    lines.append(v_script)
                else:
                    lines.append(f"  Opening Hook: {v_script.get('hook', 'N/A')}")
                    for s_idx, scene in enumerate(v_script.get('scenes', []), 1):
                        lines.append(f"  Scene {s_idx:02d}:")
                        lines.append(f"    Visual: {scene.get('scene', 'N/A')}")
                        lines.append(f"    Voiceover: {scene.get('voiceover', 'N/A')}")
                    lines.append(f"  Closing CTA: {v_script.get('cta', 'N/A')}")
            else:
                lines.append("Video Script:\nVideo script not requested.")
            lines.append("")
    else:
        # Fallback to single creative package
        lines.append("---")
        lines.append("")
        lines.append("Ad Set 1")
        lines.append("")
        lines.append("Location: General/Global")
        lines.append("Age Group: All ages")
        lines.append("Detailed Targeting: Broad")
        lines.append("")
        
        lines.append("Hooks:")
        for h_idx, hook in enumerate(detail.get("hooks", []), 1):
            lines.append(f"  {h_idx}. {hook}")
        lines.append("")
        
        lines.append("Headlines:")
        for hl_idx, headline in enumerate(detail.get("headlines", []), 1):
            lines.append(f"  {hl_idx}. {headline}")
        lines.append("")
        
        lines.append("Primary Texts:")
        for pt_idx, pt in enumerate(detail.get("primary_texts", []), 1):
            lines.append(f"  {pt_idx}. {pt}")
        lines.append("")
        
        lines.append("CTAs:")
        ctas = detail.get("ctas", [])
        lines.append(f"  {', '.join(ctas) if ctas else 'N/A'}")
        lines.append("")
        
        v_script = detail.get("video_script")
        if v_script:
            lines.append("Video Script:")
            lines.append(v_script)
        else:
            lines.append("Video Script:\nVideo script not requested.")
        lines.append("")
        
    return "\n".join(lines)

def build_md_export(detail):
    lines = []
    lines.append("# Campaign")
    lines.append("")
    lines.append("## Campaign Information")
    lines.append("")
    lines.append(f"Product: {detail.get('product_name', 'N/A')}")
    lines.append(f"Category: {detail.get('category', 'N/A')}")
    lines.append(f"Objective: {detail.get('campaign_objective', 'N/A')}")
    lines.append(f"Audience: {detail.get('audience', 'N/A') or 'Inferred from context'}")
    lines.append("")
    
    adset_creatives = detail.get("adset_creatives")
    if adset_creatives:
        for idx, ac in enumerate(adset_creatives, 1):
            lines.append(f"## Ad Set {idx}")
            lines.append("")
            lines.append(f"Location: {ac.get('location', 'N/A')}")
            lines.append(f"Age Group: {ac.get('age_group', 'N/A')}")
            targeting = ac.get("detailed_targeting", [])
            lines.append(f"Detailed Targeting: {', '.join(targeting) if targeting else 'N/A'}")
            lines.append("")
            
            lines.append("Hooks:")
            for h_idx, hook in enumerate(ac.get("hooks", []), 1):
                lines.append(f"{h_idx}. {hook}")
            lines.append("")
            
            lines.append("Headlines:")
            for hl_idx, headline in enumerate(ac.get("headlines", []), 1):
                lines.append(f"{hl_idx}. {headline}")
            lines.append("")
            
            lines.append("Primary Texts:")
            for pt_idx, pt in enumerate(ac.get("primary_texts", []), 1):
                lines.append(f"{pt_idx}. {pt}")
            lines.append("")
            
            lines.append("CTAs:")
            ctas = ac.get("ctas", [])
            lines.append(f"- {', '.join(ctas) if ctas else 'N/A'}")
            lines.append("")
            
            lines.append("## Video Script")
            lines.append("")
            v_script = ac.get("video_script")
            if v_script:
                if isinstance(v_script, str):
                    lines.append(f"```\n{v_script}\n```")
                else:
                    lines.append(f"- **Opening Hook:** {v_script.get('hook', 'N/A')}")
                    for s_idx, scene in enumerate(v_script.get('scenes', []), 1):
                        lines.append(f"- **Scene {s_idx:02d}:**")
                        lines.append(f"  - **Visual:** {scene.get('scene', 'N/A')}")
                        lines.append(f"  - **Voiceover:** {scene.get('voiceover', 'N/A')}")
                    lines.append(f"- **Closing CTA:** {v_script.get('cta', 'N/A')}")
            else:
                lines.append("Video script not requested.")
            lines.append("")
    else:
        # Fallback to single creative package
        lines.append("## Ad Set 1")
        lines.append("")
        lines.append("Location: General/Global")
        lines.append("Age Group: All ages")
        lines.append("Detailed Targeting: Broad")
        lines.append("")
        
        lines.append("Hooks:")
        for h_idx, hook in enumerate(detail.get("hooks", []), 1):
            lines.append(f"{h_idx}. {hook}")
        lines.append("")
        
        lines.append("Headlines:")
        for hl_idx, headline in enumerate(detail.get("headlines", []), 1):
            lines.append(f"{hl_idx}. {headline}")
        lines.append("")
        
        lines.append("Primary Texts:")
        for pt_idx, pt in enumerate(detail.get("primary_texts", []), 1):
            lines.append(f"{pt_idx}. {pt}")
        lines.append("")
        
        lines.append("CTAs:")
        ctas = detail.get("ctas", [])
        lines.append(f"- {', '.join(ctas) if ctas else 'N/A'}")
        lines.append("")
        
        lines.append("## Video Script")
        lines.append("")
        v_script = detail.get("video_script")
        if v_script:
            lines.append(f"```\n{v_script}\n```")
        else:
            lines.append("Video script not requested.")
        lines.append("")
        
    return "\n".join(lines)

# Load env variables with overrides enabled
load_dotenv(override=True)

# Set premium page layout natively in Streamlit
st.set_page_config(
    page_title="AI Ad Creative Studio Pro",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_theme(theme: str):
    if "Dark" in theme:
        st.markdown(
            """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

            html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], h1, h2, h3, h4, h5, h6, p, label, input, textarea, select {
                font-family: 'Outfit', sans-serif !important;
            }
            button[data-testid="baseButton-secondary"], button[data-testid="baseButton-primary"], .copy-card-btn, .stDownloadButton button {
                font-family: 'Outfit', sans-serif !important;
            }

            /* Exclude code elements from global Outfit font override */
            code, pre, code *, pre *, [data-testid="stCodeBlock"] * {
                font-family: 'Courier New', Courier, monospace !important;
            }

            /* Background gradient */
            .stApp {
                background: linear-gradient(135deg, #030712 0%, #080f1e 50%, #020617 100%) !important;
                color: #f8fafc !important;
            }

            header[data-testid="stHeader"] {
                background: transparent !important;
            }

            /* Sidebar background */
            [data-testid="stSidebar"] {
                background-color: #0b0f19 !important;
                border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
            }

            /* Sidebar Logo Styling */
            .logo-container {
                padding: 10px 0 20px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                margin-bottom: 20px;
            }
            .logo-title {
                font-size: 24px !important;
                font-weight: 700 !important;
                background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: -0.5px;
            }
            .logo-subtitle {
                font-size: 12px !important;
                color: #94a3b8 !important;
                font-weight: 400 !important;
                margin-top: 4px;
            }

            /* Sidebar segment style Theme Switcher */
            div[data-testid="stSegmentedControl"] {
                background-color: rgba(15, 23, 42, 0.6) !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-radius: 12px !important;
                padding: 2px !important;
            }
            div[data-testid="stSegmentedControl"] button {
                border: none !important;
                border-radius: 8px !important;
                color: #94a3b8 !important;
                background-color: transparent !important;
                transition: all 0.2s ease !important;
            }
            div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
                background-color: #6366f1 !important;
                color: #ffffff !important;
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
            }

            /* Input configuration Cards (Left Column) & Output Cards (Right Column) */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: rgba(15, 23, 42, 0.4) !important;
                backdrop-filter: blur(16px) !important;
                -webkit-backdrop-filter: blur(16px) !important;
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
                border-radius: 16px !important;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
                padding: 24px !important;
                margin-bottom: 20px !important;
                transition: all 0.3s ease !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"]:hover {
                box-shadow: 0 10px 40px 0 rgba(99, 102, 241, 0.08), inset 0 0 12px rgba(99, 102, 241, 0.04) !important;
                border-color: rgba(99, 102, 241, 0.2) !important;
            }

            /* Typography Hierarchy */
            h1 {
                font-size: 32px !important;
                font-weight: 700 !important;
                letter-spacing: -0.5px !important;
                margin-bottom: 8px !important;
                color: #f8fafc !important;
            }
            h2 {
                font-size: 24px !important;
                font-weight: 600 !important;
                letter-spacing: -0.3px !important;
                margin-top: 20px !important;
                margin-bottom: 12px !important;
                color: #f8fafc !important;
            }
            h3 {
                font-size: 18px !important;
                font-weight: 600 !important;
                margin-top: 15px !important;
                margin-bottom: 10px !important;
                color: #f8fafc !important;
            }
            .stMarkdown, .stMarkdown p {
                color: #e2e8f0 !important;
            }

            /* Labels */
            div[data-testid="stWidgetLabel"] p, label p {
                font-size: 13.5px !important;
                font-weight: 500 !important;
                color: #cbd5e1 !important;
            }

            /* Inputs, Textareas, Selectboxes */
            input, textarea, div[data-baseweb="input"], div[data-baseweb="textarea"], .stTextArea textarea, .stTextInput input, .stNumberInput input {
                background-color: rgba(15, 23, 42, 0.6) !important;
                color: #f8fafc !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 10px !important;
                transition: all 0.2s ease !important;
            }
            input:focus, textarea:focus, div[data-baseweb="input"]:focus-within {
                border-color: #6366f1 !important;
                box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
            }

            /* Selectbox components & Dropdown Option List styling following active theme */
            div[data-baseweb="select"] {
                background-color: rgba(15, 23, 42, 0.6) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 10px !important;
            }
            div[data-baseweb="select"] > div {
                background-color: transparent !important;
                color: #f8fafc !important;
            }
            div[data-baseweb="select"] * {
                color: inherit !important;
            }
            div[data-baseweb="popover"], ul[role="listbox"] {
                background-color: #0f172a !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 10px !important;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5) !important;
            }
            div[data-baseweb="popover"] ul {
                background-color: #0f172a !important;
            }
            div[role="option"], li[role="option"], [data-baseweb="popover"] [role="option"] {
                background-color: #0f172a !important;
                color: #f8fafc !important;
                padding: 10px 16px !important;
                transition: background-color 0.2s ease, color 0.2s ease !important;
            }
            div[role="option"]:hover, li[role="option"]:hover, [data-baseweb="popover"] [role="option"]:hover {
                background-color: #6366f1 !important;
                color: #ffffff !important;
            }
            div[role="option"][aria-selected="true"], li[role="option"][aria-selected="true"] {
                background-color: #4f46e5 !important;
                color: #ffffff !important;
            }

            /* Sidebar History Card Styling & Custom Action Buttons */
            [data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {
                background: rgba(30, 41, 59, 0.45) !important;
                border: 1px solid rgba(255, 255, 255, 0.06) !important;
                border-radius: 14px !important;
                padding: 16px !important;
                margin-bottom: 12px !important;
                box-shadow: none !important;
            }
            [data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"]:hover {
                border-color: rgba(99, 102, 241, 0.25) !important;
                background: rgba(30, 41, 59, 0.6) !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
            }
            [data-testid="stSidebar"] div[data-testid="column"]:nth-of-type(1) button {
                background-color: rgba(99, 102, 241, 0.08) !important;
                color: #a5b4fc !important;
                border: 1px solid rgba(99, 102, 241, 0.2) !important;
                border-radius: 8px !important;
            }
            [data-testid="stSidebar"] div[data-testid="column"]:nth-of-type(1) button:hover {
                background-color: #6366f1 !important;
                color: #ffffff !important;
                border-color: #6366f1 !important;
                box-shadow: 0 0 10px rgba(99, 102, 241, 0.4) !important;
            }
            [data-testid="stSidebar"] div[data-testid="column"]:nth-of-type(2) button {
                background-color: rgba(239, 68, 68, 0.08) !important;
                color: #fca5a5 !important;
                border: 1px solid rgba(239, 68, 68, 0.2) !important;
                border-radius: 8px !important;
            }
            [data-testid="stSidebar"] div[data-testid="column"]:nth-of-type(2) button:hover {
                background-color: #ef4444 !important;
                color: #ffffff !important;
                border-color: #ef4444 !important;
                box-shadow: 0 0 10px rgba(239, 68, 68, 0.4) !important;
            }

            /* Buttons inside main block & secondary actions */
            button[data-testid="baseButton-secondary"] {
                border-radius: 8px !important;
                font-size: 13px !important;
                font-weight: 500 !important;
                background-color: rgba(30, 41, 59, 0.6) !important;
                color: #e2e8f0 !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                transition: all 0.2s ease !important;
            }
            button[data-testid="baseButton-secondary"]:hover {
                background-color: rgba(99, 102, 241, 0.15) !important;
                border-color: #6366f1 !important;
                color: #ffffff !important;
                transform: translateY(-1px);
            }

            /* Primary Button (Generate Button) with Indigo Gradient & Hover Animation */
            button[data-testid="baseButton-primary"] {
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
                color: #ffffff !important;
                border: none !important;
                border-radius: 10px !important;
                font-weight: 600 !important;
                padding: 12px 24px !important;
                box-shadow: 0 4px 15px rgba(79, 70, 229, 0.25) !important;
                transition: all 0.2s ease-in-out !important;
            }
            button[data-testid="baseButton-primary"]:hover {
                background: linear-gradient(135deg, #818cf8 0%, #6366f1 100%) !important;
                box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35) !important;
                transform: translateY(-1px) !important;
            }

            /* Success Message Card (Custom Success Alert Style) */
            .success-card {
                background: rgba(16, 185, 129, 0.08) !important;
                border: 1px solid rgba(16, 185, 129, 0.25) !important;
                border-radius: 14px !important;
                padding: 16px 20px !important;
                display: flex !important;
                align-items: center !important;
                gap: 16px !important;
                margin-bottom: 24px !important;
                box-shadow: 0 4px 15px rgba(16, 185, 129, 0.05) !important;
            }
            .success-icon {
                font-size: 24px !important;
            }
            .success-content {
                display: flex !important;
                flex-direction: column !important;
            }
            .success-title {
                font-size: 16px !important;
                font-weight: 600 !important;
                color: #34d399 !important;
            }
            .success-subtitle {
                font-size: 13px !important;
                color: #94a3b8 !important;
                margin-top: 2px !important;
            }

            /* Download Buttons Positioning / Gradients */
            div[data-testid="column"]:nth-of-type(1) div.stDownloadButton > button {
                background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
                color: #ffffff !important;
                border: none !important;
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2) !important;
            }
            div[data-testid="column"]:nth-of-type(1) div.stDownloadButton > button:hover {
                background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%) !important;
                box-shadow: 0 6px 16px rgba(59, 130, 246, 0.3) !important;
                transform: translateY(-1px) !important;
            }
            div[data-testid="column"]:nth-of-type(2) div.stDownloadButton > button {
                background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%) !important;
                color: #ffffff !important;
                border: none !important;
                box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2) !important;
            }
            div[data-testid="column"]:nth-of-type(2) div.stDownloadButton > button:hover {
                background: linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%) !important;
                box-shadow: 0 6px 16px rgba(139, 92, 246, 0.3) !important;
                transform: translateY(-1px) !important;
            }
            div[data-testid="column"]:nth-of-type(3) div.stDownloadButton > button {
                background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
                color: #ffffff !important;
                border: none !important;
                box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2) !important;
            }
            div[data-testid="column"]:nth-of-type(3) div.stDownloadButton > button:hover {
                background: linear-gradient(135deg, #f87171 0%, #dc2626 100%) !important;
                box-shadow: 0 6px 16px rgba(239, 68, 68, 0.3) !important;
                transform: translateY(-1px) !important;
            }

            /* Ad Set Information Cards/Badges */
            .adset-info-grid {
                display: grid !important;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)) !important;
                gap: 12px !important;
                margin: 15px 0 20px 0 !important;
            }
            .info-card {
                background: rgba(30, 41, 59, 0.5) !important;
                border: 1px solid rgba(255, 255, 255, 0.06) !important;
                border-radius: 12px !important;
                padding: 12px 16px !important;
            }
            .info-card.wide {
                grid-column: span 1 !important;
            }
            @media (min-width: 600px) {
                .info-card.wide {
                    grid-column: span 2 !important;
                }
            }
            .info-label {
                font-size: 11px !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
                color: #94a3b8 !important;
                font-weight: 600 !important;
            }
            .info-value {
                font-size: 14px !important;
                font-weight: 500 !important;
                color: #f8fafc !important;
                margin-top: 4px !important;
            }
            .info-value-badges {
                display: flex !important;
                flex-wrap: wrap !important;
                gap: 6px !important;
                margin-top: 6px !important;
            }
            .badge {
                background: rgba(99, 102, 241, 0.15) !important;
                color: #a5b4fc !important;
                border: 1px solid rgba(99, 102, 241, 0.25) !important;
                border-radius: 6px !important;
                padding: 2px 8px !important;
                font-size: 12px !important;
                font-weight: 500 !important;
            }

            /* Copy card */
            .copy-card {
                background: rgba(30, 41, 59, 0.35) !important;
                border: 1px solid rgba(255, 255, 255, 0.06) !important;
                border-radius: 12px !important;
                padding: 16px !important;
                margin-bottom: 12px !important;
                transition: all 0.2s ease !important;
            }
            .copy-card:hover {
                border-color: rgba(99, 102, 241, 0.2) !important;
            }
            .copy-card-header {
                display: flex !important;
                justify-content: space-between !important;
                align-items: center !important;
                margin-bottom: 10px !important;
            }
            .copy-card-title {
                font-size: 12px !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
                color: #818cf8 !important;
                font-weight: 600 !important;
            }
            .copy-card-btn {
                background: rgba(99, 102, 241, 0.12) !important;
                border: 1px solid rgba(99, 102, 241, 0.25) !important;
                color: #a5b4fc !important;
                padding: 3px 8px !important;
                border-radius: 6px !important;
                font-size: 11px !important;
                font-weight: 600 !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
            }
            .copy-card-btn:hover {
                background: #6366f1 !important;
                color: #ffffff !important;
                border-color: #6366f1 !important;
            }
            .copy-card-body {
                font-size: 14px !important;
                color: #e2e8f0 !important;
                line-height: 1.5 !important;
                white-space: pre-wrap !important;
            }

            /* Tabs */
            div[data-baseweb="tab-list"] {
                border-bottom: 2px solid rgba(255, 255, 255, 0.05) !important;
                gap: 8px !important;
            }
            div[data-baseweb="tab-list"] button {
                color: #94a3b8 !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                padding: 10px 16px !important;
                border-bottom: 2px solid transparent !important;
                transition: all 0.3s ease !important;
            }
            div[data-baseweb="tab-list"] button[aria-selected="true"] {
                color: #6366f1 !important;
                border-bottom: 2px solid #6366f1 !important;
                background-color: transparent !important;
            }
            div[data-baseweb="tab-list"] button:hover {
                color: #818cf8 !important;
            }
            
            /* Alert boxes */
            div[data-testid="stAlert"] {
                border-radius: 12px !important;
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
            }

            /* Mobile/Responsive styling overrides */
            @media (max-width: 768px) {
                div[data-testid="stVerticalBlockBorderWrapper"] {
                    padding: 16px !important;
                }
                h1 {
                    font-size: 26px !important;
                }
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    else:  # Light Theme
        st.markdown(
            """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

            html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], h1, h2, h3, h4, h5, h6, p, label, input, textarea, select {
                font-family: 'Outfit', sans-serif !important;
            }
            button[data-testid="baseButton-secondary"], button[data-testid="baseButton-primary"], .copy-card-btn, .stDownloadButton button {
                font-family: 'Outfit', sans-serif !important;
            }

            /* Exclude code elements from global Outfit font override */
            code, pre, code *, pre *, [data-testid="stCodeBlock"] * {
                font-family: 'Courier New', Courier, monospace !important;
            }

            /* Background gradient */
            .stApp {
                background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
                color: #0f172a !important;
            }

            header[data-testid="stHeader"] {
                background: transparent !important;
            }

            /* Sidebar background */
            [data-testid="stSidebar"] {
                background-color: #ffffff !important;
                border-right: 1px solid #e2e8f0 !important;
            }

            /* Sidebar Logo Styling */
            .logo-container {
                padding: 10px 0 20px 0;
                border-bottom: 1px solid #e2e8f0;
                margin-bottom: 20px;
            }
            .logo-title {
                font-size: 24px !important;
                font-weight: 700 !important;
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: -0.5px;
            }
            .logo-subtitle {
                font-size: 12px !important;
                color: #475569 !important;
                font-weight: 400 !important;
                margin-top: 4px;
            }

            /* Sidebar segment style Theme Switcher */
            div[data-testid="stSegmentedControl"] {
                background-color: #f1f5f9 !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 12px !important;
                padding: 2px !important;
            }
            div[data-testid="stSegmentedControl"] button {
                border: none !important;
                border-radius: 8px !important;
                color: #475569 !important;
                background-color: transparent !important;
                transition: all 0.2s ease !important;
            }
            div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
                background-color: #4f46e5 !important;
                color: #ffffff !important;
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2) !important;
            }

            /* Input configuration Cards (Left Column) & Output Cards (Right Column) */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: #ffffff !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 16px !important;
                box-shadow: 0 4px 20px 0 rgba(148, 163, 184, 0.06) !important;
                padding: 24px !important;
                margin-bottom: 20px !important;
                transition: all 0.3s ease !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"]:hover {
                box-shadow: 0 4px 20px 0 rgba(79, 70, 229, 0.08) !important;
                border-color: rgba(79, 70, 229, 0.2) !important;
            }

            /* Typography Hierarchy */
            h1 {
                font-size: 32px !important;
                font-weight: 700 !important;
                letter-spacing: -0.5px !important;
                margin-bottom: 8px !important;
                color: #0f172a !important;
            }
            h2 {
                font-size: 24px !important;
                font-weight: 600 !important;
                letter-spacing: -0.3px !important;
                margin-top: 20px !important;
                margin-bottom: 12px !important;
                color: #0f172a !important;
            }
            h3 {
                font-size: 18px !important;
                font-weight: 600 !important;
                margin-top: 15px !important;
                margin-bottom: 10px !important;
                color: #0f172a !important;
            }
            .stMarkdown, .stMarkdown p {
                color: #334155 !important;
            }

            /* Labels */
            div[data-testid="stWidgetLabel"] p, label p {
                font-size: 13.5px !important;
                font-weight: 500 !important;
                color: #475569 !important;
            }

            /* Inputs, Textareas, Selectboxes */
            input, textarea, div[data-baseweb="input"], div[data-baseweb="textarea"], .stTextArea textarea, .stTextInput input, .stNumberInput input {
                background-color: #ffffff !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 10px !important;
                transition: all 0.2s ease !important;
            }
            input:focus, textarea:focus, div[data-baseweb="input"]:focus-within {
                border-color: #4f46e5 !important;
                box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1) !important;
            }

            /* Selectbox components & Dropdown Option List styling following active theme */
            div[data-baseweb="select"] {
                background-color: #ffffff !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 10px !important;
            }
            div[data-baseweb="select"] > div {
                background-color: transparent !important;
                color: #0f172a !important;
            }
            div[data-baseweb="select"] * {
                color: inherit !important;
            }
            div[data-baseweb="popover"], ul[role="listbox"] {
                background-color: #ffffff !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 10px !important;
                box-shadow: 0 10px 25px -5px rgba(148, 163, 184, 0.1) !important;
            }
            div[data-baseweb="popover"] ul {
                background-color: #ffffff !important;
            }
            div[role="option"], li[role="option"], [data-baseweb="popover"] [role="option"] {
                background-color: #ffffff !important;
                color: #0f172a !important;
                padding: 10px 16px !important;
                transition: background-color 0.2s ease, color 0.2s ease !important;
            }
            div[role="option"]:hover, li[role="option"]:hover, [data-baseweb="popover"] [role="option"]:hover {
                background-color: #f1f5f9 !important;
                color: #0f172a !important;
            }
            div[role="option"][aria-selected="true"], li[role="option"][aria-selected="true"] {
                background-color: #4f46e5 !important;
                color: #ffffff !important;
            }

            /* Sidebar History Card Styling & Custom Action Buttons */
            [data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {
                background: #ffffff !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 14px !important;
                padding: 16px !important;
                margin-bottom: 12px !important;
                box-shadow: 0 2px 8px rgba(148, 163, 184, 0.04) !important;
            }
            [data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"]:hover {
                border-color: rgba(79, 70, 229, 0.25) !important;
                background: #f8fafc !important;
                box-shadow: 0 4px 15px rgba(148, 163, 184, 0.1) !important;
            }
            [data-testid="stSidebar"] div[data-testid="column"]:nth-of-type(1) button {
                background-color: rgba(79, 70, 229, 0.05) !important;
                color: #4f46e5 !important;
                border: 1px solid rgba(79, 70, 229, 0.15) !important;
                border-radius: 8px !important;
            }
            [data-testid="stSidebar"] div[data-testid="column"]:nth-of-type(1) button:hover {
                background-color: #4f46e5 !important;
                color: #ffffff !important;
                border-color: #4f46e5 !important;
                box-shadow: 0 2px 8px rgba(79, 70, 229, 0.2) !important;
            }
            [data-testid="stSidebar"] div[data-testid="column"]:nth-of-type(2) button {
                background-color: rgba(220, 38, 38, 0.05) !important;
                color: #dc2626 !important;
                border: 1px solid rgba(220, 38, 38, 0.15) !important;
                border-radius: 8px !important;
            }
            [data-testid="stSidebar"] div[data-testid="column"]:nth-of-type(2) button:hover {
                background-color: #dc2626 !important;
                color: #ffffff !important;
                border-color: #dc2626 !important;
                box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2) !important;
            }

            /* Buttons inside main block & secondary actions */
            button[data-testid="baseButton-secondary"] {
                border-radius: 8px !important;
                font-size: 13px !important;
                font-weight: 500 !important;
                background-color: #ffffff !important;
                color: #334155 !important;
                border: 1px solid #cbd5e1 !important;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
                transition: all 0.2s ease !important;
            }
            button[data-testid="baseButton-secondary"]:hover {
                background-color: #f1f5f9 !important;
                border-color: #94a3b8 !important;
                color: #0f172a !important;
                transform: translateY(-1px);
            }

            /* Primary Button (Generate Button) with Indigo Gradient & Hover Animation */
            button[data-testid="baseButton-primary"] {
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
                color: #ffffff !important;
                border: none !important;
                border-radius: 10px !important;
                font-weight: 600 !important;
                padding: 12px 24px !important;
                box-shadow: 0 4px 15px rgba(79, 70, 229, 0.25) !important;
                transition: all 0.2s ease-in-out !important;
            }
            button[data-testid="baseButton-primary"]:hover {
                background: linear-gradient(135deg, #818cf8 0%, #6366f1 100%) !important;
                box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35) !important;
                transform: translateY(-1px) !important;
            }

            /* Success Message Card (Custom Success Alert Style) */
            .success-card {
                background: #f0fdf4 !important;
                border: 1px solid #bbf7d0 !important;
                border-radius: 14px !important;
                padding: 16px 20px !important;
                display: flex !important;
                align-items: center !important;
                gap: 16px !important;
                margin-bottom: 24px !important;
                box-shadow: 0 4px 15px rgba(22, 163, 74, 0.04) !important;
            }
            .success-icon {
                font-size: 24px !important;
            }
            .success-content {
                display: flex !important;
                flex-direction: column !important;
            }
            .success-title {
                font-size: 16px !important;
                font-weight: 600 !important;
                color: #166534 !important;
            }
            .success-subtitle {
                font-size: 13px !important;
                color: #15803d !important;
                margin-top: 2px !important;
            }

            /* Download Buttons Positioning / Gradients */
            div[data-testid="column"]:nth-of-type(1) div.stDownloadButton > button {
                background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
                color: #ffffff !important;
                border: none !important;
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2) !important;
            }
            div[data-testid="column"]:nth-of-type(1) div.stDownloadButton > button:hover {
                background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%) !important;
                box-shadow: 0 6px 16px rgba(59, 130, 246, 0.3) !important;
                transform: translateY(-1px) !important;
            }
            div[data-testid="column"]:nth-of-type(2) div.stDownloadButton > button {
                background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%) !important;
                color: #ffffff !important;
                border: none !important;
                box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2) !important;
            }
            div[data-testid="column"]:nth-of-type(2) div.stDownloadButton > button:hover {
                background: linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%) !important;
                box-shadow: 0 6px 16px rgba(139, 92, 246, 0.3) !important;
                transform: translateY(-1px) !important;
            }
            div[data-testid="column"]:nth-of-type(3) div.stDownloadButton > button {
                background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
                color: #ffffff !important;
                border: none !important;
                box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2) !important;
            }
            div[data-testid="column"]:nth-of-type(3) div.stDownloadButton > button:hover {
                background: linear-gradient(135deg, #f87171 0%, #dc2626 100%) !important;
                box-shadow: 0 6px 16px rgba(239, 68, 68, 0.3) !important;
                transform: translateY(-1px) !important;
            }

            /* Ad Set Information Cards/Badges */
            .adset-info-grid {
                display: grid !important;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)) !important;
                gap: 12px !important;
                margin: 15px 0 20px 0 !important;
            }
            .info-card {
                background: #ffffff !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 12px !important;
                padding: 12px 16px !important;
                box-shadow: 0 2px 8px rgba(148, 163, 184, 0.03) !important;
            }
            .info-card.wide {
                grid-column: span 1 !important;
            }
            @media (min-width: 600px) {
                .info-card.wide {
                    grid-column: span 2 !important;
                }
            }
            .info-label {
                font-size: 11px !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
                color: #64748b !important;
                font-weight: 600 !important;
            }
            .info-value {
                font-size: 14px !important;
                font-weight: 500 !important;
                color: #0f172a !important;
                margin-top: 4px !important;
            }
            .info-value-badges {
                display: flex !important;
                flex-wrap: wrap !important;
                gap: 6px !important;
                margin-top: 6px !important;
            }
            .badge {
                background: rgba(79, 70, 229, 0.08) !important;
                color: #4f46e5 !important;
                border: 1px solid rgba(79, 70, 229, 0.15) !important;
                border-radius: 6px !important;
                padding: 2px 8px !important;
                font-size: 12px !important;
                font-weight: 500 !important;
            }

            /* Copy card */
            .copy-card {
                background: #ffffff !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 12px !important;
                padding: 16px !important;
                margin-bottom: 12px !important;
                transition: all 0.2s ease !important;
                box-shadow: 0 2px 8px rgba(148, 163, 184, 0.03) !important;
            }
            .copy-card:hover {
                border-color: rgba(79, 70, 229, 0.2) !important;
            }
            .copy-card-header {
                display: flex !important;
                justify-content: space-between !important;
                align-items: center !important;
                margin-bottom: 10px !important;
            }
            .copy-card-title {
                font-size: 12px !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
                color: #4f46e5 !important;
                font-weight: 600 !important;
            }
            .copy-card-btn {
                background: rgba(79, 70, 229, 0.08) !important;
                border: 1px solid rgba(79, 70, 229, 0.15) !important;
                color: #4f46e5 !important;
                padding: 3px 8px !important;
                border-radius: 6px !important;
                font-size: 11px !important;
                font-weight: 600 !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
            }
            .copy-card-btn:hover {
                background: #4f46e5 !important;
                color: #ffffff !important;
                border-color: #4f46e5 !important;
            }
            .copy-card-body {
                font-size: 14px !important;
                color: #334155 !important;
                line-height: 1.5 !important;
                white-space: pre-wrap !important;
            }

            /* Tabs */
            div[data-baseweb="tab-list"] {
                border-bottom: 2px solid rgba(148, 163, 184, 0.1) !important;
                gap: 8px !important;
            }
            div[data-baseweb="tab-list"] button {
                color: #475569 !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                padding: 10px 16px !important;
                border-bottom: 2px solid transparent !important;
                transition: all 0.3s ease !important;
            }
            div[data-baseweb="tab-list"] button[aria-selected="true"] {
                color: #4f46e5 !important;
                border-bottom: 2px solid #4f46e5 !important;
                background-color: transparent !important;
            }
            div[data-baseweb="tab-list"] button:hover {
                color: #6366f1 !important;
            }
            
            /* Alert boxes */
            div[data-testid="stAlert"] {
                border-radius: 12px !important;
                border: 1px solid rgba(148, 163, 184, 0.1) !important;
                box-shadow: 0 4px 20px rgba(148, 163, 184, 0.08) !important;
            }

            /* Mobile/Responsive styling overrides */
            @media (max-width: 768px) {
                div[data-testid="stVerticalBlockBorderWrapper"] {
                    padding: 16px !important;
                }
                h1 {
                    font-size: 26px !important;
                }
            }
            </style>
            """,
            unsafe_allow_html=True
        )

def render_copyable_card(title: str, text: str, key: str):
    escaped_text = html.escape(text)
    st.markdown(
        f"""
        <div class="copy-card">
            <div class="copy-card-header">
                <span class="copy-card-title">{title}</span>
            </div>
            <div class="copy-card-body">{escaped_text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Backend URL configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Category labels for user-friendly display
CATEGORY_DISPLAY_MAP = {
    "education": "🎓 Education & Webinars",
    "food_bussiness": "🍔 Food & Restaurant Business",
    "medical": "💊 Healthcare & Life Sciences",
    "sales_consulting": "📈 Sales & Consulting Services",
    "ecommerce": "🛍️ E-commerce & Retail",
    "finance": "💳 Financial Services & FinTech"
}

# Dynamic category discovery from backend
@st.cache_data(ttl=20)
def get_categories():
    try:
        res = requests.get(f"{BACKEND_URL}/api/v1/categories", timeout=5)
        if res.status_code == 200:
            return res.json().get("categories", [])
    except Exception:
        pass
    return ["education", "food_bussiness", "medical", "sales_consulting", "ecommerce", "finance"]

available_categories = get_categories()

# ----------------------------------------------------
# STREAMLIT STATE INITS
# ----------------------------------------------------
KEYS_DEFAULTS = {
    "product_name": "",
    "product_description": "",
    "category": "education",
    "custom_category": "",
    "brand_voice": "",
    "audience": "",
    "pain_point": "",
    "usp": "",
    "offer_angle": "",
    "campaign_objective": "Lead Generation",
    "platform": "Meta Ads (Facebook + Instagram)",
    "custom_platform": "",
    "cta": "",
    "language": "Hinglish",
    "generate_video_script": False,
    # Ad Set Toggle Foundation
    "generate_adsets": False,
    "adset_count": 1,
    "auto_generate_adsets": True,
    # Outputs Memory
    "current_hooks": None,
    "current_headlines": None,
    "current_primary_texts": None,
    "current_ctas": None,
    "current_style_note": "",
    "current_video_script": None,
    "current_compliance_report": None,
    "current_adsets": None,
    "current_adset_creatives": None,
    "manual_adsets_inputs": [{"location": "", "age_group": "", "targeting": ""} for _ in range(20)],
    "selected_theme": "Dark"
}

for key, val in KEYS_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ----------------------------------------------------
# SIDEBAR - BRANDING & LOGO
# ----------------------------------------------------
st.sidebar.markdown(
    """
    <div class="logo-container">
        <div class="logo-title">AI Ad Studio Pro</div>
        <div class="logo-subtitle">Smart. Strategic. High Impact.</div>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------------------------------
# SIDEBAR - THEME SWITCHER
# ----------------------------------------------------
theme_options = ["Light ☀️", "Dark 🌙"]
current_theme = st.session_state.get("selected_theme", "Dark 🌙")
default_idx = 1 if "Dark" in current_theme else 0

st.sidebar.markdown("**Theme**")
selected_theme = st.sidebar.segmented_control(
    "Theme Selection",
    options=theme_options,
    default=theme_options[default_idx],
    label_visibility="collapsed"
)
# Ensure selected_theme is not None
if selected_theme is None:
    selected_theme = "Dark 🌙"

st.session_state.selected_theme = selected_theme
apply_theme(selected_theme)

# ----------------------------------------------------
# SIDEBAR - CAMPAIGN HISTORY PANEL
# ----------------------------------------------------
st.sidebar.title("🗂️ Campaign History")

# Search and filter controls inside sidebar
search_query = st.sidebar.text_input("🔍 Search by product/category...", value="")

# Fetch campaigns list from backend
@st.cache_data(ttl=2)  # Cache briefly for performance and responsiveness
def fetch_campaigns_list():
    try:
        res = requests.get(f"{BACKEND_URL}/api/v1/campaigns?limit=50", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

campaigns_history = fetch_campaigns_list()

# Apply filter locally based on search_query
filtered_campaigns = []
for camp in campaigns_history:
    prod_name = camp.get("product_name", "").lower()
    cat_name = camp.get("category", "").lower()
    q = search_query.lower()
    if q in prod_name or q in cat_name:
        filtered_campaigns.append(camp)

# Explicitly sort campaigns from Newest to Oldest based on created_at
filtered_campaigns.sort(key=lambda x: x.get("created_at", ""), reverse=True)

# Display history cards
if not filtered_campaigns:
    st.sidebar.info("No campaigns generated yet.")
else:
    st.sidebar.caption(f"Showing latest {len(filtered_campaigns)} campaigns")
    
    for camp in filtered_campaigns:
        camp_id = camp.get("id")
        camp_prod = camp.get("product_name", "Unnamed Product")
        camp_cat = camp.get("category", "General")
        camp_status = camp.get("compliance_status", "safe").lower()
        camp_date = camp.get("created_at", "")
        
        # Parse friendly date representation (IST local time)
        try:
            dt = datetime.fromisoformat(camp_date)
            from zoneinfo import ZoneInfo
            if dt.tzinfo is not None:
                dt = dt.astimezone(ZoneInfo("Asia/Kolkata"))
            else:
                dt = dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            formatted_date = dt.strftime("%d %b, %H:%M IST")
        except Exception:
            formatted_date = camp_date[:16].replace("T", " ")
            
        # Status color formatting
        status_emoji = "🟢"
        if camp_status == "warning":
            status_emoji = "🟡"
        elif camp_status == "high_risk":
            status_emoji = "🔴"
            
        # Card container inside sidebar
        with st.sidebar.container(border=True):
            st.markdown(f"**{status_emoji} {camp_prod}**")
            st.caption(f"📁 {camp_cat.title()}  •  📅 {formatted_date}")
            
            # Action buttons for this history item
            btn_col1, btn_col2 = st.columns(2)
            
            with btn_col1:
                if st.button(f"👁️ Load", key=f"load_{camp_id}", use_container_width=True):
                    # Fetch details from API
                    with st.spinner("Loading details..."):
                        try:
                            detail_res = requests.get(f"{BACKEND_URL}/api/v1/campaigns/{camp_id}", timeout=5)
                            if detail_res.status_code == 200:
                                detail = detail_res.json()
                                
                                # 1. Populate form inputs
                                st.session_state.product_name = detail.get("product_name", "")
                                st.session_state.product_description = detail.get("product_description", "")
                                
                                db_cat = detail.get("category", "")
                                if db_cat in available_categories:
                                    st.session_state.category = db_cat
                                    st.session_state.custom_category = ""
                                else:
                                    st.session_state.category = "Others"
                                    st.session_state.custom_category = db_cat
                                    
                                st.session_state.brand_voice = detail.get("brand_voice", "") or ""
                                st.session_state.audience = detail.get("audience", "")
                                st.session_state.pain_point = detail.get("pain_point", "")
                                st.session_state.usp = detail.get("usp", "")
                                st.session_state.offer_angle = detail.get("offer_angle", "")
                                st.session_state.campaign_objective = detail.get("campaign_objective", "Lead Generation")
                                
                                db_platform = detail.get("platform", "")
                                if db_platform == "Meta Ads (Facebook + Instagram)":
                                    st.session_state.platform = db_platform
                                    st.session_state.custom_platform = ""
                                else:
                                    st.session_state.platform = "Others"
                                    st.session_state.custom_platform = db_platform
                                    
                                st.session_state.cta = detail.get("desired_cta", "") or detail.get("cta", "") or ""
                                st.session_state.language = detail.get("language", "Hinglish")
                                st.session_state.generate_video_script = bool(detail.get("video_script"))
                                
                                # Ad Set state loading
                                st.session_state.generate_adsets = bool(detail.get("generate_adsets", False))
                                st.session_state.adset_count = int(detail.get("adset_count", 0))
                                st.session_state.auto_generate_adsets = bool(detail.get("auto_generate_adsets", True))
                                
                                # 2. Populate outputs
                                st.session_state.current_hooks = detail.get("hooks", [])
                                st.session_state.current_headlines = detail.get("headlines", [])
                                st.session_state.current_primary_texts = detail.get("primary_texts", [])
                                st.session_state.current_ctas = detail.get("ctas", [])
                                st.session_state.current_style_note = "Loaded from history record."
                                st.session_state.current_video_script = detail.get("video_script", "")
                                
                                # Format compliance report for display
                                st.session_state.current_compliance_report = {
                                    "status": detail.get("compliance_status", "safe"),
                                    "issues": detail.get("compliance_issues", [])
                                }
                                st.session_state.current_adsets = detail.get("adsets", [])
                                st.session_state.current_adset_creatives = detail.get("adset_creatives", [])
                                
                                # Populate manual ad sets inputs from loaded campaign history if present
                                loaded_creatives = detail.get("adset_creatives") or []
                                loaded_adsets = detail.get("adsets") or []
                                manual_list = [{"location": "", "age_group": "", "targeting": ""} for _ in range(20)]
                                source_adsets = loaded_creatives if loaded_creatives else loaded_adsets
                                if source_adsets:
                                    for idx, sa in enumerate(source_adsets[:20]):
                                        targeting_list = sa.get("detailed_targeting", [])
                                        targeting_str = "\n".join(targeting_list) if isinstance(targeting_list, list) else str(targeting_list)
                                        manual_list[idx] = {
                                            "location": sa.get("location", ""),
                                            "age_group": sa.get("age_group", ""),
                                            "targeting": targeting_str
                                        }
                                st.session_state.manual_adsets_inputs = manual_list
                                
                                # Force Rerun to update input fields and tabs
                                st.rerun()
                            else:
                                st.error("Failed to load details.")
                        except Exception as e:
                            st.error(f"Error loading: {e}")
                            
            with btn_col2:
                if st.button(f"🗑️ Delete", key=f"del_{camp_id}", use_container_width=True):
                    with st.spinner("Deleting..."):
                        try:
                            del_res = requests.delete(f"{BACKEND_URL}/api/v1/campaigns/{camp_id}", timeout=5)
                            if del_res.status_code == 200:
                                # Force cache clear to load new list
                                st.cache_data.clear()
                                st.success("Deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete.")
                        except Exception as e:
                            st.error(f"Error deleting: {e}")

# ----------------------------------------------------
# MAIN APP BODY
# ----------------------------------------------------
st.title("AI Ad Creative Studio Pro")
st.caption("Next-generation dynamic ad copywriting & style synthesis. Structured Outputs & Screening Pipelines.")

# Double columns for form input vs output rendering
col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    # 4-Section Creative Brief Form
    with st.container(border=True):
        st.subheader("📦 Product & Brand")
        product_name = st.text_input(
            "Product / Brand Name",
            value=st.session_state.product_name,
            placeholder="e.g. Raaj Pharma eLearning",
            help="Specify the name of your brand or company."
        )
        st.session_state.product_name = product_name
        
        product_description = st.text_area(
            "Product / Service Description",
            value=st.session_state.product_description,
            placeholder="e.g. Practical online courses on Regulatory Affairs and GMP compliance guidelines for healthcare professionals looking to start industry careers.",
            height=90,
            help="Detail what your product does, what problems it solves, and core details."
        )
        st.session_state.product_description = product_description
        
        # Ad Reference Category selection with custom platform support
        category_options = available_categories + ["Others"]
        category_format = lambda x: CATEGORY_DISPLAY_MAP.get(x, x.replace("_", " ").title())
        
        category = st.selectbox(
            "Ad Reference Category",
            options=category_options,
            format_func=category_format,
            index=category_options.index(st.session_state.category) if st.session_state.category in category_options else 0,
            help="Loads relevant reference ads dynamically to align copywriting tone."
        )
        st.session_state.category = category
        
        custom_category = ""
        if category == "Others":
            custom_category = st.text_input(
                "Please Specify Category",
                value=st.session_state.custom_category,
                placeholder="e.g. real_estate, fitness"
            )
            st.session_state.custom_category = custom_category
            
        brand_voice = st.text_input(
            "Brand Voice Preference",
            value=st.session_state.brand_voice,
            placeholder="e.g. Professional yet highly encouraging and friendly",
            help="Direct the specific tone parameters (e.g. bold, analytical, witty)."
        )
        st.session_state.brand_voice = brand_voice

    with st.container(border=True):
        st.subheader("👥 Audience & Positioning")
        audience = st.text_input(
            "Target Audience Description",
            value=st.session_state.audience,
            placeholder="e.g. Pharma college students and industry professionals looking to get jobs",
            help="Who is the primary buyer or target persona for this ad copy?"
        )
        st.session_state.audience = audience
        
        pain_point = st.text_area(
            "Core Customer Pain Point",
            value=st.session_state.pain_point,
            placeholder="e.g. Hard to pass job interviews because university degree programs lack real-world, practical training",
            height=90,
            help="Describe what major struggle, problem, or friction your audience faces."
        )
        st.session_state.pain_point = pain_point
        
        usp = st.text_area(
            "Product USP / Key Benefit",
            value=st.session_state.usp,
            placeholder="e.g. Courses designed and led by life science experts with accreditation from Etherea University, USA",
            height=90,
            help="Highlight the unique advantage, benefit, or primary differentiator."
        )
        st.session_state.usp = usp

    with st.container(border=True):
        st.subheader("⚙️ Campaign Settings")
        offer_angle = st.text_input(
            "Offer / Hook Angle",
            value=st.session_state.offer_angle,
            placeholder="e.g. Get a free 'GMP Compliance Interview Guide' with your first course signup",
            help="What special promo, angle, hook angle, discount, or offer are we pushing?"
        )
        st.session_state.offer_angle = offer_angle
        
        campaign_objective_options = ["Lead Generation", "Brand Awareness", "Sales", "Registrations", "Webinar Signups", "App Installs", "Demo Bookings"]
        campaign_objective = st.selectbox(
            "Campaign Objective",
            options=campaign_objective_options,
            index=campaign_objective_options.index(st.session_state.campaign_objective) if st.session_state.campaign_objective in campaign_objective_options else 0,
            help="Select the goal of the ad campaign to optimize call to actions."
        )
        st.session_state.campaign_objective = campaign_objective
        
        # Target Platform selection with custom input support
        platform_options = [
            "Meta Ads (Facebook + Instagram)",
            "Others"
        ]
        platform = st.selectbox(
            "Target Platform",
            options=platform_options,
            index=platform_options.index(st.session_state.platform) if st.session_state.platform in platform_options else 0,
            help="Adapts copywriting style, density, and formatting to suit specific channels."
        )
        st.session_state.platform = platform
        
        custom_platform = ""
        if platform == "Others":
            custom_platform = st.text_input(
                "Please Specify Platform",
                value=st.session_state.custom_platform,
                placeholder="e.g. LinkedIn, TikTok"
            )
            st.session_state.custom_platform = custom_platform
            
        cta = st.text_input(
            "Custom CTA Button Label (Optional)",
            value=st.session_state.cta,
            placeholder="e.g. Learn More",
            help="Override the default button label (e.g. Book Now, Get Offer)."
        )
        st.session_state.cta = cta
        
        language_options = ["Hinglish", "English", "Hindi", "Spanish", "German"]
        language = st.selectbox(
            "Desired Copy Language",
            options=language_options,
            index=language_options.index(st.session_state.language) if st.session_state.language in language_options else 0,
            help="Choose 'Hinglish' to trigger highly popular conversational Hindi + English mix."
        )
        st.session_state.language = language

    with st.container(border=True):
        st.subheader("🎬 Video & Creative Settings")
        generate_video_script = st.checkbox(
            "Generate Video Script",
            value=st.session_state.generate_video_script,
            help="Triggers the secondary video ad copy generator, outputting visual visual guides and screenplay dialogues."
        )
        st.session_state.generate_video_script = generate_video_script

    with st.container(border=True):
        st.subheader("🎯 Meta Ad Sets")
        generate_adsets = st.checkbox(
            "Generate Ad Sets",
            value=st.session_state.generate_adsets,
            help="Enables targeted audience configuration segment generation."
        )
        st.session_state.generate_adsets = generate_adsets
        
        if generate_adsets:
            adset_count = st.number_input(
                "Number of Ad Sets",
                min_value=0,
                max_value=100,
                value=int(st.session_state.adset_count) if st.session_state.adset_count > 0 else 1,
                step=1,
                help="Enter how many ad set variations to produce (1-20)."
            )
            st.session_state.adset_count = int(adset_count)
            
            auto_generate_adsets = st.checkbox(
                "Auto Generate Ad Set Targeting",
                value=st.session_state.auto_generate_adsets,
                help="Automatically infer target locations, age brackets, and interest groups from product briefs."
            )
            st.session_state.auto_generate_adsets = auto_generate_adsets
            
            if not auto_generate_adsets:
                st.markdown("##### ✍️ Manual Ad Set Targeting Configurations")
                # Clamp to safe max input size
                render_count = min(max(0, st.session_state.adset_count), 20)
                for i in range(render_count):
                    st.markdown(f"**AD SET {i+1}**")
                    
                    # Fetch existing values from state
                    existing = st.session_state.manual_adsets_inputs[i]
                    
                    loc = st.text_input(
                        f"Location (Ad Set {i+1})",
                        value=existing["location"],
                        key=f"manual_location_{i}",
                        placeholder="e.g. Delhi NCR or US, UK"
                    )
                    
                    age = st.text_input(
                        f"Age Group (Ad Set {i+1})",
                        value=existing["age_group"],
                        key=f"manual_age_{i}",
                        placeholder="e.g. 18-25 or 25-40"
                    )
                    
                    targeting_str = st.text_area(
                        f"Detailed Targeting (Ad Set {i+1}) - One interest/behavior per line",
                        value=existing["targeting"],
                        key=f"manual_targeting_{i}",
                        placeholder="e.g.\nMBA Students\nBBA Students\nCAT Aspirants",
                        height=100
                    )
                    
                    # Store back in state
                    st.session_state.manual_adsets_inputs[i] = {
                        "location": loc,
                        "age_group": age,
                        "targeting": targeting_str
                    }
                    st.write("---")
        else:
            st.session_state.adset_count = 0

    # Submit button with type="primary" for premium styling
    generate_btn = st.button("🚀 Generate High-Converting Campaign Assets", type="primary", use_container_width=True)

with col2:
    st.subheader("⚡ Structured Ad Creative Elements")
    
    # RENDER EXPORT SECTION IF OUTPUT EXISTS IN STATE
    if st.session_state.current_hooks is not None:
        # Premium success card custom rendering
        st.markdown(
            """
            <div class="success-card">
                <div class="success-icon">✅</div>
                <div class="success-content">
                    <div class="success-title">Campaign Generated Successfully</div>
                    <div class="success-subtitle">Your ad creative package is ready.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("Download Options:")
        
        current_detail = {
            "product_name": st.session_state.product_name,
            "product_description": st.session_state.product_description,
            "category": st.session_state.category,
            "audience": st.session_state.audience,
            "language": st.session_state.language,
            "offer_angle": st.session_state.offer_angle,
            "campaign_objective": st.session_state.campaign_objective,
            "platform": st.session_state.platform,
            "pain_point": st.session_state.pain_point,
            "usp": st.session_state.usp,
            "brand_voice": st.session_state.brand_voice,
            "cta": st.session_state.cta,
            "hooks": st.session_state.current_hooks,
            "headlines": st.session_state.current_headlines,
            "primary_texts": st.session_state.current_primary_texts,
            "ctas": st.session_state.current_ctas,
            "video_script": st.session_state.current_video_script,
            "adset_creatives": st.session_state.current_adset_creatives,
            "adsets": st.session_state.current_adsets,
            "compliance_status": st.session_state.current_compliance_report.get("status") if st.session_state.current_compliance_report else "safe",
            "compliance_issues": st.session_state.current_compliance_report.get("issues") if st.session_state.current_compliance_report else []
        }
        
        txt_content = build_txt_export(current_detail)
        md_content = build_md_export(current_detail)
        try:
            pdf_content = build_pdf_export(current_detail)
        except Exception as e:
            pdf_content = f"Error generating PDF content: {e}".encode('utf-8')
        
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            st.download_button(
                label="Download TXT",
                data=txt_content,
                file_name=f"meta_campaign_{st.session_state.product_name.lower().replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with btn_col2:
            st.download_button(
                label="Download Markdown",
                data=md_content,
                file_name=f"meta_campaign_{st.session_state.product_name.lower().replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with btn_col3:
            st.download_button(
                label="Download PDF",
                data=pdf_content,
                file_name=f"meta_campaign_{st.session_state.product_name.lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    if generate_btn:
        # Check adset count limit
        if st.session_state.generate_adsets:
            if st.session_state.adset_count < 1:
                st.error("❌ Please enter at least 1 Ad Set.")
                st.stop()
            elif st.session_state.adset_count > 20:
                st.error("❌ Maximum 20 Ad Sets allowed.")
                st.stop()
                
        # Front-end field validation
        missing_fields = []
        if not product_name.strip(): missing_fields.append("Product Name")
        if not product_description.strip(): missing_fields.append("Product Description")
        if not brand_voice.strip(): missing_fields.append("Brand Voice Preference")
        if not pain_point.strip(): missing_fields.append("Pain Point")
        if not usp.strip(): missing_fields.append("Key USP")
        if not offer_angle.strip(): missing_fields.append("Offer/Hook Angle")
        
        # Validations for custom Others option
        if category == "Others" and not custom_category.strip():
            missing_fields.append("Custom Category Definition")
        if platform == "Others" and not custom_platform.strip():
            missing_fields.append("Custom Platform Definition")
            
        if st.session_state.generate_adsets and not st.session_state.auto_generate_adsets:
            for i in range(st.session_state.adset_count):
                inputs = st.session_state.manual_adsets_inputs[i]
                if not inputs["location"].strip():
                    missing_fields.append(f"Ad Set {i+1} Location")
                if not inputs["age_group"].strip():
                    missing_fields.append(f"Ad Set {i+1} Age Group")
                if not inputs["targeting"].strip():
                    missing_fields.append(f"Ad Set {i+1} Detailed Targeting")
            
        if missing_fields:
            st.error("⚠️ Please complete all required fields.")
        else:
            with st.spinner("🔍 Querying Structured Pydantic LLM Contracts..."):
                try:
                    # Parse manual adsets payload
                    manual_adsets_payload = []
                    if st.session_state.generate_adsets and not st.session_state.auto_generate_adsets:
                        for i in range(st.session_state.adset_count):
                            inputs = st.session_state.manual_adsets_inputs[i]
                            raw_targeting = inputs["targeting"].split("\n")
                            cleaned_targeting = [t.strip() for t in raw_targeting if t.strip()]
                            manual_adsets_payload.append({
                                "location": inputs["location"].strip(),
                                "age_group": inputs["age_group"].strip(),
                                "detailed_targeting": cleaned_targeting
                            })
                            
                    payload = {
                        "product_name": product_name,
                        "product_description": product_description,
                        "category": custom_category if category == "Others" else category,
                        "audience": audience,
                        "language": language,
                        "offer_angle": offer_angle,
                        "campaign_objective": campaign_objective,
                        "platform": custom_platform if platform == "Others" else platform,
                        "pain_point": pain_point,
                        "usp": usp,
                        "brand_voice": brand_voice.strip() if brand_voice.strip() else None,
                        "cta": cta.strip() if cta.strip() else None,
                        "generate_video_script": generate_video_script,
                        "generate_adsets": st.session_state.generate_adsets,
                        "adset_count": st.session_state.adset_count,
                        "auto_generate_adsets": st.session_state.auto_generate_adsets,
                        "manual_adsets": manual_adsets_payload
                    }
                    
                    # Frontend debug logging
                    res = requests.post(f"{BACKEND_URL}/api/v1/generate/hooks", json=payload, timeout=300)
                    
                    if res.status_code == 200:
                        data = res.json()
                        
                        # Populate session states for outputs
                        st.session_state.current_hooks = data.get("hooks", [])
                        st.session_state.current_headlines = data.get("headlines", [])
                        st.session_state.current_primary_texts = data.get("primary_texts", [])
                        st.session_state.current_ctas = data.get("ctas", [])
                        st.session_state.current_style_note = data.get("inferred_style_note", "")
                        st.session_state.current_video_script = data.get("video_script", None)
                        st.session_state.current_compliance_report = data.get("compliance_report", None)
                        st.session_state.current_adsets = data.get("adsets", [])
                        st.session_state.current_adset_creatives = data.get("adset_creatives", [])
                        
                        # Clear history cache to force reloading new list in sidebar
                        st.cache_data.clear()
                        
                        # Rerun the script to display the newly generated outputs & download options immediately
                        st.rerun()
                    else:
                        try:
                            err_detail = res.json().get("detail", "Unknown server error.")
                        except Exception:
                            err_detail = res.text
                        
                        # Friendly mappings
                        if "Gemini API key not configured" in err_detail:
                            st.error("❌ Gemini API key not configured.")
                        elif "AI generation limit reached" in err_detail or "quota exceeded" in err_detail.lower():
                            st.error("❌ AI generation limit reached. Please try again shortly.")
                        elif "Generation took too long" in err_detail:
                            st.error("❌ Generation took too long. Please try again.")
                        elif "Please complete all required fields" in err_detail:
                            st.error("❌ Please complete all required fields.")
                        elif "Please enter at least 1 Ad Set" in err_detail:
                            st.error("❌ Please enter at least 1 Ad Set.")
                        elif "Maximum 20 Ad Sets allowed" in err_detail:
                            st.error("❌ Maximum 20 Ad Sets allowed.")
                        else:
                            st.error(f"❌ Backend Generation Error: {err_detail}")
                        
                except requests.exceptions.Timeout:
                    st.error("❌ Generation took too long. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error(
                        "❌ Connection Error: Could not connect to the backend server. "
                        "Please ensure the FastAPI backend is running."
                    )
                except Exception as ex:
                    st.error("❌ An unexpected error occurred. Please try again.")

    # RENDER TABS IF OUTPUT EXISTS IN STATE (Either newly generated or reloaded from history)
    # RENDER TABS IF OUTPUT EXISTS IN STATE (Either newly generated or reloaded from history)
    if st.session_state.current_hooks is not None:
        adset_creatives = st.session_state.get("current_adset_creatives")
        
        if adset_creatives:
            st.subheader("🎯 Generated Meta Ad Sets & Target-Tailored Creatives")
            for idx, ac in enumerate(adset_creatives, 1):
                with st.container(border=True):
                    st.markdown(f"### 🎯 AD SET {ac.get('adset_number', idx)}")
                    
                    # Targeting Details styled as premium info cards
                    targeting_list = ac.get('detailed_targeting', [])
                    targeting_badges = "".join([f'<span class="badge">{t}</span>' for t in targeting_list]) if targeting_list else '<span class="badge">N/A</span>'
                    st.markdown(
                        f"""
                        <div class="adset-info-grid">
                            <div class="info-card">
                                <div class="info-label">📍 Location</div>
                                <div class="info-value">{ac.get('location', 'N/A')}</div>
                            </div>
                            <div class="info-card">
                                <div class="info-label">👥 Age Group</div>
                                <div class="info-value">{ac.get('age_group', 'N/A')}</div>
                            </div>
                            <div class="info-card wide">
                                <div class="info-label">🎯 Detailed Targeting</div>
                                <div class="info-value-badges">{targeting_badges}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Creative Assets nested inside tabs per ad set
                    c_tabs = st.tabs([
                        "🧲 Hooks & Headlines",
                        "✍️ Primary Copy",
                        "🎬 Video Script",
                        "🛡️ Compliance"
                    ])
                    
                    with c_tabs[0]:
                        st.markdown("**🧲 Hook Options (Exactly 5)**")
                        for h_idx, hook in enumerate(ac.get("hooks", []), 1):
                            render_copyable_card(f"Hook Variation 0{h_idx}", hook, f"adset_{idx}_hook_{h_idx}")
                            
                        st.markdown("**📣 Aligned Headlines (Exactly 5)**")
                        for hl_idx, headline in enumerate(ac.get("headlines", []), 1):
                            render_copyable_card(f"Headline Option 0{hl_idx}", headline, f"adset_{idx}_headline_{hl_idx}")
                            
                    with c_tabs[1]:
                        st.markdown("**📝 Body Copy (Primary Text - Exactly 3)**")
                        for pt_idx, pt in enumerate(ac.get("primary_texts", []), 1):
                            render_copyable_card(f"Primary Text 0{pt_idx}", pt, f"adset_{idx}_pt_{pt_idx}")
                            
                        st.markdown("**📣 Call to Action Variations**")
                        ctas = ac.get("ctas", [])
                        if ctas:
                            st.write("  •  ".join(ctas))
                            
                    with c_tabs[2]:
                        v_script = ac.get("video_script")
                        if v_script:
                            st.markdown("**🎬 Video Screenplay Script**")
                            if isinstance(v_script, str):
                                st.text(v_script)
                            else:
                                v_hook = v_script.get("hook", "")
                                v_scenes = v_script.get("scenes", [])
                                v_cta = v_script.get("cta", "")
                                
                                st.caption("Opening Hook (0-5s)")
                                st.text(v_hook)
                                
                                for s_idx, scene in enumerate(v_scenes, 1):
                                    st.caption(f"Scene {s_idx:02d} framing")
                                    st.text(f"Visual: {scene.get('scene', '')}")
                                    st.text(f"Voiceover Dialogue: \"{scene.get('voiceover', '')}\"")
                                    st.write("")
                                    
                                st.caption("Closing Screen & CTA (25-30s)")
                                st.text(v_cta)
                        else:
                            st.info("Video script not requested.")
                            
                    with c_tabs[3]:
                        comp_data = ac.get("compliance_report")
                        if comp_data:
                            comp_status = comp_data.get("status", "safe").lower()
                            comp_issues = comp_data.get("issues", [])
                            
                            st.markdown("**🛡️ Meta Policy Compliance Report**")
                            if comp_status == "safe":
                                st.success(f"🟢 Ad Set {idx} Compliance Status: SAFE\n\nAd copies are policy-compliant.")
                            elif comp_status == "warning":
                                st.warning(f"🟡 Ad Set {idx} Compliance Status: WARNING\n\nPotential soft policy flags detected.")
                            else:
                                st.error(f"🔴 Ad Set {idx} Compliance Status: HIGH RISK\n\nViolations of Meta advertising policy detected!")
                                
                            if comp_issues:
                                st.write("**📋 Policy Issues & Safe Rewrites:**")
                                for issue_idx, issue in enumerate(comp_issues, 1):
                                    severity_icon = "⚠️" if issue.get("severity") == "warning" else "🚨"
                                    with st.container(border=True):
                                        st.write(f"**{severity_icon} Issue 0{issue_idx}: {issue.get('type')} ({issue.get('rule_id')})**")
                                        st.write(f"**Flagged Content:** {issue.get('text')}")
                                        st.success(f"💡 **Safer Rewrite Suggestion:** {issue.get('suggestion')}")
                            else:
                                st.info("💡 No policy issues identified for this Ad Set.")
                        else:
                            st.info("💡 Compliance report not available.")
            st.divider()
            
            style_note = st.session_state.current_style_note
            if style_note:
                st.subheader("🎭 Inferred Tone Synthesis")
                with st.container(border=True):
                    st.write(style_note)
        else:
            # Fallback to single campaign display
            adsets = st.session_state.get("current_adsets")
            if adsets:
                st.subheader("🎯 Generated Meta Ad Sets")
                for idx, adset in enumerate(adsets, 1):
                    with st.container(border=True):
                        st.markdown(f"### 🎯 AD SET {idx}")
                        targeting_list = adset.get('detailed_targeting', [])
                        targeting_badges = "".join([f'<span class="badge">{t}</span>' for t in targeting_list]) if targeting_list else '<span class="badge">N/A</span>'
                        st.markdown(
                            f"""
                            <div class="adset-info-grid">
                                <div class="info-card">
                                    <div class="info-label">📍 Location</div>
                                    <div class="info-value">{adset.get('location', 'N/A')}</div>
                                </div>
                                <div class="info-card">
                                    <div class="info-label">👥 Age Group</div>
                                    <div class="info-value">{adset.get('age_group', 'N/A')}</div>
                                </div>
                                <div class="info-card wide">
                                    <div class="info-label">🎯 Detailed Targeting</div>
                                    <div class="info-value-badges">{targeting_badges}</div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                st.divider()
            elif st.session_state.generate_adsets:
                st.info("No Ad Sets generated.")
                st.divider()
    
            hooks = st.session_state.current_hooks
            headlines = st.session_state.current_headlines
            primary_texts = st.session_state.current_primary_texts
            ctas = st.session_state.current_ctas
            style_note = st.session_state.current_style_note
            video_script_data = st.session_state.current_video_script
            compliance_data = st.session_state.current_compliance_report
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "🧲 Hooks & Headlines", 
                "✍️ Primary Copy", 
                "🎬 Video Script", 
                "🛡️ Compliance"
            ])
            
            with tab1:
                st.subheader("🧲 Hook Options")
                for idx, hook_item in enumerate(hooks, 1):
                    render_copyable_card(f"Hook Variation 0{idx}", hook_item, f"single_hook_{idx}")
                        
                st.subheader("📣 Aligned Headlines")
                for idx, headline_item in enumerate(headlines, 1):
                    render_copyable_card(f"Headline Option 0{idx}", headline_item, f"single_headline_{idx}")
                    
            with tab2:
                st.subheader("📝 Body Copy (Primary Text)")
                for idx, text_item in enumerate(primary_texts, 1):
                    render_copyable_card(f"Primary Text 0{idx}", text_item, f"single_pt_{idx}")
                        
                st.subheader("📣 Call to Action Variations")
                if ctas:
                    with st.container(border=True):
                        st.write("  •  ".join(ctas))
                    
            with tab3:
                if video_script_data:
                    st.subheader("🎬 Video Screenplay Script")
                    with st.container(border=True):
                        if isinstance(video_script_data, str):
                            st.text(video_script_data)
                        else:
                            v_hook = video_script_data.get("hook", "")
                            v_scenes = video_script_data.get("scenes", [])
                            v_cta = video_script_data.get("cta", "")
                            
                            st.caption("Opening Hook (0-5s)")
                            st.text(v_hook)
                            
                            for s_idx, scene in enumerate(v_scenes, 1):
                                st.caption(f"Scene {s_idx:02d} framing")
                                st.text(f"Visual: {scene.get('scene', '')}")
                                st.text(f"Voiceover Dialogue: \"{scene.get('voiceover', '')}\"")
                                st.write("")
                                
                            st.caption("Closing Screen & CTA (25-30s)")
                            st.text(v_cta)
                else:
                    st.info("Video script not requested.")
                    
            with tab4:
                if compliance_data:
                    comp_status = compliance_data.get("status", "safe").lower()
                    comp_issues = compliance_data.get("issues", [])
                    
                    st.subheader("🛡️ Meta Policy Compliance Report")
                    
                    if comp_status == "safe":
                        st.success("🟢 Meta Ad Compliance Status: SAFE\n\nAd copies are policy-compliant. Generated creative assets meet standard Meta safety and claims policies. No policy risk found.")
                    elif comp_status == "warning":
                        st.warning("🟡 Meta Ad Compliance Status: WARNING\n\nPotential soft policy flags detected. Review the warnings below before deploying your campaign.")
                    else:
                        st.error("🔴 Meta Ad Compliance Status: HIGH RISK\n\nViolations of Meta advertising policy detected! The ad copy contains phrases likely to be flagged or rejected by Meta's automated ad scanners.")
                    
                    if comp_issues:
                        st.subheader("📋 Policy Issues & Safe Rewrites")
                        for idx, issue in enumerate(comp_issues, 1):
                            severity_icon = "⚠️" if issue.get("severity") == "warning" else "🚨"
                            
                            with st.container(border=True):
                                st.write(f"**{severity_icon} Issue 0{idx}: {issue.get('type')} ({issue.get('rule_id')})**")
                                st.caption(f"Severity: {issue.get('severity')}")
                                st.write(f"**Description:** {issue.get('description', 'Meta policy scanner flagged phrase.')}")
                                st.write(f"**Flagged Content:** {issue.get('text')}")
                                st.success(f"💡 **Safer Rewrite Suggestion:** {issue.get('suggestion')}")
                    else:
                        st.info("💡 No policy issues identified. Generated creatives are safe for Meta platform deployment.")
                        
                if style_note:
                    st.subheader("🎭 Inferred Tone Synthesis")
                    with st.container(border=True):
                        st.write(style_note)
    else:
        st.info("💡 Complete the Creative Brief on the left and click 'Generate Campaign Assets' to synthesize ad copy, tone references, and screenplays.")
