# Sunum dosyasını (.pptx) PC’ye indirmek

Bu projede sunum **`Sunum_Search_Relevance.pptx`** olarak üretilir. Sohbet üzerinden ikili dosya gönderilemediği için en kesin yol **Google Colab** (tarayıcı, ücretsiz, Python kurulumu gerekmez).

---

## Yöntem A — Google Colab (önerilen, PC’de Python yoksa)

1. Tarayıcıda aç: **https://colab.research.google.com**
2. **Yeni not defteri** oluştur.
3. Sol taraftaki **dosya simgesi** → **`sunum_olustur.py`** dosyasını yükle (proje kökünde; `scripts` klasörü boş olsa bile yeterli).  
   Tam yol örneği:  
   `Documents\search-relevance-eval\sunum_olustur.py`
4. Üstte **+ Kod** ile tek bir hücre aç, aşağıyı yapıştır ve **Çalıştır** (▶):

```python
!pip install python-pptx -q
import os
os.environ["SUNUM_OUT"] = "/content/Sunum_Search_Relevance.pptx"
exec(open("sunum_olustur.py", encoding="utf-8").read())
```

5. Birkaç saniye sonra tarayıcı **Sunum_Search_Relevance.pptx** dosyasını **otomatik indirir** (Colab indirme çubuğu).
6. İndirilen dosyayı **Google Drive**’a sürükleyip **Google Slides ile aç**abilirsin: sağ tık → **Uygulamalarla aç** → **Google Slaytlar**.

---

## Yöntem B — Windows’ta çift tık (Python yüklüyse)

Proje klasöründeki **`BUILD_SUNUM.bat`** dosyasına çift tıkla.  
Başarılı olursa dosya şurada oluşur:

`Documents\search-relevance-eval\Sunum_Search_Relevance.pptx`

Python yoksa veya hata verirse **Yöntem A**’yı kullan.

---

## Yöntem C — Manuel komut

Komut İstemi veya PowerShell’de (Python / `py` tanıyorsa):

```bat
cd %USERPROFILE%\Documents\search-relevance-eval
py -m pip install python-pptx
py sunum_olustur.py
```

---

## Google Slides’a aktarma (PowerPoint yok)

1. **https://drive.google.com** → **Yeni** → **Dosya yükle** → `Sunum_Search_Relevance.pptx`
2. Yüklenen dosyaya çift tıkla → **Google Slaytlar** ile açılır.
3. Sunum için: **Slayt göster** veya **Ctrl+F5**.
