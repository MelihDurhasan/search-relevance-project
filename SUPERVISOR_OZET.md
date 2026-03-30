# Arama Sonuçları Alakalılık Ölçümleme — Proje Özeti

**Konu:** Staj projesi  
**Proje:** Arama Sonuçları Alakalılık Ölçümleme ve LLM Judge Arayüz Geliştirme

---

## Projenin Amacı

E-ticaret aramalarında çıkan ürünlerin ne kadar alakalı olduğunu ölçüyoruz. Hem klasik metriklerle (nDCG, MRR) hem de LLM ile otomatik etiketleyerek. Sonuçta manuel etiketlemeye yakın bir LLM Judge hedefliyoruz; promptları iyileştirerek accuracy'yi artırmaya çalışıyoruz.

---

## Kullandığım Veriler

| Veri seti | Nereden | Kaç sorgu | Kaç satır |
|----------|---------|-----------|-----------|
| **Örnek (demo)** | Kendi oluşturduğum | 10 | 50 |
| **Amazon ESCI** | Hugging Face (milistu/amazon-esci-data) | 1.000 (örneklenen) | ~20.000 civarı |
| **Amazon ESCI (tam)** | [GitHub](https://github.com/amazon-science/esci-data) | ~130.000 | ~2.6 milyon |

Amazon verisini Hugging Face'ten indirdim. Train setinde **1.983.272** query-ürün çifti vardı. Bunun içinden **1.000 sorgu** örnekleyip products ile birleştirdim.

---

## Ne Yaptım?

### Değerlendirme (Metrikler)
- ESCI ile her query-ürün çiftini E/S/C/I diye etiketliyorum
- nDCG, MRR, TOP-K Exact oranı hesaplıyorum
- LLM'in verdiği etiketleri manuel etiketlerle karşılaştırıp accuracy, precision, recall çıkarıyorum

### LLM Judge
- Sorgu + ürün başlığı + açıklama veriyorum, LLM E/S/C/I döndürüyor
- Structured output kullanıyorum (Pydantic, JSON parse)
- Chain-of-Thought var, her cevapta kısa reasoning yazıyor
- 4 farklı prompt (V1, V2, V3, V4) deniyorum; hangisi daha iyi görmek için

### Prompt İyileştirmesi
- V1: Basit tanımlar → baseline
- V2: Detaylı açıklamalar → daha iyi
- V3: Sıkı kurallar → daha tutarlı
- V4: Substitute/Complement ayrımı netleştirildi → en güncel

### Özellik Setleri ve Shot'lar
- Sadece başlık, sadece açıklama, veya ikisini birlikte kullanabiliyorum
- Zero-shot, one-shot, few-shot deneyleri yapabiliyorum

### Hata Analizi
- LLM yanlış etiketlediğinde, o örneği title_only, description_only, title+description ile ayrı ayrı çalıştırıyorum
- Hatanın başlıktan mı açıklamadan mı geldiğini anlamaya çalışıyorum

### SQL
- Tüm eval sonuçları SQLite veritabanına kaydediliyor (eval_runs, eval_results tabloları)
- Geçmiş sonuçlar SQL sorguları ile takip edilebiliyor

### Arayüz ve Ek Araçlar
- **Streamlit paneli:** Tüm bunları yapabiliyorum: metrikler, LLM değerlendirme, prompt karşılaştırma, hata analizi, tablo görünümü
- **Evidently:** Classification raporu (HTML)
- **MLflow:** Deney loglama
- **Docker:** Projeyi Dockerize ettim

---

## Proje Yapısı

```
search-relevance-eval/
├── streamlit_app.py          # Ana dashboard paneli
├── notebooks/
│   └── supervisor_demo.ipynb # Tüm özellikleri gösteren demo notebook
├── src/
│   ├── esci.py               # ESCI etiketleri
│   ├── metrics.py            # nDCG, MRR, accuracy, precision, recall
│   ├── llm_judge.py          # LLM Judge (V1–V4 prompt, structured output)
│   ├── evaluation.py         # LLM vs ground truth karşılaştırma
│   ├── eval_db.py            # SQL (SQLite) eval geçmişi
│   ├── shopping_queries.py   # Amazon ESCI veri birleştirme
│   ├── llm_experiments.py    # Deney ızgarası (feature × shot)
│   ├── evidently_report.py   # Evidently entegrasyonu
│   └── mlflow_logger.py      # MLflow loglama
├── scripts/
│   ├── load_amazon_esci.py   # Amazon verisi indirme
│   └── run_accuracy_eval.py  # Toplu accuracy ölçümü
├── data/                     # CSV/Parquet veri dosyaları
├── reports/                  # Teknik rapor, eval sonuçları, SQLite DB
├── Dockerfile                # Docker
└── docker-compose.yml
```

---

## Tamamlanan Maddeler (Proje Tanımından)

| Beklenen Çıktı | Durum |
|----------------|-------|
| ESCI çerçevesi | ✓ Tamamlandı |
| nDCG, MRR metrikleri | ✓ Tamamlandı |
| TOP-K Exact rate | ✓ Tamamlandı |
| LLM Judge (otomatik etiketleme) | ✓ Tamamlandı |
| Prompt Engineering (V1–V4) | ✓ Tamamlandı |
| Accuracy, Precision, Recall | ✓ Tamamlandı |
| SQL | ✓ Tamamlandı |
| Streamlit Dashboard | ✓ Tamamlandı |
| Docker | ✓ Tamamlandı |
| Teknik analiz raporu | ✓ Tamamlandı |
| Evidently / MLflow | ✓ Tamamlandı |

---

## Nerede Çalıştırıyorum?

Jupyter sunucusunda (atlasg02) çalışıyor. `supervisor_demo.ipynb` notebook'u tüm özellikleri gösterir. Streamlit paneli için Terminal'den `streamlit run streamlit_app.py` çalıştırılır.

---

## Kısa Özet

Proje tanımındaki tüm maddeleri tamamladım: ESCI, nDCG, MRR, TOP-K, LLM Judge, structured output, zero/one/few-shot, chain-of-thought, farklı özellik setleri, prompt iyileştirme (V1→V4), SQL, Evidently, MLflow, Docker, Streamlit Dashboard ve teknik analiz raporu.
