# Jupyter'a Proje Aktarma ve Supervisor Demo Rehberi

## 1. Yerelden Jupyter sunucusuna aktarım

### Yöntem A: Git kullanıyorsanız

**Yerelde (Cursor/VS Code):**
```bash
cd c:\Users\mdurhasanhb\Documents\search-relevance-eval
git add .
git commit -m "V4 prompt, SQL eval_db, run_accuracy_eval, teknik rapor"
git push
```

**Jupyter sunucusunda (Terminal veya Notebook hücresinde):**
```bash
cd /data-storage/search/melih_durhasan/search-relevance-eval
git pull
```

### Yöntem B: Git yoksa — Manuel kopyalama

Aşağıdaki dosya/klasörleri Jupyter sunucusuna kopyalayın (scp, WinSCP, veya Jupyter File Upload):

| Kaynak (yerel) | Hedef (Jupyter) |
|----------------|-----------------|
| `scripts/run_accuracy_eval.py` | `scripts/` |
| `src/eval_db.py` | `src/` |
| `src/llm_judge.py` | `src/` |
| `streamlit_app.py` | proje kökü |
| `reports/TEKNIK_ANALIZ_RAPORU.md` | `reports/` |
| `notebooks/supervisor_demo.ipynb` | `notebooks/` |
| `run_accuracy_eval.bat` | proje kökü (opsiyonel) |

---

## 2. Jupyter'da ne çalıştırılacak?

### Seçenek 1: Supervisor Demo Notebook

`notebooks/supervisor_demo.ipynb` dosyasını açın ve hücreleri sırayla çalıştırın. Bu notebook:

- Veri yükleme
- nDCG, MRR metrikleri
- LLM Judge (tek örnek)
- Accuracy ölçümü (az satır)
- SQL: eval geçmişini okuma
- Streamlit'in nasıl açılacağı

### Seçenek 2: Streamlit paneli

Jupyter'dan **Terminal** açın (File → New → Terminal) ve:

```bash
cd /data-storage/search/melih_durhasan/search-relevance-eval
pip install -r requirements.txt   # gerekirse
streamlit run streamlit_app.py
```

Tarayıcıda açılan adresi supervisor’a gösterin (örn. `http://10.16.16.242:8501`).

### Seçenek 3: Accuracy eval script (terminal)

```bash
cd /data-storage/search/melih_durhasan/search-relevance-eval
python scripts/run_accuracy_eval.py --max_rows 20 --prompts v1 v2 v3 v4
```

`data/amazon_esci_1000q.parquet` yoksa önce:

```bash
python scripts/load_amazon_esci.py --n_queries 1000
```

---

## 3. .env (API anahtarı)

Jupyter sunucusunda da `.env` dosyası olmalı. `.env.example`'dan kopyalayıp `OPENAI_API_KEY` değerini doldurun:

```
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

---

## 4. Kontrol listesi (Supervisor öncesi)

- [ ] Dosyalar Jupyter sunucusuna aktarıldı
- [ ] `pip install -r requirements.txt` çalıştırıldı
- [ ] `.env` içinde `OPENAI_API_KEY` tanımlı
- [ ] `supervisor_demo.ipynb` veya Streamlit test edildi
- [ ] Varsa `data/amazon_esci_1000q.parquet` hazır
