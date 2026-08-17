"""
Sihtak (صحتك) Premium Product Deck — v2
Full-bleed backgrounds, 3D accents, shadows, rounded phones, transitions.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree
import os

# ── Paths ──
BASE = os.path.dirname(os.path.abspath(__file__))
SCREENS = os.path.join(BASE, "screens")
ASSETS = os.path.join(BASE, "assets")
ICON = os.path.join(BASE, "..", "icon.png")
OUT = os.path.join(BASE, "Sihtak-Guide-v2.pptx")

# ── Brand Colors ──
TEAL    = RGBColor(0x0D, 0x94, 0x88)
TEAL_L  = RGBColor(0x14, 0xB8, 0xA6)
TEAL_D  = RGBColor(0x0F, 0x76, 0x6E)
DARK    = RGBColor(0x0F, 0x17, 0x2A)
MID     = RGBColor(0x47, 0x55, 0x69)
LIGHT   = RGBColor(0x94, 0xA3, 0xB8)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
OFF_W   = RGBColor(0xF8, 0xFA, 0xFC)
TEAL_BG = RGBColor(0xF0, 0xFD, 0xFA)
MINT    = RGBColor(0xCC, 0xFB, 0xF1)

# ── Presentation Setup ──
prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
W = prs.slide_width
H = prs.slide_height
TOTAL = 10


# ═══════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def solid_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_bg_image(slide, filename):
    """Full-bleed background image, sent to back."""
    path = os.path.join(ASSETS, filename)
    if not os.path.exists(path):
        return None
    pic = slide.shapes.add_picture(path, 0, 0, W, H)
    sp = pic._element
    tree = sp.getparent()
    tree.remove(sp)
    tree.insert(2, sp)
    return pic


def add_accent(slide, filename, left, top, width=None, height=None, opacity=100):
    """Decorative accent image with optional opacity (0-100)."""
    path = os.path.join(ASSETS, filename)
    if not os.path.exists(path):
        return None
    kw = {}
    if width:  kw['width'] = width
    if height: kw['height'] = height
    pic = slide.shapes.add_picture(path, left, top, **kw)
    if opacity < 100:
        blip = pic._element.find('.//' + qn('a:blip'))
        if blip is not None:
            am = etree.SubElement(blip, qn('a:alphaModFix'))
            am.set('amt', str(opacity * 1000))
    return pic


def _set_shape_transparency(shape, transparency_pct):
    """Set transparency (0-100) on a shape's solid fill via XML."""
    spPr = shape._element.find(qn('p:spPr'))
    if spPr is None:
        return
    srgb = spPr.find('.//' + qn('a:srgbClr'))
    if srgb is not None:
        # Remove existing alpha
        for a in srgb.findall(qn('a:alpha')):
            srgb.remove(a)
        a = etree.SubElement(srgb, qn('a:alpha'))
        a.set('val', str((100 - transparency_pct) * 1000))


def add_overlay(slide, left, top, width, height, color=WHITE, transparency=15):
    """Semi-transparent rounded rectangle overlay."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    _set_shape_transparency(shape, transparency)
    return shape


def _shadow_xml(spPr):
    """Inject outer-shadow effect into spPr element."""
    for e in spPr.findall(qn('a:effectLst')):
        spPr.remove(e)
    el = etree.SubElement(spPr, qn('a:effectLst'))
    sh = etree.SubElement(el, qn('a:outerShdw'))
    sh.set('blurRad', '114300')
    sh.set('dist', '50800')
    sh.set('dir', '5400000')
    sh.set('algn', 'bl')
    sh.set('rotWithShape', '0')
    c = etree.SubElement(sh, qn('a:srgbClr'))
    c.set('val', '000000')
    alp = etree.SubElement(c, qn('a:alpha'))
    alp.set('val', '20000')


def add_shadow(shape):
    """Add drop shadow to any shape/picture."""
    spPr = shape._element.find(qn('p:spPr'))
    if spPr is not None:
        _shadow_xml(spPr)


def add_phone(slide, img_name, left, top, h=Inches(4.2), shadow=True, rounded=True):
    """Phone screenshot with rounded corners + shadow."""
    path = os.path.join(SCREENS, img_name)
    if not os.path.exists(path):
        return None
    pic = slide.shapes.add_picture(path, left, top, height=h)
    spPr = pic._element.find(qn('p:spPr'))
    if spPr is not None:
        if rounded:
            pg = spPr.find(qn('a:prstGeom'))
            if pg is not None:
                pg.set('prst', 'roundRect')
                av = pg.find(qn('a:avLst'))
                if av is None:
                    av = etree.SubElement(pg, qn('a:avLst'))
                else:
                    for ch in list(av): av.remove(ch)
                gd = etree.SubElement(av, qn('a:gd'))
                gd.set('name', 'adj')
                gd.set('fmla', 'val 5000')
        if shadow:
            _shadow_xml(spPr)
    return pic


def add_text(slide, left, top, width, height, text, size=18, bold=False,
             color=DARK, align=PP_ALIGN.RIGHT, font_name="Tajawal", name=None):
    tb = slide.shapes.add_textbox(left, top, width, height)
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = align
    return tf


def add_para(tf, text, size=14, bold=False, color=MID, align=PP_ALIGN.RIGHT,
             font_name="Tajawal", space_before=Pt(4)):
    p = tf.add_paragraph()
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = align
    p.space_before = space_before
    return p


def check_item(tf, text, size=13, color=MID):
    p = tf.add_paragraph()
    p.text = f"✓  {text}"
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.name = "Tajawal"
    p.alignment = PP_ALIGN.RIGHT
    p.space_before = Pt(6)
    return p


def section_badge(slide, left, top, text, emoji=""):
    w, h = Inches(3.0), Inches(0.44)
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = TEAL_BG
    shape.line.fill.background()
    tf = shape.text_frame
    tf.paragraphs[0].text = f"{emoji}  {text}" if emoji else text
    tf.paragraphs[0].font.size = Pt(12)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = TEAL
    tf.paragraphs[0].font.name = "Tajawal"
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    add_shadow(shape)
    return shape


def teal_bar(slide):
    """Bottom teal accent bar — named for morph."""
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, H - Inches(0.06), W, Inches(0.06))
    s.fill.solid()
    s.fill.fore_color.rgb = TEAL
    s.line.fill.background()
    s.name = "!!TealBar"
    return s


def slide_footer(slide, num, total=TOTAL, dark=False):
    c = WHITE if dark else LIGHT
    add_text(slide, Inches(0.5), H - Inches(0.5), Inches(2), Inches(0.3),
             f"{num} / {total}", size=9, color=c, align=PP_ALIGN.LEFT, font_name="Inter")
    add_text(slide, W - Inches(2.5), H - Inches(0.5), Inches(2), Inches(0.3),
             "sihtak.com", size=9, color=c, align=PP_ALIGN.RIGHT, font_name="Inter")


def add_logo(slide, left, top, w=Inches(0.7)):
    if os.path.exists(ICON):
        pic = slide.shapes.add_picture(ICON, left, top, width=w)
        pic.name = "!!Logo"
        return pic


def add_transition(slide, speed='slow'):
    """Fade transition (switch to Morph in PowerPoint for best effect)."""
    sld = slide._element
    for t in sld.findall(qn('p:transition')):
        sld.remove(t)
    trans = etree.Element(qn('p:transition'))
    trans.set('spd', speed)
    trans.set('advClick', '1')
    etree.SubElement(trans, qn('p:fade'))
    csld = sld.find(qn('p:cSld'))
    if csld is not None:
        csld.addnext(trans)


def add_chip_row(slide, chips, start_x, y, spacing=Inches(2.35)):
    """Row of branded chips."""
    x = start_x
    for text, emoji in chips:
        w, h = Inches(2.2), Inches(0.44)
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
        shape.fill.solid()
        shape.fill.fore_color.rgb = WHITE
        shape.line.color.rgb = RGBColor(0xE2, 0xE8, 0xF0)
        shape.line.width = Pt(1)
        tf = shape.text_frame
        tf.paragraphs[0].text = f"{emoji} {text}"
        tf.paragraphs[0].font.size = Pt(11)
        tf.paragraphs[0].font.bold = True
        tf.paragraphs[0].font.color.rgb = DARK
        tf.paragraphs[0].font.name = "Tajawal"
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        add_shadow(shape)
        x -= spacing


def add_number_accent(slide, num, left, top, color=None):
    """Large decorative number in corner."""
    c = color or RGBColor(0xE2, 0xE8, 0xF0)
    add_text(slide, left, top, Inches(1.5), Inches(1.2),
             num, size=72, bold=True, color=c, align=PP_ALIGN.LEFT, font_name="Inter")


# ═══════════════════════════════════════════════════════════
#  SLIDE 1 — COVER
# ═══════════════════════════════════════════════════════════
sl = prs.slides.add_slide(prs.slide_layouts[6])
add_bg_image(sl, "bg_gradient_0.png")

# Decorative 3D accent bottom-right
add_accent(sl, "medical_row.png", W - Inches(6), H - Inches(3.2),
           width=Inches(6), opacity=22)

# White overlay panel for text
add_overlay(sl, Inches(1.5), Inches(0.4), Inches(10.3), Inches(4.0),
            WHITE, transparency=25)

# Logo
add_logo(sl, Inches(5.95), Inches(0.6), Inches(1.0))

# Title
add_text(sl, Inches(2), Inches(1.8), Inches(9.3), Inches(1.0),
         "صحتك", size=52, bold=True, color=TEAL, name="!!Title")
add_text(sl, Inches(2), Inches(2.7), Inches(9.3), Inches(0.7),
         "كل صحتك في تطبيق واحد", size=36, bold=True, color=DARK)

# Subtitle
add_text(sl, Inches(2.5), Inches(3.5), Inches(8.3), Inches(0.7),
         "مساعد صحي ذكي يتحدث معك بالصوت، يمسح تحاليلك، يتابع أدويتك، ويدير صحة عائلتك",
         size=15, color=MID)

# Feature chips
chips = [("ذكاء اصطناعي صوتي", "🤖"), ("ماسح تحاليل", "🔬"), ("متابعة أدوية", "💊"),
         ("صحة العائلة", "👨‍👩‍👧"), ("عربي + English", "🌍")]
add_chip_row(sl, chips, Inches(10.0), Inches(4.6))

# Phone screenshots
add_phone(sl, "IMG_6510.PNG", Inches(2.2), Inches(5.0), h=Inches(2.2))
add_phone(sl, "IMG_6621.PNG", Inches(5.0), Inches(4.6), h=Inches(2.6))
add_phone(sl, "IMG_6624.PNG", Inches(8.0), Inches(5.0), h=Inches(2.2))

teal_bar(sl)
slide_footer(sl, "01")
add_transition(sl)


# ═══════════════════════════════════════════════════════════
#  SLIDE 2 — VOICE AI ASSISTANT
# ═══════════════════════════════════════════════════════════
sl = prs.slides.add_slide(prs.slide_layouts[6])
solid_bg(sl, WHITE)

# AI Brain accent on right
add_accent(sl, "ai_brain.png", W - Inches(5.5), Inches(0.5),
           height=Inches(6.5), opacity=18)

# Number accent
add_number_accent(sl, "01", Inches(0.4), Inches(0.3))

# Section badge
section_badge(sl, Inches(9.5), Inches(0.5), "المساعد الذكي", "🤖")

# Title
add_text(sl, Inches(5.5), Inches(1.2), Inches(7.3), Inches(0.8),
         "تحدّث مع طبيبك الذكي بالصوت", size=32, bold=True, color=DARK)

# Description + checks
tf = add_text(sl, Inches(5.5), Inches(2.1), Inches(7.3), Inches(0.5),
              "اسأله أي سؤال صحي — يفهم ملفك الصحي بالكامل", size=15, color=MID)
check_item(tf, "تحويل صوت إلى نص فوري — تكلم بطبيعية")
check_item(tf, "يعرف أدويتك وتحاليلك وحساسيتك")
check_item(tf, "يعمل بالعربي والإنجليزي")
check_item(tf, "قاطعه بأي وقت أثناء الكلام")
check_item(tf, "مصادر من Mayo Clinic و WHO")

# Phone screenshots
add_phone(sl, "IMG_6522.PNG", Inches(1.0), Inches(1.2), h=Inches(5.2))
add_phone(sl, "IMG_6510.PNG", Inches(3.3), Inches(1.2), h=Inches(5.2))

teal_bar(sl)
slide_footer(sl, "02")
add_transition(sl)


# ═══════════════════════════════════════════════════════════
#  SLIDE 3 — DRUG INTERACTIONS
# ═══════════════════════════════════════════════════════════
sl = prs.slides.add_slide(prs.slide_layouts[6])
add_bg_image(sl, "bg_gradient_1.png")

# White overlay for readability
add_overlay(sl, Inches(4.8), Inches(0.3), Inches(8.2), Inches(6.9),
            WHITE, transparency=12)

# Capsule DNA accent bottom-left
add_accent(sl, "capsule_dna.png", Inches(-0.5), H - Inches(4),
           height=Inches(4), opacity=25)

add_number_accent(sl, "02", Inches(5.0), Inches(0.4), RGBColor(0xD1, 0xD5, 0xDB))
section_badge(sl, Inches(9.5), Inches(0.5), "فحص الأدوية", "💊")

add_text(sl, Inches(5.5), Inches(1.2), Inches(7.3), Inches(0.8),
         "يفحص تفاعلات أدويتك تلقائياً", size=32, bold=True, color=DARK)

tf = add_text(sl, Inches(5.5), Inches(2.1), Inches(7.3), Inches(0.5),
              "ضغطة واحدة تفحص كل أدويتك وتكشف أي تفاعلات خطيرة", size=15, color=MID)
check_item(tf, "فحص تلقائي لكل أدويتك النشطة")
check_item(tf, "تصنيف: خفيف · متوسط · شديد")
check_item(tf, "يكتشف أنماطاً مقلقة في صحتك")
check_item(tf, "إرسال صور من الكاميرا للتحليل")

add_phone(sl, "IMG_6624.PNG", Inches(1.0), Inches(1.0), h=Inches(5.4))
add_phone(sl, "IMG_6625.PNG", Inches(3.2), Inches(1.0), h=Inches(5.4))

teal_bar(sl)
slide_footer(sl, "03")
add_transition(sl)


# ═══════════════════════════════════════════════════════════
#  SLIDE 4 — LAB SCANNER
# ═══════════════════════════════════════════════════════════
sl = prs.slides.add_slide(prs.slide_layouts[6])
solid_bg(sl, WHITE)

# Molecular flow accent bottom-right
add_accent(sl, "molecular_flow.png", W - Inches(6), H - Inches(3.5),
           width=Inches(6), opacity=15)

add_number_accent(sl, "03", Inches(0.4), Inches(0.3))
section_badge(sl, Inches(9.5), Inches(0.5), "ماسح التحاليل", "🔬")

add_text(sl, Inches(5.0), Inches(1.2), Inches(7.8), Inches(0.8),
         "صوّر تحاليلك والذكاء الاصطناعي يحللها", size=32, bold=True, color=DARK)

tf = add_text(sl, Inches(5.0), Inches(2.1), Inches(7.8), Inches(0.5),
              "صورة واحدة لتقرير تحاليلك — يقرأ ويعطيك تقييم شامل", size=15, color=MID)
check_item(tf, "يقرأ ١٨+ تحليل من صورة واحدة")
check_item(tf, "تصنيف الخطورة: منخفض · متوسط · عالي")
check_item(tf, "يراعي أدويتك الحالية بالتحليل")
check_item(tf, "توصيات عملية وفحوصات إضافية")
check_item(tf, 'زر "اسأل الذكاء الاصطناعي عن النتائج"')

add_phone(sl, "IMG_6626.PNG", Inches(1.2), Inches(0.8), h=Inches(5.8))

teal_bar(sl)
slide_footer(sl, "04")
add_transition(sl)


# ═══════════════════════════════════════════════════════════
#  SLIDE 5 — SYMPTOM CHECKER
# ═══════════════════════════════════════════════════════════
sl = prs.slides.add_slide(prs.slide_layouts[6])
add_bg_image(sl, "bg_gradient_3.png")

add_overlay(sl, Inches(4.8), Inches(0.3), Inches(8.2), Inches(6.9),
            WHITE, transparency=12)

# Capsule person accent
add_accent(sl, "capsule_person.png", Inches(-0.3), H - Inches(4.5),
           height=Inches(4.5), opacity=22)

add_number_accent(sl, "04", Inches(5.0), Inches(0.4), RGBColor(0xD1, 0xD5, 0xDB))
section_badge(sl, Inches(9.5), Inches(0.5), "فحص الأعراض", "🩺")

add_text(sl, Inches(5.5), Inches(1.2), Inches(7.3), Inches(0.8),
         "اوصف أعراضك واحصل على تشخيص ذكي", size=32, bold=True, color=DARK)

tf = add_text(sl, Inches(5.5), Inches(2.1), Inches(7.3), Inches(0.5),
              "اكتب أعراضك بكلماتك — ٥ أسباب محتملة مع مستوى الطوارئ", size=15, color=MID)
check_item(tf, "🟢 أخضر: رعاية ذاتية في المنزل")
check_item(tf, "🟡 أصفر: راجع طبيب قريباً")
check_item(tf, "🔴 أحمر: اذهب للطوارئ فوراً")
check_item(tf, "خطوات علاج فورية وتحذيرات")
check_item(tf, "يراعي أدويتك بالتحليل")

add_phone(sl, "IMG_6639.PNG", Inches(1.0), Inches(1.0), h=Inches(5.4))
add_phone(sl, "IMG_6640.PNG", Inches(3.2), Inches(1.0), h=Inches(5.4))

teal_bar(sl)
slide_footer(sl, "05")
add_transition(sl)


# ═══════════════════════════════════════════════════════════
#  SLIDE 6 — HEALTH TRACKING
# ═══════════════════════════════════════════════════════════
sl = prs.slides.add_slide(prs.slide_layouts[6])
solid_bg(sl, WHITE)

# Capsule heart accent top-right
add_accent(sl, "capsule_heart_gold.png", W - Inches(4.5), Inches(0),
           height=Inches(4), opacity=15)

add_number_accent(sl, "05", Inches(0.4), Inches(0.3))
section_badge(sl, Inches(9.5), Inches(0.5), "متابعة الصحة", "📊")

add_text(sl, Inches(4.5), Inches(1.2), Inches(8.3), Inches(0.8),
         "راقب كل جوانب صحتك يومياً", size=32, bold=True, color=DARK)

# Category text right
tf = add_text(sl, Inches(7.2), Inches(2.3), Inches(5.6), Inches(5.0), "", size=14, color=MID)
p = tf.paragraphs[0]
p.text = "❤️  العلامات الحيوية"
p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = DARK
p.font.name = "Tajawal"; p.alignment = PP_ALIGN.RIGHT
check_item(tf, "ضغط الدم · نبض القلب · سكر الدم · حرارة")
check_item(tf, "رسم بياني أسبوعي مع إحصائيات")

add_para(tf, "", size=4)
add_para(tf, "🥗  التغذية والسعرات", size=16, bold=True, color=DARK)
check_item(tf, "سعرات ومغذيات يومية مع ماسح باركود")
check_item(tf, "قاعدة بيانات أطعمة ومطاعم")

add_para(tf, "", size=4)
add_para(tf, "😴  النوم والتمارين", size=16, bold=True, color=DARK)
check_item(tf, "جودة النوم والاستيقاظات والنشاط الرياضي")

add_para(tf, "", size=4)
add_para(tf, "🌙  صحة المرأة + Apple Health", size=16, bold=True, color=DARK)
check_item(tf, "دورة شهرية وخصوبة ومزاج")
check_item(tf, "مزامنة ١٠ مقاييس من Apple Health")

# Phone screenshots
add_phone(sl, "IMG_6642.PNG", Inches(0.6), Inches(2.2), h=Inches(3.8))
add_phone(sl, "IMG_6641.PNG", Inches(2.5), Inches(2.2), h=Inches(3.8))
add_phone(sl, "IMG_6661.PNG", Inches(4.4), Inches(2.2), h=Inches(3.8))

# Smaller bottom phones
add_phone(sl, "IMG_6630.PNG", Inches(1.2), Inches(6.1), h=Inches(1.2))
add_phone(sl, "IMG_6635.PNG", Inches(3.2), Inches(6.1), h=Inches(1.2))

teal_bar(sl)
slide_footer(sl, "06")
add_transition(sl)


# ═══════════════════════════════════════════════════════════
#  SLIDE 7 — HEALTH PASSPORT + DIRECTORY
# ═══════════════════════════════════════════════════════════
sl = prs.slides.add_slide(prs.slide_layouts[6])
add_bg_image(sl, "bg_gradient_0.png")

add_overlay(sl, Inches(4.8), Inches(0.3), Inches(8.2), Inches(6.9),
            WHITE, transparency=12)

# Canva design accent
add_accent(sl, "canva_design.png", W - Inches(4.5), Inches(3.8),
           height=Inches(3.5), opacity=20)

add_number_accent(sl, "06", Inches(5.0), Inches(0.4), RGBColor(0xD1, 0xD5, 0xDB))
section_badge(sl, Inches(9.5), Inches(0.5), "جواز صحي ودليل", "🛂")

add_text(sl, Inches(5.5), Inches(1.2), Inches(7.3), Inches(0.8),
         "شارك ملفك الصحي وابحث عن مقدمي الخدمة", size=28, bold=True, color=DARK)

# Passport section
tf = add_text(sl, Inches(5.5), Inches(2.1), Inches(7.3), Inches(0.5),
              "📱 جواز صحي رقمي", size=18, bold=True, color=DARK)
check_item(tf, "رمز QR يمسحه الطبيب بدون تحميل تطبيق")
check_item(tf, "تقرير PDF من ٤ صفحات عبر واتساب")
check_item(tf, "زر طوارئ SOS باتصال فوري")

# Directory section
tf2 = add_text(sl, Inches(5.5), Inches(4.3), Inches(7.3), Inches(0.5),
               "🏥 دليل شامل", size=18, bold=True, color=DARK)
check_item(tf2, "أطباء · مختبرات · صيدليات")
check_item(tf2, "بحث وترتيب وحجز مواعيد")
check_item(tf2, "مقارنة أسعار التحاليل")

add_phone(sl, "IMG_6643.PNG", Inches(0.8), Inches(0.6), h=Inches(3.5))
add_phone(sl, "IMG_6644.PNG", Inches(2.8), Inches(0.6), h=Inches(3.5))
add_phone(sl, "IMG_6633.PNG", Inches(1.5), Inches(4.2), h=Inches(3.0))

teal_bar(sl)
slide_footer(sl, "07")
add_transition(sl)


# ═══════════════════════════════════════════════════════════
#  SLIDE 8 — DOCTOR + PHARMACY + LAB
# ═══════════════════════════════════════════════════════════
sl = prs.slides.add_slide(prs.slide_layouts[6])
solid_bg(sl, WHITE)

# Subtle medical row accent at bottom
add_accent(sl, "medical_row.png", Inches(3), H - Inches(2.2),
           width=Inches(7), opacity=10)

add_number_accent(sl, "07", Inches(0.4), Inches(0.3))
section_badge(sl, Inches(9.5), Inches(0.5), "لكل الأدوار", "👥")

add_text(sl, Inches(3.0), Inches(1.2), Inches(9.8), Inches(0.8),
         "تطبيق واحد — طبيب · صيدلي · مختبر", size=32, bold=True, color=DARK)

# ─── Doctor column ───
add_overlay(sl, Inches(8.6), Inches(2.1), Inches(4.3), Inches(4.8),
            TEAL_BG, transparency=0)
tf = add_text(sl, Inches(8.6), Inches(2.2), Inches(4.3), Inches(0.5),
              "👨‍⚕️ الطبيب", size=20, bold=True, color=TEAL_D)
check_item(tf, "قائمة مرضى + رسائل فورية")
check_item(tf, "مسح QR + وصفات إلكترونية")
check_item(tf, "مكالمات صوتية ومرئية")
add_phone(sl, "IMG_6600.PNG", Inches(9.5), Inches(4.2), h=Inches(2.5))

# ─── Pharmacy column ───
add_overlay(sl, Inches(4.0), Inches(2.1), Inches(4.3), Inches(4.8),
            OFF_W, transparency=0)
tf2 = add_text(sl, Inches(4.0), Inches(2.2), Inches(4.3), Inches(0.5),
               "💊 الصيدلي", size=20, bold=True, color=TEAL_D)
check_item(tf2, "مخزون كامل + تتبع دفعات")
check_item(tf2, "تنبيهات انتهاء وطلبات واردة")
check_item(tf2, "تأكيد/رفض + توصيل")
add_phone(sl, "IMG_6669.PNG", Inches(5.0), Inches(4.2), h=Inches(2.5))

# ─── Lab column ───
add_overlay(sl, Inches(-0.3), Inches(2.1), Inches(4.0), Inches(4.8),
            TEAL_BG, transparency=0)
tf3 = add_text(sl, Inches(-0.1), Inches(2.2), Inches(3.8), Inches(0.5),
               "🔬 المختبر", size=20, bold=True, color=TEAL_D)
check_item(tf3, "إدخال نتائج في ملف المريض")
check_item(tf3, "طلبات فحص + قائمة أسعار")
check_item(tf3, "النتائج تصل المريض فوراً")
add_phone(sl, "IMG_6672.PNG", Inches(0.8), Inches(4.2), h=Inches(2.5))

teal_bar(sl)
slide_footer(sl, "08")
add_transition(sl)


# ═══════════════════════════════════════════════════════════
#  SLIDE 9 — ALL 50+ FEATURES
# ═══════════════════════════════════════════════════════════
sl = prs.slides.add_slide(prs.slide_layouts[6])
add_bg_image(sl, "bg_gradient_1.png")

add_overlay(sl, Inches(0.4), Inches(0.3), Inches(12.5), Inches(6.9),
            WHITE, transparency=10)

add_number_accent(sl, "08", Inches(0.6), Inches(0.4), RGBColor(0xD1, 0xD5, 0xDB))
section_badge(sl, Inches(9.5), Inches(0.5), "كل الميزات", "⭐")

add_text(sl, Inches(4.0), Inches(1.2), Inches(8.8), Inches(0.8),
         "أكثر من ٥٠ ميزة في تطبيق واحد", size=32, bold=True, color=DARK)

# Feature grid
features = [
    ("🤖", "محادثة ذكية"),   ("🎙️", "وضع صوتي"),     ("💊", "إدارة أدوية"),
    ("🔬", "ماسح تحاليل"),   ("🩺", "فحص أعراض"),     ("❤️", "علامات حيوية"),
    ("🥗", "تغذية"),         ("🏋️", "تمارين"),        ("😴", "تتبع نوم"),
    ("🌙", "صحة المرأة"),    ("🛂", "جواز صحي"),      ("👨‍👩‍👧", "صحة العائلة"),
    ("👨‍⚕️", "دليل أطباء"), ("📞", "مكالمات فيديو"), ("⌚", "Apple Health"),
    ("🚨", "طوارئ SOS"),     ("💉", "تطعيمات"),       ("🩸", "إدارة السكري"),
    ("💗", "إدارة الضغط"),   ("📱", "بدون إنترنت"),   ("🔒", "Face ID"),
]
cols = 7
for i, (emoji, label) in enumerate(features):
    col = i % cols
    row = i // cols
    x = Inches(11.8) - col * Inches(1.7)
    y = Inches(2.3) + row * Inches(0.72)
    shape = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(1.6), Inches(0.56))
    shape.fill.solid()
    shape.fill.fore_color.rgb = WHITE
    shape.line.color.rgb = RGBColor(0xE2, 0xE8, 0xF0)
    shape.line.width = Pt(1)
    tf = shape.text_frame
    tf.paragraphs[0].text = f"{emoji}  {label}"
    tf.paragraphs[0].font.size = Pt(11)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = DARK
    tf.paragraphs[0].font.name = "Tajawal"
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE

# More menu phones
add_phone(sl, "IMG_6627.PNG", Inches(0.8), Inches(4.8), h=Inches(2.4))
add_phone(sl, "IMG_6628.PNG", Inches(2.6), Inches(4.8), h=Inches(2.4))
add_phone(sl, "IMG_6629.PNG", Inches(4.4), Inches(4.8), h=Inches(2.4))

add_text(sl, Inches(6.5), Inches(5.8), Inches(6.0), Inches(0.6),
         "قائمة المزيد: كل الميزات مصنفة حسب الفئة مع بحث سريع",
         size=14, color=MID)

teal_bar(sl)
slide_footer(sl, "09")
add_transition(sl)


# ═══════════════════════════════════════════════════════════
#  SLIDE 10 — CTA / CALL TO ACTION
# ═══════════════════════════════════════════════════════════
sl = prs.slides.add_slide(prs.slide_layouts[6])

# Full-bleed capsule heart as background
add_bg_image(sl, "capsule_heart_red.png")

# Dark teal overlay for contrast
add_overlay(sl, 0, 0, W, H, RGBColor(0x04, 0x2F, 0x2E), transparency=28)

# Logo
add_logo(sl, Inches(6.0), Inches(0.6), Inches(1.0))

# CTA text
add_text(sl, Inches(2), Inches(2.0), Inches(9.3), Inches(1.0),
         "ابدأ رحلتك الصحية اليوم", size=42, bold=True, color=WHITE)

add_text(sl, Inches(2.5), Inches(3.1), Inches(8.3), Inches(0.8),
         "قريباً على App Store — مجاني بالكامل\nبدون إعلانات · بدون بيع بيانات",
         size=17, color=MINT)

# Contact boxes
box_x = Inches(3.5)
box_w = Inches(6.3)
for i, (label, value) in enumerate([
    ("البريد الإلكتروني", "contact@sihtak.com"),
    ("واتساب", "+44 744 048 7115"),
    ("الموقع", "sihtak.com"),
]):
    y = Inches(4.2) + i * Inches(0.82)
    shape = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, box_x, y, box_w, Inches(0.68))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0x0B, 0x7A, 0x70)
    shape.line.color.rgb = TEAL_L
    shape.line.width = Pt(1)
    _set_shape_transparency(shape, 25)
    tf = shape.text_frame
    tf.paragraphs[0].text = f"{label}:  {value}"
    tf.paragraphs[0].font.size = Pt(17)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].font.name = "Tajawal"
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE

# Stats
stats = ["٥٠+ ميزة", "٦ أدوار", "عربي + English", "ذكاء اصطناعي", "مجاني"]
sx = Inches(10.8)
for s in stats:
    w = Inches(2.0)
    shape = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx, Inches(6.8), w, Inches(0.38))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0x0B, 0x7A, 0x70)
    shape.line.fill.background()
    _set_shape_transparency(shape, 40)
    tf = shape.text_frame
    tf.paragraphs[0].text = s
    tf.paragraphs[0].font.size = Pt(10)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = MINT
    tf.paragraphs[0].font.name = "Tajawal"
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    sx -= Inches(2.1)

add_text(sl, Inches(3.5), H - Inches(0.5), Inches(6.3), Inches(0.3),
         "صنع بواسطة عدنان الرفاعي  ·  sihtak.com", size=10,
         color=RGBColor(0x5E, 0xEA, 0xD4), align=PP_ALIGN.CENTER)

# Teal bar (on top of dark bg)
s = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, H - Inches(0.06), W, Inches(0.06))
s.fill.solid()
s.fill.fore_color.rgb = TEAL_L
s.line.fill.background()
s.name = "!!TealBar"

slide_footer(sl, "10", dark=True)
add_transition(sl)


# ═══════════════════════════════════════════════════════════
#  SAVE
# ═══════════════════════════════════════════════════════════
prs.save(OUT)
print(f"Saved: {OUT}")
sz = os.path.getsize(OUT)
print(f"Size: {sz / 1024 / 1024:.1f} MB")
print("Tip: In PowerPoint, select all slides > Transitions > Morph for best effect!")
