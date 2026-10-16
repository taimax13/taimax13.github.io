"""Build the CV PDF from the reviewed wording in _data/cv.json.
Requires reportlab and Pillow. Run: python3 scripts/build_cv.py [--variant short]
"""
import argparse
from html import escape
from io import BytesIO
import json
from pathlib import Path
import re
from PIL import Image
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, PageBreak

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--variant', choices=['full', 'short'], default='full')
SHORT = parser.parse_args().variant == 'short'
OUTPUT = ROOT / ('assets/files/talex-maxim-cv-short.pdf' if SHORT else 'assets/files/talex-maxim-cv.pdf')
DATA = json.loads((ROOT / ('_data/cv-short.json' if SHORT else '_data/cv.json')).read_text())
rl_config.useA85 = False
portrait_buffer = BytesIO()
with Image.open(ROOT / 'assets/images/talex-portrait-gold-teal-v2.png') as original:
    portrait = original.convert('RGB')
    portrait.thumbnail((480, 480), Image.Resampling.LANCZOS)
    portrait.save(portrait_buffer, format='JPEG', quality=92, optimize=True)
portrait_buffer.seek(0)
PORTRAIT = ImageReader(portrait_buffer)
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
for name, filename in [('CV', 'DejaVuSans.ttf'), ('CV-Bold', 'DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
pdfmetrics.registerFontFamily('CV', normal='CV', bold='CV-Bold')
INK = colors.HexColor('#101719')
TEAL = colors.HexColor('#245e58')
GOLD = colors.HexColor('#a58143')
MUTED = colors.HexColor('#4b5659')
WIDTH, HEIGHT = A4
LEFT = 44
CONTENT = WIDTH - 2 * LEFT
STYLES = {
    'paragraph': ParagraphStyle('paragraph', fontName='CV', fontSize=9.7, leading=14, textColor=INK, spaceAfter=6),
    'bullet': ParagraphStyle('bullet', fontName='CV', fontSize=9.7, leading=14, textColor=INK, spaceAfter=4, leftIndent=10, firstLineIndent=-10),
    'section': ParagraphStyle('section', fontName='CV-Bold', fontSize=11, leading=16, textColor=TEAL, spaceBefore=10, spaceAfter=7, keepWithNext=True),
    'subheading': ParagraphStyle('subheading', fontName='CV-Bold', fontSize=12.2, leading=17, textColor=INK, spaceBefore=6, spaceAfter=3, keepWithNext=True),
    'metadata': ParagraphStyle('metadata', fontName='CV', fontSize=9.3, leading=13.5, textColor=TEAL, spaceAfter=7, keepWithNext=True),
    'label': ParagraphStyle('label', fontName='CV-Bold', fontSize=9.7, leading=14, textColor=INK, spaceBefore=4, spaceAfter=3, keepWithNext=True),
}

if SHORT:
    for name in ['paragraph', 'bullet']:
        STYLES[name].fontSize = 9.5
        STYLES[name].leading = 13.2
        STYLES[name].spaceAfter = 3
    for name, values in {
        'section': (10.6, 15, 6, 4),
        'subheading': (11.1, 15, 4, 3),
        'metadata': (9, 12.4, 0, 4),
        'label': (9.3, 13, 3, 3),
    }.items():
        style = STYLES[name]
        style.fontSize, style.leading, style.spaceBefore, style.spaceAfter = values


def clean(text):
    return re.sub(r'[\u2010-\u2015]', '-', text)

def draw_text(canvas, text, y, size, color, bold=False):
    text = clean(text)
    font = 'CV-Bold' if bold else 'CV'
    assert pdfmetrics.stringWidth(text, font, size) <= CONTENT-112, 'Header overlaps portrait'
    canvas.setFont(font, size)
    canvas.setFillColor(color)
    canvas.drawString(LEFT, HEIGHT-y, text)

def decoration(canvas, doc):
    canvas.saveState()
    canvas.setTitle('Talex Maxim - Curriculum Vitae')
    canvas.setAuthor('Talex Maxim')
    canvas.setSubject(clean(DATA['header'][1]))
    if doc.page == 1:
        canvas.setFillColor(INK)
        header_height = 120 if SHORT else 148
        canvas.rect(0, HEIGHT-header_height, WIDTH, header_height, fill=1, stroke=0)
        size = 86 if SHORT else 96
        x, y = WIDTH-LEFT-size, HEIGHT-(106 if SHORT else 126)
        canvas.drawImage(PORTRAIT, x, y, width=size, height=size, preserveAspectRatio=True)
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(0.7)
        canvas.rect(x, y, size, size, fill=0, stroke=1)
        paper = colors.HexColor('#f2eee5')
        gold = colors.HexColor('#d4b67b')
        offsets = [36,58,80,97] if SHORT else [41,62,80,97,117,133]
        sizes = [25,10.5,8.7,8.7] if SHORT else [25,9.5,8.8,8.1,8.8,7.7]
        palette = [paper,gold,paper,paper] if SHORT else [paper,gold,paper,gold,paper,paper]
        for i, (line, offset, font_size, color) in enumerate(zip(DATA['header'], offsets, sizes, palette)):
            draw_text(canvas, line, offset, font_size, color, i == 0)
        if SHORT:
            canvas.linkURL('mailto:taimax13@gmail.com', (LEFT,HEIGHT-84,LEFT+112,HEIGHT-71))
            canvas.linkURL('https://github.com/taimax13', (LEFT+120,HEIGHT-84,LEFT+290,HEIGHT-71))
            canvas.linkURL('https://www.linkedin.com/in/talex-maxim/', (LEFT,HEIGHT-101,LEFT+260,HEIGHT-88))
        else:
            canvas.linkURL('mailto:taimax13@gmail.com', (LEFT,HEIGHT-121,LEFT+120,HEIGHT-108))
            canvas.linkURL('https://github.com/taimax13', (LEFT,HEIGHT-137,LEFT+140,HEIGHT-124))
            canvas.linkURL('https://www.linkedin.com/in/talex-maxim/', (LEFT+150,HEIGHT-137,LEFT+CONTENT-112,HEIGHT-124))
    else:
        canvas.setFont('CV-Bold', 11)
        canvas.setFillColor(INK)
        canvas.drawString(LEFT, HEIGHT-34, DATA['header'][0])
        canvas.setFont('CV', 8)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(WIDTH-LEFT, HEIGHT-34, 'Curriculum Vitae')
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.8)
    canvas.line(LEFT,35,WIDTH-LEFT,35)
    canvas.setFont('CV', 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(LEFT,22,'taimax13.github.io')
    canvas.drawRightString(WIDTH-LEFT,22,str(doc.page))
    canvas.restoreState()

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc = BaseDocTemplate(str(OUTPUT), pagesize=A4, pageCompression=1)
doc.addPageTemplates([
    PageTemplate(id='first', autoNextPageTemplate='later', frames=[Frame(LEFT,49,CONTENT,HEIGHT-(187 if SHORT else 215),leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)], onPage=decoration),
    PageTemplate(id='later', frames=[Frame(LEFT,49,CONTENT,HEIGHT-105,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)], onPage=decoration),
])
story=[]
for block in DATA['blocks']:
    kind, text = block['kind'], block['text']
    if SHORT and kind == 'section' and text == 'SELECTED PROJECTS':
        story.append(PageBreak())
    prefix = '- ' if kind=='bullet' else ''
    story.append(Paragraph(escape(prefix+clean(text)), STYLES[kind]))
doc.build(story)
print(OUTPUT)
