@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Sunum olusturuluyor: Sunum_Search_Relevance.pptx
echo.

where py >nul 2>&1
if %errorlevel%==0 (
  py -m pip install python-pptx -q
  py sunum_olustur.py
  if exist "Sunum_Search_Relevance.pptx" (
    echo.
    echo Tamam. Dosya:
    echo   %cd%\Sunum_Search_Relevance.pptx
    explorer /select,"%cd%\Sunum_Search_Relevance.pptx"
    goto :end
  )
)

where python >nul 2>&1
if %errorlevel%==0 (
  python -m pip install python-pptx -q
  python sunum_olustur.py
  if exist "Sunum_Search_Relevance.pptx" (
    echo.
    echo Tamam. Dosya:
    echo   %cd%\Sunum_Search_Relevance.pptx
    explorer /select,"%cd%\Sunum_Search_Relevance.pptx"
    goto :end
  )
)

echo.
echo Python bulunamadi veya sunum olusturulamadi.
echo Kesin cozum: SUNUM_PPTX_INDIR.md dosyasindaki Google Colab adimlarini izle.
echo.
pause
exit /b 1

:end
echo.
pause
