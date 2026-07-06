@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

:: ============================================================
::   SYSFORGE  --  BUMP DE VERSAO  (SINGULARITY DOT // SD-02)
::   Uso:
::     bump.bat            -> incrementa o patch (1.1.4 -> 1.1.5)
::     bump.bat 1.2.0      -> define exatamente a versao 1.2.0
::   Atualiza a fonte unica: gear\updater.py (CURRENT_VERSION).
:: ============================================================

for /f "tokens=3 delims= " %%a in ('findstr /b /c:"CURRENT_VERSION" gear\updater.py') do set "RAWVER=%%a"
set "CUR=%RAWVER:"=%"
if "%CUR%"=="" ( echo [X] Nao consegui ler CURRENT_VERSION de gear\updater.py. & pause & exit /b 1 )

if not "%~1"=="" (
    set "NEW=%~1"
) else (
    for /f "tokens=1,2,3 delims=." %%x in ("%CUR%") do (
        set /a PATCH=%%z+1
        set "NEW=%%x.%%y.!PATCH!"
    )
)

echo [i] Versao atual: %CUR%
echo [i] Nova versao:  !NEW!

powershell -NoProfile -Command "$p='gear\updater.py'; $c=[IO.File]::ReadAllText($p); $c=[regex]::Replace($c,'(?m)^CURRENT_VERSION\s*=.*','CURRENT_VERSION = \"!NEW!\"'); [IO.File]::WriteAllText($p,$c,(New-Object Text.UTF8Encoding($false)))"
if errorlevel 1 ( echo [X] Falha ao atualizar a versao. & pause & exit /b 1 )

:: Confirma a gravacao
for /f "tokens=3 delims= " %%a in ('findstr /b /c:"CURRENT_VERSION" gear\updater.py') do set "CHK=%%a"
set "CHK=%CHK:"=%"
if not "%CHK%"=="!NEW!" ( echo [X] Verificacao falhou. Esperado !NEW!, encontrado %CHK%. & pause & exit /b 1 )

echo [OK] CURRENT_VERSION atualizado para !NEW! em gear\updater.py.
echo      ^(O deploy.bat e o Inno Setup ja usam essa versao automaticamente.^)
echo.
pause
