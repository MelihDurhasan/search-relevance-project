# Arama Sonuçları Alakalılık Ölçümleme (Search Relevance) & LLM Judge

E-ticaret arama motoru sonuçlarının ESCI çerçevesinde değerlendirilmesi, nDCG/MRR metrikleri ve LLM Judge ile otomatik etiketleme.

> **Proje durumu:** `PROJECT_STATUS.md` dosyasında detaylı bilgi.

## Kurulum

```bash
pip install -r requirements.txt
```

## Çalıştırma

1. `.env` dosyasında `OPENAI_API_KEY` ayarlayın (veya `.env.example`'dan kopyalayıp doldurun).
2. Streamlit paneli:
   ```bash
   streamlit run streamlit_app.py
   ```
3. Docker ile:
   ```bash
   docker-compose up --build
   ```

## Veri

- **Varsayılan:** `data/rankings_expanded.csv` — 10 sorgu × 5 ürün = 50 satır.
- **Küçük demo:** `data/sample_rankings.csv` — 2 sorgu, 8 satır.
- **Amazon ESCI (Hugging Face):** [milistu/amazon-esci-data](https://huggingface.co/datasets/milistu/amazon-esci-data) — ~130K sorgu, 2.6M etiket.

### Amazon ESCI indirme (1000+ query)

```bash
pip install datasets
python scripts/load_amazon_esci.py --n_queries 1000
python scripts/load_amazon_esci.py --n_queries 5000 --locale us
python scripts/load_amazon_esci.py --n_queries 10000 -o data/amazon_10k.parquet
```

Oluşan Parquet panelde "Veri kaynağı"ndan seçilebilir.

## Özellikler

| Özellik | Açıklama |
|---------|----------|
| ESCI | Exact, Substitute, Complement, Irrelevant |
| nDCG@k, MRR | Ranking metrikleri |
| TOP-K Exact rate | TOP-1, TOP-3, TOP-5, TOP-10 |
| LLM Judge | Query + Product → ESCI (structured output) |
| Prompt V1/V2/V3 | Karşılaştırmalı deney |
| Precision, Recall | LLM vs manuel accuracy |
| Error Analysis | title_only, description_only, title+desc |
| Evidently | Classification report (HTML) |
| MLflow | Deney loglama |

## Proje Yapısı

```
├── streamlit_app.py      # Ana panel
├── src/
│   ├── esci.py           # ESCI etiketleri
│   ├── metrics.py        # nDCG, MRR, accuracy
│   ├── llm_judge.py      # LLM Judge (prompt V1/V2/V3)
│   ├── evaluation.py     # LLM vs ground truth
│   ├── evidently_report.py # Evidently entegrasyonu
│   └── mlflow_logger.py  # MLflow
├── data/
│   ├── rankings_expanded.csv  # 50 satır
│   └── sample_rankings.csv    # 8 satır
└── Dockerfile
```

## Referanslar

- [Amazon ESCI Data](https://github.com/amazon-science/esci-data)
- [Evidently AI](https://github.com/evidentlyai/evidently)
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
