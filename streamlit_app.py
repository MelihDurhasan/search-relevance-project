"""Streamlit dashboard: ESCI, nDCG, MRR, TOP-K, LLM Judge, prompt comparison, model comparison."""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "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")
os.environ.setdefault("OPENAI_MODEL", "gpt-4o-mini")
os.environ.setdefault("OPENAI_MODEL_NANO", "gpt-4o-mini")
os.environ.setdefault("OPENAI_MODEL_MINI", "gpt-4o")
os.environ.setdefault("OPENAI_MODEL_GPT", "gpt-4o")

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.evaluation import subset_df_multi_label_queries
from src.esci import LABEL_NAMES, parse_esci
from src.metrics import (
    _normalize_esci,
    confusion_matrix_dataframe,
    confusion_matrix_row_percent,
    mean_mrr,
    ndcg_at_k,
    ndcg_at_k_multi,
    top_k_exact_rate,
)
from src.shopping_queries import (
    ensure_query_text_column,
    ensure_rank_column,
    filter_task1_small,
    read_table,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_CSV = DATA_DIR / "rankings_expanded.csv"
if not DEFAULT_CSV.exists():
    DEFAULT_CSV = DATA_DIR / "sample_rankings.csv"

st.set_page_config(page_title="Arama Alakalılık Paneli", layout="wide")
st.title("Arama Sonuçları — nDCG / MRR / TOP-K / LLM Judge")
st.caption(
    "[Amazon ESCI](https://github.com/amazon-science/esci-data) verisi ile arama sonuçlarının "
    "alakalılık ölçümü. Sidebar'dan veri seçin veya Amazon ESCI indirin."
)


def frame_to_gains(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "esci_gain" in out.columns:
        out["gain"] = out["esci_gain"].astype(int)
    elif "esci_label" in out.columns:
        out["gain"] = out["esci_label"].map(lambda x: parse_esci(x))
    else:
        raise ValueError("CSV needs esci_label or esci_gain column")
    return out


def compute_per_query(df: pd.DataFrame, k: int | None) -> pd.DataFrame:
    rows = []
    for qid, g in df.groupby("query_id", sort=False):
        g = g.sort_values("rank")
        rel = g["gain"].to_numpy()
        nd = ndcg_at_k(rel, k=k)
        binary = (rel >= 2).astype(int)
        mr = mean_mrr([binary.tolist()])
        rows.append({
            "query_id": qid,
            "query_text": g["query_text"].iloc[0] if "query_text" in g.columns else "",
            "nDCG": nd,
            "MRR": mr,
            "num_results": len(g),
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.subheader("Veri kaynağı")

    # Mevcut veri dosyalarını listele
    data_options: list[str] = []
    amazon_files = sorted(
        list(DATA_DIR.glob("amazon_esci_*.parquet")) if DATA_DIR.exists() else [],
        key=lambda x: -int("".join(filter(str.isdigit, x.name)) or "0"),
    )
    for af in amazon_files:
        nq = "".join(filter(str.isdigit, af.stem))
        data_options.append(af.name)

    data_options.append("Varsayılan (50 satır)")
    data_options.append("Küçük demo (8 satır)")

    for n in (500, 1000):
        p = DATA_DIR / f"rankings_{n}q.csv"
        if p.exists():
            data_options.append(f"{n} sorgu ({n * 5} satır)")

    data_choice = st.selectbox(
        "Veri seç",
        list(dict.fromkeys(data_options)),
        format_func=lambda x: (
            x.replace(".parquet", "").replace("_", " ").replace("amazon esci ", "Amazon ESCI — ")
            if x.endswith(".parquet")
            else x
        ),
    )

    if not amazon_files:
        st.warning("Amazon ESCI verisi bulunamadı. Aşağıdan indirin.")

    with st.expander("Amazon ESCI indir", expanded=not bool(amazon_files)):
        st.caption("Hugging Face'den gerçek Amazon veri seti. 1000 sorgu = ~5000 satır.")
        n_q_dl = st.selectbox("Sorgu sayısı", [100, 250, 500, 1000], index=3)
        if st.button("Amazon verisini indir"):
            with st.spinner(f"{n_q_dl} sorgu indiriliyor (birkaç dakika sürebilir)..."):
                try:
                    import sys
                    sys.path.insert(0, str(Path(__file__).resolve().parent))
                    from scripts.load_amazon_esci import load_amazon_esci
                    DATA_DIR.mkdir(parents=True, exist_ok=True)
                    dl_df = load_amazon_esci(n_queries=int(n_q_dl))
                    out_path = DATA_DIR / f"amazon_esci_{n_q_dl}q.parquet"
                    dl_df.to_parquet(out_path, index=False)
                    st.success(f"{out_path.name} — {len(dl_df)} satır indirildi!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"İndirme hatası: {ex}")

    task1_small = st.checkbox("Yalnız Task 1 small_version", value=False)
    uploaded = st.file_uploader("CSV/Parquet yükle", type=["csv", "parquet"])

    st.divider()
    st.subheader("LLM ayarları")
    use_sample = st.checkbox("1 rastgele sorgu, top 10", value=False)
    sample_seed = st.number_input("Seed", value=42, min_value=0) if use_sample else 42

    st.divider()
    st.markdown("**ESCI** | E=Exact, S=Substitute, C=Complement, I=Irrelevant")

# ═══════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════
if uploaded:
    suf = Path(uploaded.name).suffix.lower()
    raw = read_table(uploaded, suffix=suf)
elif data_choice.endswith(".parquet"):
    am_path = DATA_DIR / data_choice
    raw = read_table(am_path) if am_path.exists() else read_table(DEFAULT_CSV)
elif "Küçük" in data_choice:
    raw = read_table(DATA_DIR / "sample_rankings.csv")
elif "sorgu" in data_choice:
    n = int(re.search(r"\d+", data_choice).group())
    p = DATA_DIR / f"rankings_{n}q.csv"
    raw = read_table(p) if p.exists() else read_table(DEFAULT_CSV)
else:
    raw = read_table(DEFAULT_CSV)

if task1_small and "small_version" in raw.columns:
    raw = filter_task1_small(raw)

if use_sample:
    from src.evaluation import sample_one_query_top_n
    raw = sample_one_query_top_n(raw, n=10, seed=sample_seed)
    if raw.empty:
        st.warning("Örnek veri boş.")
        st.stop()

if "query_id" not in raw.columns:
    st.error("query_id sütunu gerekli.")
    st.stop()

if "esci_label" not in raw.columns and "esci_gain" not in raw.columns:
    st.error("esci_label veya esci_gain gerekli.")
    st.stop()

raw = ensure_rank_column(raw)
raw = ensure_query_text_column(raw)
df = frame_to_gains(raw)
st.session_state["data_label"] = uploaded.name if uploaded is not None else data_choice

n_rows = len(df)
n_queries = df["query_id"].nunique()
st.sidebar.info(f"Yüklü: **{n_rows}** satır, **{n_queries}** sorgu")

# ═══════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "TOP-K & nDCG",
    "LLM Judge & Accuracy",
    "Prompt & Model Kıyası",
    "Error Analysis",
    "DataFrame",
])

# ═══════════════════════════════════════════════════════════════
# TAB 1: TOP-K & nDCG
# ═══════════════════════════════════════════════════════════════
with tab1:
    st.subheader("TOP-K Exact rate & nDCG@k")
    k_vals = (1, 3, 4, 5, 10)
    exact_rates = top_k_exact_rate(df, label_col="esci_label", k_values=k_vals)
    ndcg_vals = ndcg_at_k_multi(df, gain_col="gain", k_values=k_vals)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Exact in TOP-K**")
        ex_df = pd.DataFrame([{"k": f"TOP-{k}", "Exact rate": round(exact_rates[k], 4)} for k in k_vals])
        st.dataframe(ex_df, use_container_width=True)
        st.plotly_chart(px.bar(ex_df, x="k", y="Exact rate", title="Exact@k"), use_container_width=True)
    with col2:
        st.markdown("**nDCG@k** (ortalama)")
        nd_df = pd.DataFrame([{"k": f"nDCG@{k}", "nDCG": round(ndcg_vals[k], 4)} for k in k_vals])
        st.dataframe(nd_df, use_container_width=True)
        st.plotly_chart(px.bar(nd_df, x="k", y="nDCG", title="nDCG@k"), use_container_width=True)

    per_q = compute_per_query(df, k=4)
    st.dataframe(per_q, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TAB 2: LLM Judge & Accuracy
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.subheader("LLM Judge — Tek sorgu test")
    _default_desc = str(raw["product_description"].iloc[0]) if "product_description" in raw.columns else ""
    col_a, col_b = st.columns(2)
    with col_a:
        q_test = st.text_input("Sorgu", value=str(raw["query_text"].iloc[0]) if "query_text" in raw.columns else "")
        title_test = st.text_input("Ürün başlığı", value=str(raw["product_title"].iloc[0]) if "product_title" in raw.columns else "")
        prompt_ver = st.selectbox("Prompt", ["v1", "v2", "v3", "v4"],
                                  format_func=lambda x: {"v1": "V1 (baseline)", "v2": "V2", "v3": "V3", "v4": "V4 (en iyi)"}[x])
    with col_b:
        feat_mode = st.selectbox("Özellik", ["title_description", "title_only", "description_only"],
                                 format_func=lambda x: {"title_only": "Sadece başlık", "description_only": "Sadece açıklama", "title_description": "Başlık + açıklama"}[x])
        shot_mode = st.selectbox("Shot", ["zero_shot", "one_shot", "few_shot"],
                                 format_func=lambda x: {"zero_shot": "Zero-shot", "one_shot": "One-shot", "few_shot": "Few-shot"}[x])
    desc_test = st.text_area("Ürün açıklaması", value=_default_desc, height=80)

    if st.button("LLM ile değerlendir"):
        from src.llm_judge import judge_query_product
        try:
            with st.spinner("LLM çağrılıyor..."):
                j = judge_query_product(q_test, title_test, desc_test, feature_mode=feat_mode, shot_mode=shot_mode, prompt_version=prompt_ver)
            st.success(f"**{j.label}** (güven: {j.confidence:.2f})")
            with st.expander("Reasoning (CoT)", expanded=True):
                st.write(j.reasoning)
        except Exception as e:
            st.error(str(e))

    st.divider()
    st.subheader("Toplu LLM vs Ground Truth")
    st.caption(
        "**Sorgu modu:** Aynı sorguda tek ESCI etiketi olanları atlayıp yalnızca karışık sorgularla "
        "ölçüm (supervisor önerisi). **Satır modu:** Verinin en üstten N satırı."
    )
    eval_mode = st.radio(
        "Ölçüm",
        ["Satır (üstten N satır)", "Sorgu (N sorgu — birden fazla etiketli sorgular)"],
        horizontal=True,
        key="t2_eval_mode",
    )
    if eval_mode.startswith("Satır"):
        eval_rows = st.number_input("Satır sayısı", min_value=1, max_value=min(100, n_rows), value=min(15, n_rows), key="t2_nrows")
        max_q = None
    else:
        eval_rows = 15
        max_q = st.number_input(
            "Sorgu sayısı (çok etiketli)",
            min_value=1,
            max_value=min(100, raw["query_id"].nunique()) if "query_id" in raw.columns else 20,
            value=min(20, raw["query_id"].nunique()) if "query_id" in raw.columns else 10,
            key="t2_nqueries",
            help="Aynı sorguda en az 2 farklı ground truth etiketi olan sorgular sayılır.",
        )
        ex_sl = st.checkbox("Tek etiketli sorguları çıkar", value=True, key="t2_ex_sl")

    if st.button("Accuracy hesapla"):
        from src.evaluation import evaluate_llm_on_dataframe
        try:
            if eval_mode.startswith("Satır"):
                with st.spinner(f"{eval_rows} satır değerlendiriliyor..."):
                    ev_df, metrics = evaluate_llm_on_dataframe(
                        raw, prompt_version=prompt_ver, feature_mode=feat_mode,
                        shot_mode=shot_mode, max_rows=int(eval_rows), temperature=0.0,
                    )
            else:
                with st.spinner(f"En fazla {max_q} çok-etiketli sorgu değerlendiriliyor..."):
                    ev_df, metrics = evaluate_llm_on_dataframe(
                        raw, prompt_version=prompt_ver, feature_mode=feat_mode,
                        shot_mode=shot_mode, max_queries=int(max_q),
                        exclude_single_label_queries=ex_sl,
                        temperature=0.0,
                    )
            st.session_state["ev_df"] = ev_df
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Accuracy (satır)", f"{metrics['accuracy']:.2%}")
            c2.metric("Precision", f"{metrics['precision_macro']:.3f}")
            c3.metric("Recall", f"{metrics['recall_macro']:.3f}")
            c4.metric("F1-macro", f"{metrics['f1_macro']:.3f}")
            r2 = st.columns(4)
            r2[0].metric(
                "Ort. sorgu doğruluğu",
                f"{metrics['mean_query_accuracy']:.2%}" if metrics.get("mean_query_accuracy") is not None else "—",
            )
            r2[1].metric("Sorgu sayısı", str(metrics.get("num_queries", "—")))
            r2[2].metric(
                "Accuracy (Exact hariç)",
                f"{metrics['accuracy_non_exact']:.2%}" if metrics.get("accuracy_non_exact") is not None else "—",
            )
            r2[3].metric(
                "F1 ort. (S,C,I)",
                f"{metrics['f1_macro_non_exact']:.3f}" if metrics.get("f1_macro_non_exact") is not None else "—",
            )
            show_cols = [c for c in ["query_id", "query_text", "product_title", "esci_label", "pred_label"] if c in ev_df.columns]
            st.dataframe(ev_df[show_cols], use_container_width=True)
            cm = metrics.get("confusion_matrix", {})
            if cm:
                st.subheader("Confusion Matrix")
                true_counts = pd.Series([_normalize_esci(str(x)) for x in ev_df["esci_label"]]).value_counts()
                st.caption(
                    f"Satır sayısı N={len(ev_df)}. Ground truth dağılımı: "
                    + ", ".join(f"{k}={v}" for k, v in true_counts.items())
                )
                st.markdown("**Sayım** — satır = gerçek, sütun = tahmin")
                cm_df = confusion_matrix_dataframe(cm)
                st.dataframe(cm_df, use_container_width=True)
                with st.expander("Satır yüzdeleri (her gerçek sınıf için)"):
                    st.dataframe(confusion_matrix_row_percent(cm), use_container_width=True)
        except Exception as e:
            st.error(str(e))

# ═══════════════════════════════════════════════════════════════
# TAB 3: PROMPT & MODEL KIYASI
# ═══════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Prompt iyileştirme & Model kıyası")
    t3a, t3b = st.tabs(["Prompt V1→V4 karşılaştırma", "Model: nano / mini / gpt + maliyet"])

    # ─── PROMPT KARŞILAŞTIRMA ─────────────────────────────────
    with t3a:
        st.markdown(
            "Aynı verinin **en üstten N satırı** üzerinde **V1, V2, V3, V4** prompt’larını sırayla çalıştırır; "
            "ground truth ile karşılaştırıp aşağıdaki grafikleri üretir."
        )

        with st.expander("V1–V4 farkı nedir? (özet)"):
            st.markdown("""
| | |
|--|--|
| **V1** | Zayıf tanım (markaya takılır), sadece ürün başlığı, örnek yok |
| **V2** | Doğru tanımlar, başlık, örnek yok |
| **V3** | Detaylı tanım + başlık & açıklama + 1 örnek |
| **V4** | Karar ağacı + örnekler + başlık & açıklama |
""")

        mx = max(5, min(100, int(n_rows)))
        t3_max_q: int | None = None
        t3_ex_sl = True
        t3_mode = st.radio(
            "Örneklem",
            ["Satır (üstten N)", "Sorgu (N çok-etiketli sorgu)"],
            horizontal=True,
            key="t3_sample_mode",
        )
        if t3_mode.startswith("Satır"):
            comp_rows = st.number_input(
                "Kaç satırda karşılaştıralım?",
                min_value=5,
                max_value=mx,
                value=min(12, mx),
                step=1,
                help=f"Veri setinde topl {n_rows} satır var. İlk N satır kullanılır.",
                key="t3_prompt_nrows",
            )
            n_calls_est = int(comp_rows) * 4
        else:
            nq_max = min(100, raw["query_id"].nunique()) if "query_id" in raw.columns else 20
            t3_max_q = st.number_input(
                "Kaç çok-etiketli sorgu?",
                min_value=1,
                max_value=max(1, nq_max),
                value=min(10, nq_max),
                key="t3_nq",
            )
            t3_ex_sl = st.checkbox("Tek etiketli sorguları çıkar", value=True, key="t3_ex_sl")
            comp_rows = 12
            sub_prev = subset_df_multi_label_queries(
                raw, int(t3_max_q), exclude_single_label_queries=t3_ex_sl,
            )
            n_calls_est = len(sub_prev) * 4
        est_min = max(1, n_calls_est // 60)
        est_max = max(2, n_calls_est // 15)
        st.caption(
            f"**Tahmini API çağrısı:** {n_calls_est} (4 prompt × satır) — kabaca {est_min}–{est_max} dk"
        )

        if st.button("Karşılaştır ve grafikleri göster", key="t3_run_prompt", type="primary"):
            from src.evaluation import run_prompt_comparison

            try:
                prog = st.progress(0, text="Hazırlanıyor…")
                status = st.empty()

                def _on_progress(done: int, total: int, pv: str, nrows: int) -> None:
                    prog.progress(done / total if total else 1.0, text=f"{pv.upper()} tamamlandı ({done}/{total})")
                    status.info(f"**{pv.upper()}** bitti. {'Devam ediyor…' if done < total else 'Hepsi bitti!'}")

                with st.spinner("LLM çağrıları devam ediyor…"):
                    if t3_mode.startswith("Satır"):
                        comp_df = run_prompt_comparison(
                            raw, max_rows=int(comp_rows), temperature=0.0, progress_callback=_on_progress,
                        )
                    else:
                        comp_df = run_prompt_comparison(
                            raw, max_queries=int(t3_max_q), exclude_single_label_queries=t3_ex_sl,
                            temperature=0.0, progress_callback=_on_progress,
                        )
                prog.progress(1.0, text="Tamamlandı")
                status.success(f"Tamamlandı ({n_calls_est} çağrı).")
                st.session_state["t3_prompt_df"] = comp_df
            except Exception as e:
                st.error(str(e))

        # ─── SONUÇLAR ────────────────────────────────────────
        comp_df = st.session_state.get("t3_prompt_df")
        if comp_df is not None and len(comp_df):
            n_used = int(comp_df["total_count"].iloc[0]) if "total_count" in comp_df.columns else None
            n_qq = int(comp_df["num_queries"].iloc[0]) if "num_queries" in comp_df.columns and pd.notna(comp_df["num_queries"].iloc[0]) else None
            st.divider()
            if n_qq is not None and n_qq > 0:
                st.subheader(f"Grafikler — {n_qq} sorgu, {n_used or '?'} satır, 4 prompt")
            else:
                st.subheader(f"Grafikler — {n_used or '?'} satır, 4 prompt")

            base_row = comp_df[comp_df["prompt_version"].astype(str) == "v1"]
            v1_acc = float(base_row["accuracy"].iloc[0]) if len(base_row) else None
            best_row = comp_df.loc[comp_df["accuracy"].idxmax()]
            best_pv = str(best_row["prompt_version"])
            best_acc = float(best_row["accuracy"])

            if v1_acc is not None:
                gain_pp = (best_acc - v1_acc) * 100
                k1, k2 = st.columns(2)
                k1.metric("V1 doğruluk (accuracy)", f"{v1_acc:.1%}")
                k2.metric(f"En iyi ({best_pv.upper()})", f"{best_acc:.1%}", delta=f"+{gain_pp:.1f} pp")

            plot_df = comp_df.copy()
            plot_df["Prompt"] = plot_df["prompt_version"].str.upper()

            st.markdown("**1) Hangi prompt daha doğru? (accuracy — satır)**")
            fig_acc = px.bar(
                plot_df, x="Prompt", y="accuracy",
                text_auto=".0%",
                title="Accuracy — yüksek çubuk = ground truth’a daha yakın",
                labels={"accuracy": "Doğruluk"},
            )
            fig_acc.update_layout(yaxis=dict(range=[0, 1.05], tickformat=".0%"))
            fig_acc.update_traces(textposition="outside")
            st.plotly_chart(fig_acc, use_container_width=True)

            if "accuracy_non_exact" in comp_df.columns and comp_df["accuracy_non_exact"].notna().any():
                st.markdown("**1b) Exact olmayan satırlarda accuracy** (S/C/I karışımı)")
                ne_df = comp_df.copy()
                ne_df["Prompt"] = ne_df["prompt_version"].str.upper()
                fig_ne = px.bar(
                    ne_df, x="Prompt", y="accuracy_non_exact",
                    text_auto=".0%",
                    title="Ground truth ≠ Exact olan satırlarda doğruluk",
                )
                fig_ne.update_layout(yaxis=dict(range=[0, 1.05], tickformat=".0%"))
                st.plotly_chart(fig_ne, use_container_width=True)

            st.markdown("**2) V1 → V4 ilerledikçe metrikler**")
            m_cols = [c for c in (
                "accuracy", "f1_macro", "f1_macro_non_exact", "precision_macro", "recall_macro",
            ) if c in comp_df.columns]
            long = comp_df.melt(
                id_vars=["prompt_version"], value_vars=m_cols,
                var_name="Metrik", value_name="Değer",
            )
            long["Metrik"] = long["Metrik"].replace({
                "accuracy": "Accuracy",
                "f1_macro": "F1 (ortalama)",
                "f1_macro_non_exact": "F1 (S,C,I ort.)",
                "precision_macro": "Precision",
                "recall_macro": "Recall",
            })
            fig_line = px.line(
                long, x="prompt_version", y="Değer", color="Metrik", markers=True,
                title="Prompt sürümü arttıkça skorlar",
                category_orders={"prompt_version": ["v1", "v2", "v3", "v4"]},
                labels={"prompt_version": "Prompt"},
            )
            fig_line.update_layout(yaxis=dict(range=[0, 1.05]))
            st.plotly_chart(fig_line, use_container_width=True)

            with st.expander("Sayılar (tablo)"):
                show_cols = [c for c in [
                    "prompt_version", "feature_mode", "shot_mode", "accuracy", "f1_macro",
                    "precision_macro", "recall_macro", "correct_count", "total_count",
                ] if c in comp_df.columns]
                st.dataframe(comp_df[show_cols], use_container_width=True)

            class_cols = [c for c in ("f1_Exact", "f1_Substitute", "f1_Complement", "f1_Irrelevant") if c in comp_df.columns]
            if class_cols:
                st.markdown("**3) Sınıf bazlı F1 (Exact / Substitute / …)**")
                hm = comp_df.set_index("prompt_version")[class_cols]
                fig_hm = go.Figure(data=go.Heatmap(
                    z=hm.values,
                    x=[c.replace("f1_", "") for c in class_cols],
                    y=[v.upper() for v in hm.index],
                    colorscale="RdYlGn", zmin=0, zmax=1,
                    text=[[f"{v:.2f}" for v in row] for row in hm.values],
                    texttemplate="%{text}", textfont={"size": 14},
                ))
                fig_hm.update_layout(
                    title="Yeşil = o sınıfta LLM tahmini ground truth’a yakın",
                    xaxis_title="Sınıf", yaxis_title="Prompt",
                    yaxis=dict(autorange="reversed"),
                    height=320,
                )
                st.plotly_chart(fig_hm, use_container_width=True)

            class_cols_ne = [c for c in ("f1_Substitute", "f1_Complement", "f1_Irrelevant") if c in comp_df.columns]
            if len(class_cols_ne) >= 2:
                st.markdown("**3b) Exact hariç sınıflar (S / C / I)** — çoğu veri setinde Exact baskın olduğu için ayrıca bakılır")
                hm2 = comp_df.set_index("prompt_version")[class_cols_ne]
                fig_hm2 = go.Figure(data=go.Heatmap(
                    z=hm2.values,
                    x=[c.replace("f1_", "") for c in class_cols_ne],
                    y=[v.upper() for v in hm2.index],
                    colorscale="RdYlGn", zmin=0, zmax=1,
                    text=[[f"{v:.2f}" for v in row] for row in hm2.values],
                    texttemplate="%{text}", textfont={"size": 14},
                ))
                fig_hm2.update_layout(
                    title="Substitute / Complement / Irrelevant F1",
                    xaxis_title="Sınıf", yaxis_title="Prompt",
                    yaxis=dict(autorange="reversed"),
                    height=300,
                )
                st.plotly_chart(fig_hm2, use_container_width=True)

    # ─── MODEL KARŞILAŞTIRMA ─────────────────────────────────
    with t3b:
        st.markdown("""
**nano / mini / gpt:** Aynı satırlar, aynı prompt ile farklı modellerin accuracy ve tahmini maliyetini 
karşılaştırın. **En verimli** (accuracy / maliyet) ve **en doğru** modeli görün.
""")
        from src.model_tiers import EST_INPUT_TOKENS_PER_CALL, EST_OUTPUT_TOKENS_PER_CALL, resolve_tier_models

        tiers = resolve_tier_models()
        with st.expander("Model eşlemesi"):
            st.json(tiers)

        m_prompt = st.selectbox("Prompt", ["v1", "v2", "v3", "v4"], index=3,
                                format_func=lambda x: x.upper(), key="t3b_prompt")
        m_rows = st.slider("Satır sayısı", 5, min(50, n_rows), min(10, n_rows), key="t3b_rows")
        st.caption(f"{m_rows} satır × 3 model = {m_rows * 3} çağrı")

        if st.button("Nano / mini / gpt çalıştır", key="t3b_run", type="primary"):
            from src.evaluation import run_model_comparison
            try:
                with st.spinner(f"3 model × {m_rows} satır çalıştırılıyor..."):
                    mdf = run_model_comparison(raw, prompt_version=m_prompt, max_rows=m_rows, temperature=0.0)
                st.session_state["t3_model_df"] = mdf
            except Exception as e:
                st.error(str(e))

        mdf = st.session_state.get("t3_model_df")
        if mdf is not None and len(mdf):
            st.divider()
            show = mdf.copy()
            if "est_cost_usd" in show.columns:
                show["accuracy_pct"] = (show["accuracy"] * 100).round(2)
                show["cost_per_correct"] = show.apply(
                    lambda r: round(r["est_cost_usd"] / r["correct_count"], 6) if r.get("correct_count", 0) > 0 else None, axis=1,
                )
            st.dataframe(show, use_container_width=True)

            st.plotly_chart(px.bar(mdf, x="tier", y="accuracy", color="model_id",
                                   title="Accuracy: nano vs mini vs gpt"), use_container_width=True)

            if "est_cost_usd" in mdf.columns:
                fig_sc = px.scatter(mdf, x="est_cost_usd", y="accuracy", text="tier",
                                    size="total_count", hover_data=["model_id"],
                                    title="Maliyet vs Accuracy",
                                    labels={"est_cost_usd": "Tahmini maliyet (USD)", "accuracy": "Accuracy"})
                fig_sc.update_traces(textposition="top center")
                st.plotly_chart(fig_sc, use_container_width=True)

                eff = mdf.copy()
                eff["acc_per_usd"] = eff.apply(
                    lambda r: r["accuracy"] / r["est_cost_usd"] if r["est_cost_usd"] > 0 else 0, axis=1,
                )
                st.plotly_chart(px.bar(eff, x="tier", y="acc_per_usd", color="model_id",
                                       title="Verimlilik: Accuracy / USD (yüksek = daha verimli)"),
                                use_container_width=True)

                from src.model_tiers import pricing_for_model
                cost_t = []
                for _, r in mdf.iterrows():
                    ip, op = pricing_for_model(str(r["model_id"]))
                    cost_t.append({
                        "Katman": str(r["tier"]).upper(),
                        "Model": str(r["model_id"]),
                        "Input $/1M": ip, "Output $/1M": op,
                        "Maliyet ($)": round(float(r["est_cost_usd"]), 6),
                        "Accuracy %": round(float(r["accuracy"]) * 100, 2),
                        "Doğru/Toplam": f"{int(r.get('correct_count', 0))}/{int(r.get('total_count', 0))}",
                    })
                st.markdown("**Maliyet tablosu (ChatGPT fiyatları)**")
                st.dataframe(pd.DataFrame(cost_t), use_container_width=True)

                best_e = eff.loc[eff["acc_per_usd"].idxmax()]
                best_a = eff.loc[eff["accuracy"].idxmax()]
                c1, c2 = st.columns(2)
                c1.success(f"**En verimli:** {str(best_e['tier']).upper()} — {float(best_e['accuracy']):.1%}, ${float(best_e['est_cost_usd']):.4f}")
                c2.info(f"**En doğru:** {str(best_a['tier']).upper()} — {float(best_a['accuracy']):.1%}, ${float(best_a['est_cost_usd']):.4f}")

            class_m = [c for c in ("f1_Exact", "f1_Substitute", "f1_Complement", "f1_Irrelevant") if c in mdf.columns]
            if class_m:
                st.subheader("Model × Sınıf F1")
                hm_m = mdf.set_index("tier")[class_m]
                fig_hm2 = go.Figure(data=go.Heatmap(
                    z=hm_m.values,
                    x=[c.replace("f1_", "") for c in class_m],
                    y=[t.upper() for t in hm_m.index],
                    colorscale="RdYlGn", zmin=0, zmax=1,
                    text=[[f"{v:.2f}" for v in row] for row in hm_m.values],
                    texttemplate="%{text}", textfont={"size": 15},
                ))
                fig_hm2.update_layout(title="Model × Sınıf F1", height=300)
                st.plotly_chart(fig_hm2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TAB 4: ERROR ANALYSIS
# ═══════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Error Analysis")
    st.markdown(
        "Bu sekme **hata avcısı değil**: seçtiğin satırda LLM’e **aynı soruyu üç kez** sorar "
        "(sadece başlık / sadece açıklama / ikisi birden). Kolay örneklerde üçü de **doğru** çıkar; "
        "bu normal. Gerçek hatayı görmek için aşağıdan **yanlış tahmin edilen satırları** seç."
    )

    err_prompt = st.selectbox("Prompt", ["v1", "v2", "v3", "v4"],
                              format_func=lambda x: x.upper(), key="err_prompt")

    ev_df = st.session_state.get("ev_df")
    wrong_ilocs: list[int] = []
    if ev_df is not None and len(ev_df) and "pred_label" in ev_df.columns and "esci_label" in ev_df.columns:
        for k in range(len(ev_df)):
            t = _normalize_esci(str(ev_df.iloc[k]["esci_label"]))
            p = _normalize_esci(str(ev_df.iloc[k]["pred_label"]))
            if t != p:
                wrong_ilocs.append(k)

    row_mode = st.radio(
        "Satır listesi",
        ["Tüm satırlar", "Yalnızca yanlış tahmin (Tab 2 → Accuracy hesapla sonrası)"],
        horizontal=True,
        key="err_row_mode",
    )

    if row_mode.startswith("Yalnızca"):
        if ev_df is None or not len(wrong_ilocs):
            st.warning(
                "Önce **LLM Judge** sekmesinde **Accuracy hesapla** ile toplu değerlendirme yap; "
                "burada yalnızca `pred ≠ doğru etiket` satırlar listelenir."
            )
            row_options = list(range(len(df)))
        else:
            row_options = wrong_ilocs
            st.caption(f"Tab 2 çıktısından **{len(wrong_ilocs)}** yanlış satır (ilk N satır içinde).")
    else:
        row_options = list(range(len(df)))

    def _row_label(i: int) -> str:
        if i >= len(df):
            return str(i)
        r = df.iloc[i]
        tt = str(r.get("product_title", ""))[:45]
        tl = str(r.get("esci_label", ""))
        if row_mode.startswith("Yalnızca") and ev_df is not None and i < len(ev_df) and "pred_label" in ev_df.columns:
            pl = str(ev_df.iloc[i]["pred_label"])
            return f"Satır {i}: …{tt}… | doğru={tl} tahmine={pl}"
        return f"Satır {i}: …{tt}…"

    err_idx = st.selectbox("Satır seç", row_options, format_func=_row_label)

    if st.button("Error analysis çalıştır"):
        from src.llm_judge import judge_query_product, run_error_analysis
        row = df.iloc[int(err_idx)]
        q = str(row.get("query_text", row.get("query", "")))
        title = str(row.get("product_title", ""))
        desc = str(row.get("product_description", "")) if "product_description" in df.columns else ""
        true_l = str(row["esci_label"])
        pred_l = row.get("pred_label", "-")
        if pred_l == "-" or pred_l is None or str(pred_l).strip() == "":
            with st.spinner("LLM çağrılıyor (tek tahmin)..."):
                j0 = judge_query_product(
                    q, title, desc, prompt_version=err_prompt, temperature=0.0,
                )
            pred_l = j0.label
        match = _normalize_esci(str(true_l)) == _normalize_esci(str(pred_l))
        with st.spinner("3 feature mode çalıştırılıyor..."):
            results = run_error_analysis(
                q, title, desc, true_label=true_l, pred_label=str(pred_l),
                prompt_version=err_prompt, temperature=0.0,
            )
        st.write(f"**Query:** {q}")
        st.write(f"**Product:** {title}")
        st.write(f"**Doğru etiket:** {true_l} | **Üstteki tek tahmin (Pred):** {pred_l}")
        if match:
            st.info("Bu satırda tek tahmin zaten doğru — yine de üç modda girdi farkını görebilirsin.")
        else:
            st.error("Bu satırda tek tahmin yanlış — aşağıda hangi modda nasıl sapıyor bak.")
        for mode, j in results.items():
            ok_m = _normalize_esci(true_l) == _normalize_esci(j.label)
            tag = "✓" if ok_m else "✗"
            with st.expander(f"{tag} {mode}: {j.label}"):
                st.write(j.reasoning)

# ═══════════════════════════════════════════════════════════════
# TAB 5: DATAFRAME
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.subheader("DataFrame — Query bazlı")
    query_filter = st.selectbox("Query seç", ["Tümü"] + list(df["query_id"].unique().astype(str)))
    disp = df[df["query_id"].astype(str) == query_filter].copy() if query_filter != "Tümü" else df.copy()
    st.dataframe(disp, use_container_width=True)
    st.markdown("**Sınıf dağılımı**")
    from src.evaluation import get_class_distribution
    dist = get_class_distribution(disp["esci_label"].astype(str).tolist())
    dist_df = pd.DataFrame(list(dist.items()), columns=["Sınıf", "Adet"]).set_index("Sınıf")
    st.bar_chart(dist_df)
