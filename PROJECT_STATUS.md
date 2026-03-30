# Proje Durumu ve Bilgisi

## Projenin Amacı

**Arama Sonuçları Alakalılık Ölçümleme (Search Relevance) ve LLM Judge**

E-ticaret arama motoru sonuçlarının:
- **ESCI** çerçevesiyle değerlendirilmesi
- **nDCG, MRR** gibi metriklerle ölçülmesi
- **LLM** ile otomatik etiketleme (manuel etiketlere yakın mı?)

---

## Mevcut Durum

### Tamamlanan Özellikler

| Bileşen | Durum | Açıklama |
|---------|-------|----------|
| ESCI çerçevesi | Tamamlandı | E/S/C/I etiketleri, kazanç (0-3) |
| nDCG@k, MRR | Tamamlandı | Sıralama metrikleri |
| TOP-K Exact rate | Tamamlandı | TOP-1, 3, 5, 10 oranları |
| LLM Judge | Tamamlandı | Query + Product → ESCI, structured output |
| Prompt V1/V2/V3 | Tamamlandı | Karşılaştırmalı deney |
| Accuracy, Precision, Recall | Tamamlandı | LLM vs manuel |
| Error Analysis | Tamamlandı | title_only, description_only, title+desc |
| Evidently | Tamamlandı | Classification raporu |
| MLflow | Tamamlandı | Deney loglama |
| Streamlit panel | Tamamlandı | Tüm sekmeler çalışır |
| Docker | Tamamlandı | Dockerfile + docker-compose |

### Veri

| Dosya | Sorgu | Satır |
|-------|-------|-------|
| sample_rankings.csv | 2 | 8 |
| rankings_expanded.csv | 10 | 50 |
| rankings_500q.csv | 500 | 2500 | *(script ile oluşturulur)* |
| Amazon ESCI | ~130K | ~2.6M | *(Hugging Face'den indirilir)* |

**Varsayılan:** 50 satır (10 sorgu). Daha fazla veri için script çalıştırılır veya Amazon indirilir.

---

## Proje Akışı

```
Veri (CSV/Parquet)
       ↓
  ESCI etiketleri (manuel) + Sorgu + Ürün
       ↓
  ┌─────────────────────────────────────────┐
  │ 1. nDCG, MRR, TOP-K hesapla (metrikler)  │
  │ 2. LLM'a gönder: Query + Product → ESCI   │
  │ 3. LLM tahmini vs manuel → Accuracy      │
  │ 4. Prompt V1/V2/V3 karşılaştır           │
  │ 5. Hata analizi (yanlış olanlarda neden?)│
  └─────────────────────────────────────────┘
       ↓
  Rapor: Accuracy, Precision, Recall, Confusion matrix
```

---

## Eksik / Yapılacaklar

1. **Gerçek veri ile ölçüm**
   - Prompt V1/V2/V3'ün gerçek accuracy değerleri henüz ölçülmedi (API ile çalıştırılmalı).
   - Öneri: 30–50 satır üzerinde "Değerlendir ve metrikleri hesapla" ve "Promtları karşılaştır" çalıştır.

2. **500/1000 query verisi**
   - `python scripts/generate_1000_queries.py -n 500` veya `run_data_gen.bat` ile oluşturulur.
   - Oluşmazsa proje 50 satırla çalışır (demo için yeterli).

3. **Teknik analiz raporu**
   - Proje tanımında "iyileştirme önerileri" raporu var; ayrı doküman oluşturulabilir.

---

## Nasıl Çalıştırılır

```bash
# 1. Bağımlılıklar
pip install -r requirements.txt

# 2. .env dosyasında OPENAI_API_KEY (LLM için)

# 3. Panel
streamlit run streamlit_app.py

# 4. (İsteğe bağlı) 500 sorgu verisi
python scripts/generate_1000_queries.py -n 500
```

---

## Proje Yapısı

```
search-relevance-eval/
├── streamlit_app.py       # Ana panel (tek giriş noktası)
├── src/
│   ├── esci.py            # ESCI sınıfları
│   ├── metrics.py         # nDCG, MRR, accuracy, precision, recall
│   ├── llm_judge.py       # LLM çağrısı, prompt V1/V2/V3
│   ├── evaluation.py      # LLM vs ground truth değerlendirme
│   ├── evidently_report.py
│   └── mlflow_logger.py
├── data/
│   ├── sample_rankings.csv    # 8 satır
│   └── rankings_expanded.csv # 50 satır
├── scripts/
│   ├── generate_1000_queries.py  # 500/1000 sorgu üret
│   └── load_amazon_esci.py       # Amazon verisi indir
└── experiments/literature_notes.md # Literatür
```

---

## Özet

Proje **tamamlanmış ve çalışır durumda**. Tüm supervisor istekleri (ESCI, nDCG, MRR, TOP-K, LLM Judge, prompt karşılaştırma, accuracy, error analysis, Evidently, MLflow) uygulanmıştır.

Eksik olan: **gerçek API ile accuracy ölçümü** (Streamlit’te butonlara tıklanarak yapılır) ve isteğe bağlı olarak **500 sorguluk veri oluşturulması**.
