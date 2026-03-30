"""Supervisor sunumu: Search Relevance Eval + LLM Judge — PowerPoint (.pptx).

Bu dosya proje kökündedir; `scripts` klasörü boş / eksik olsa bile Colab'a tek dosya
olarak yüklenebilir. Çıktı: Sunum_Search_Relevance.pptx
"""
import sys, os


def _project_root() -> str:
    """Proje kökü; Colab'da exec() ile çalışınca __file__ olmayabilir — o zaman cwd kullanılır."""
    try:
        d = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.getcwd()
    if os.path.basename(d) == "scripts":
        return os.path.dirname(d)
    return d


ROOT = _project_root()
# Colab: os.environ["SUNUM_OUT"] = "/content/Sunum_Search_Relevance.pptx"
OUT = os.environ.get("SUNUM_OUT", os.path.join(ROOT, "Sunum_Search_Relevance.pptx"))

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
except ImportError:
    sys.exit("python-pptx not installed. Run: pip install python-pptx")

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

BG = RGBColor(0x1A, 0x1A, 0x2E)
ACCENT = RGBColor(0x00, 0xD2, 0xFF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xCC, 0xCC, 0xCC)
ORANGE = RGBColor(0xFF, 0xA5, 0x00)


def bg(slide):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG


def txt(slide, l, t, w, h, text, sz=18, b=False, c=WHITE, a=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = text
    p.font.size = Pt(sz); p.font.bold = b; p.font.color.rgb = c; p.alignment = a
    return tf


def bullets(slide, items, l=0.8, t=2.2, w=11.5, sz=20, c=LIGHT):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(5))
    tf = tb.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item; p.font.size = Pt(sz); p.font.color.rgb = c; p.space_after = Pt(8)
    return tf


def tbar(slide, title, sub=""):
    txt(slide, 0.6, 0.4, 12, 0.8, title, sz=36, b=True, c=ACCENT)
    if sub:
        txt(slide, 0.6, 1.2, 12, 0.5, sub, sz=18, c=LIGHT)


def table(slide, data, l=1.0, t=2.5, w=11.3, rh=0.45):
    rows, cols = len(data), len(data[0])
    sh = slide.shapes.add_table(rows, cols, Inches(l), Inches(t), Inches(w), Inches(rows * rh))
    tbl = sh.table
    for r in range(rows):
        for cc in range(cols):
            cell = tbl.cell(r, cc); cell.text = str(data[r][cc])
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(14)
                p.font.color.rgb = ACCENT if r == 0 else WHITE
                p.font.bold = (r == 0)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0x0D, 0x0D, 0x2B) if r == 0 else RGBColor(0x22, 0x22, 0x44)
    return tbl


# ═══════ SLAYT 1: KAPAK ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
txt(s, 0.5, 1.5, 12.3, 1.2,
    "Arama Sonuçları Alakalılık Ölçümleme\nve LLM Judge Otomatik Değerlendirme",
    sz=40, b=True, c=WHITE, a=PP_ALIGN.CENTER)
txt(s, 0.5, 3.5, 12.3, 0.6,
    "Search Relevance Evaluation & Automated LLM Judgement System",
    sz=22, c=ACCENT, a=PP_ALIGN.CENTER)
txt(s, 0.5, 5.0, 12.3, 0.5,
    "Melih Durhasan  |  Staj Projesi  |  2025", sz=18, c=LIGHT, a=PP_ALIGN.CENTER)
txt(s, 0.5, 5.8, 12.3, 0.5,
    "Python  •  OpenAI GPT-4o  •  Streamlit  •  Docker  •  Pandas  •  Plotly",
    sz=14, c=LIGHT, a=PP_ALIGN.CENTER)

# ═══════ SLAYT 2: PROBLEM & AMAÇ ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "Problem ve Amaç")
bullets(s, [
    "E-ticaret arama motorları milyonlarca sorgu–ürün eşlemesi üretiyor",
    "Bu eşlemelerin kalitesi (alakalılık) kullanıcı deneyimini doğrudan etkiler",
    "Manuel değerlendirme: yavaş, pahalı, ölçeklenmiyor",
    "",
    "Amaç:",
    "  1. Matematiksel metriklerle (nDCG, MRR) arama kalitesini ölçmek",
    "  2. LLM (GPT-4o) ile insan değerlendirmesini otomatize etmek",
    "  3. Prompt engineering ile LLM doğruluğunu artırmak",
    "  4. İnteraktif Streamlit paneli ile tüm süreci görselleştirmek",
])

# ═══════ SLAYT 3: ESCI FRAMEWORK ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "ESCI Framework", "Amazon Shopping Queries Dataset — 4 sınıflı alakalılık")
table(s, [
    ["Sınıf", "Tanım", "Örnek"],
    ["Exact (E)", "Ürün, arama niyetini birebir karşılıyor", '"koşu ayakkabısı" → Nike Air Max Running'],
    ["Substitute (S)", "Farklı ürün ama aynı ihtiyaç", '"iPad" → Samsung Galaxy Tab'],
    ["Complement (C)", "İlgili aksesuar / eklenti", '"laptop" → Laptop Çantası'],
    ["Irrelevant (I)", "Hiç alakası yok", '"kulaklık" → Mutfak Havlusu'],
], t=2.3, rh=0.65)
txt(s, 1.0, 5.8, 11, 0.5,
    "Kaynak: Amazon ESCI — github.com/amazon-science/esci-data", sz=13, c=LIGHT)

# ═══════ SLAYT 4: MATEMATİKSEL METRİKLER ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "Matematiksel Metrikler", "Arama kalitesini sayısal olarak ölçmek")
bullets(s, [
    "nDCG (Normalized Discounted Cumulative Gain)",
    "  • Sıralı sonuçlarda üst sıradaki alakalı ürünleri ödüllendirir",
    "  • DCG = Σ (2^rel - 1) / log₂(rank + 1)  →  nDCG = DCG / idealDCG",
    "",
    "MRR (Mean Reciprocal Rank)",
    "  • İlk doğru sonucun sırası  →  1/rank ortalaması",
    "",
    "TOP-K Exact Rate",
    "  • İlk K sonuçta Exact etiketli ürün var mı? (k = 1, 3, 5, 10)",
    "",
    "Accuracy, Precision, Recall, F1-macro",
    "  • LLM tahminlerinin ground truth ile uyumu",
], sz=18)

# ═══════ SLAYT 5: LLM JUDGE SİSTEMİ ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "LLM Judge — Otomatik Değerlendirme Sistemi")
bullets(s, [
    "Akış:  Sorgu + Ürün bilgisi  →  System Prompt  →  GPT-4o  →  JSON çıktı",
    "",
    "Structured Output (Pydantic):",
    "  • label: Exact / Substitute / Complement / Irrelevant",
    "  • reasoning: Adım adım açıklama (Chain of Thought)",
    "  • confidence: 0.0 – 1.0 güven skoru",
    "",
    "Chain of Thought (CoT):",
    "  • Model etiket seçmeden ÖNCE düşünce sürecini yazıyor",
    '  • "(1) Sorgu niyeti, (2) Ürün tipi, (3) Eşleşme analizi, (4) Etiket"',
    "",
    "Neden Structured Output?",
    "  • JSON şeması zorunlu → parse hatası yok, Pydantic validasyonu",
    "  • temperature=0 → deterministik, tekrarlanabilir sonuçlar",
], sz=17)

# ═══════ SLAYT 6: PROMPT ENGİNEERİNG V1→V4 ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "Prompt Engineering — V1 → V4 Stratejisi",
     "Her adımda prompt kalitesi, bilgi düzeyi ve örnek sayısı artırıldı")
table(s, [
    ["Versiyon", "Strateji", "Ürün Bilgisi", "Shot Mode", "Beklenen Sorun"],
    ["V1", "Zayıf tanım (markaya takılır)", "Sadece başlık", "Zero-shot", "Farklı marka=Substitute der"],
    ["V2", "Doğru ESCI tanımları", "Sadece başlık", "Zero-shot", "S/C karışabilir"],
    ["V3", "Detaylı tanım + kritik ayrımlar", "Başlık + Açıklama", "One-shot (1 örnek)", "Nadir edge case"],
    ["V4", "Karar ağacı + sık hatalar", "Başlık + Açıklama", "Few-shot (3 örnek)", "Minimum hata"],
], t=2.5, rh=0.6)
txt(s, 1.0, 5.8, 11, 0.7,
    "Feature Modes: title_only → sadece başlık  |  title_description → başlık + ürün açıklaması\n"
    "Shot Modes: Zero-shot (örnek yok) → One-shot (1 örnek) → Few-shot (3 örnek)",
    sz=14, c=LIGHT)

# ═══════ SLAYT 7: PROMPT SONUÇLARI ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "Prompt İyileştirme Sonuçları",
     "V1'den V4'e accuracy ve F1 artışı — Streamlit panelinden")
bullets(s, [
    "V1 (baseline): Düşük accuracy — markaya takılan tanım + sadece başlık + zero-shot",
    "V2: Doğru tanımlar → ilk iyileşme",
    "V3: Açıklama eklendi + one-shot örnek → belirgin artış",
    "V4: Karar ağacı + few-shot → en yüksek accuracy ve F1",
    "",
    "Exact hariç sınıflarda (Substitute, Complement, Irrelevant) fark daha belirgin",
    "",
    "Önemli: V1 → V4 arasında 3 boyut değişiyor:",
    "  1) Prompt kalitesi (tanımlar, ayrımlar, karar ağacı)",
    "  2) Feature mode (title_only → title_description)",
    "  3) Shot mode (zero → one → few shot)",
    "",
    "[ Streamlit'ten accuracy bar chart ve çizgi grafik SS ekleyin ]",
], sz=17)

# ═══════ SLAYT 8: MODEL KARŞILAŞTIRMA ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "Model Karşılaştırma — nano / mini / gpt",
     "Aynı veri, aynı prompt ile 3 model katmanı + tahmini maliyet")
table(s, [
    ["Katman", "Model", "Input $/1M token", "Output $/1M token", "Kullanım"],
    ["nano", "gpt-4o-mini", "$0.15", "$0.60", "Hızlı, ucuz, büyük batch"],
    ["mini", "gpt-4o", "$2.50", "$10.00", "Dengeli performans"],
    ["gpt", "gpt-4o", "$2.50", "$10.00", "En yüksek doğruluk"],
], t=2.3, rh=0.55)
bullets(s, [
    "",
    "",
    "",
    "Verimlilik = Accuracy / Maliyet ($) — en yüksek olan model en verimli",
    "Maliyet tahmini: ortalama ~800 input + ~150 output token/çağrı",
    "",
    "[ Streamlit'ten accuracy bar + maliyet scatter SS ekleyin ]",
], t=4.5, sz=17)

# ═══════ SLAYT 9: SORGU BAZLI ÖLÇÜM ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "Sorgu Bazlı Değerlendirme",
     "Satır yerine sorgu odaklı metrikler — daha anlamlı ölçüm")
bullets(s, [
    "Problem: Satır bazlı accuracy'de Exact ağırlıklı veri sonuçları şişirebilir",
    "",
    "Çözüm: Çok-etiketli sorgu filtresi",
    "  • Aynı sorguda en az 2 farklı ESCI etiketi olan sorgular seçilir",
    "  • Tek etiketli (kolay) sorgular çıkarılır",
    "  • Her sorgu için: doğru tahmin / toplam ürün → sorgu accuracy",
    "  • Tüm sorguların ortalaması: Mean Query Accuracy",
    "",
    "Ek metrikler:",
    "  • Accuracy (Exact hariç) — S/C/I satırlarında doğruluk",
    "  • F1-macro (Exact hariç) — Substitute, Complement, Irrelevant F1 ortalaması",
    "  • Confusion Matrix: satır yüzdeleri ile",
], sz=17)

# ═══════ SLAYT 10: ERROR ANALYSİS ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "Error Analysis", "Hata kaynağı: başlık mı, açıklama mı, ikisi mi?")
bullets(s, [
    "Aynı sorgu–ürün çifti, 3 farklı feature mode ile değerlendirilir:",
    "",
    "  title_only       → Modele sadece ürün başlığı veriliyor",
    "  description_only  → Modele sadece ürün açıklaması veriliyor",
    "  title_description → İkisi birden",
    "",
    "Sonuçta:",
    "  • Üçü de doğru → model bu örneği anlıyor ✓",
    "  • Sadece başlıkla yanlış → başlık yanıltıcı / eksik",
    "  • Açıklama ekleyince düzeliyor → description ek bağlam sağlıyor",
    "",
    "Tab 2'de toplu accuracy sonrası yalnızca YANLIŞ tahminler filtrelenebilir",
], sz=17)

# ═══════ SLAYT 11: TEKNOLOJİ STACK ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "Teknoloji ve Araçlar")
table(s, [
    ["Kategori", "Araç", "Kullanım"],
    ["Dil", "Python 3.11+", "Tüm backend mantığı"],
    ["LLM", "OpenAI GPT-4o / GPT-4o-mini", "Otomatik ESCI etiketleme (API)"],
    ["Structured Output", "Pydantic + JSON Schema", "LLM çıktısını şemaya zorla"],
    ["Dashboard", "Streamlit + Plotly", "İnteraktif görselleştirme paneli"],
    ["Veri", "Pandas, NumPy, PyArrow", "Veri işleme, parquet okuma"],
    ["Veritabanı", "SQLite", "Eval koşu geçmişi loglama"],
    ["Deployment", "Docker + docker-compose", "Tek komutla konteyner çalıştırma"],
], t=2.0, rh=0.55)

# ═══════ SLAYT 12: DOCKER & DEPLOYMENT ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "Docker ile Deployment", "Tek komutla çalıştırma")
bullets(s, [
    "Dockerfile:",
    "  • Python 3.11 slim base image",
    "  • requirements.txt ile tüm bağımlılıklar",
    "  • Streamlit port 8501 expose",
    "",
    "docker-compose.yml:",
    "  • Ortam değişkenleri (.env) ile API key yönetimi",
    "  • Volume mount ile veri kalıcılığı",
    "",
    "Çalıştırma:",
    "  $ docker-compose up --build",
    "  → http://localhost:8501 adresinde panel hazır",
    "",
    "Alternatif: JupyterHub üzerinden Streamlit çalıştırma (sunucu ortamı)",
], sz=18)

# ═══════ SLAYT 13: STREAMLIT PANELİ ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "Streamlit Dashboard — Sekmeler")
table(s, [
    ["Sekme", "İçerik"],
    ["TOP-K & nDCG", "Exact rate @k, nDCG@k, MRR — sorgu bazlı tablo"],
    ["LLM Judge & Accuracy", "Tek sorgu test + toplu accuracy (satır/sorgu modu)"],
    ["Prompt & Model Kıyası", "V1→V4 prompt + nano/mini/gpt model karşılaştırma"],
    ["Error Analysis", "3 feature mode ile hata teşhisi"],
    ["DataFrame", "Ham veri, sınıf dağılımı, sorgu filtresi"],
], t=2.3, rh=0.6)
txt(s, 1.0, 6.0, 11, 0.5,
    "[ Streamlit panelinin genel ekran görüntüsünü ekleyin ]", sz=15, c=ORANGE)

# ═══════ SLAYT 14: CANLI DEMO ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
txt(s, 0.5, 2.0, 12.3, 1.0, "Canlı Demo",
    sz=48, b=True, c=ACCENT, a=PP_ALIGN.CENTER)
txt(s, 0.5, 3.5, 12.3, 0.8,
    "Streamlit paneli üzerinden canlı gösterim",
    sz=28, c=WHITE, a=PP_ALIGN.CENTER)
txt(s, 0.5, 4.8, 12.3, 0.5,
    "V1→V4 prompt karşılaştırma  •  nano/mini/gpt model kıyası  •  Error Analysis",
    sz=20, c=LIGHT, a=PP_ALIGN.CENTER)

# ═══════ SLAYT 15: SONUÇ & KAZANIMLAR ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tbar(s, "Sonuç ve Kazanımlar")
bullets(s, [
    "Proje çıktıları:",
    "  ✓  nDCG, MRR, TOP-K ile arama kalitesi ölçümü",
    "  ✓  LLM Judge ile otomatik ESCI etiketleme (insan değerlendirmesine yakın)",
    "  ✓  Prompt engineering ile V1→V4 doğruluk artışı gösterildi",
    "  ✓  nano/mini/gpt model + maliyet karşılaştırması yapıldı",
    "  ✓  Streamlit interaktif dashboard ile görselleştirme",
    "  ✓  Docker ile deployment-ready altyapı",
    "",
    "Kişisel kazanımlar:",
    "  • LLM API entegrasyonu, Structured Output, Chain of Thought",
    "  • Prompt engineering: zero-shot → few-shot, karar ağacı tasarımı",
    "  • Veri bilimi metrikleri: nDCG, MRR, F1-macro, confusion matrix",
    "  • Full-stack: Python → Streamlit → Docker pipeline",
], sz=17)

# ═══════ SLAYT 16: TEŞEKKÜR ═══════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
txt(s, 0.5, 2.5, 12.3, 1.0, "Teşekkürler",
    sz=52, b=True, c=ACCENT, a=PP_ALIGN.CENTER)
txt(s, 0.5, 4.0, 12.3, 0.6, "Sorularınız?",
    sz=28, c=WHITE, a=PP_ALIGN.CENTER)
txt(s, 0.5, 5.2, 12.3, 0.5, "Melih Durhasan  •  Staj Projesi",
    sz=18, c=LIGHT, a=PP_ALIGN.CENTER)

# ═══════ KAYDET ═══════
prs.save(OUT)
print(f"OK — {len(prs.slides)} slayt → {OUT}")
print(f"Boyut: {os.path.getsize(OUT):,} byte")

try:
    from google.colab import files  # type: ignore

    files.download(OUT)
    print("Colab: dosya indirildi (veya indirme penceresi açıldı).")
except Exception:
    pass
