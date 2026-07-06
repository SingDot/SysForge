@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

:: ============================================================
::   MIGRACAO PARA HISTORICO LIMPO  --  SINGULARITY DOT / SD-02
::   Cria um historico git novo (sem os vazamentos antigos) e
::   envia para a conta nova. Rode UMA VEZ, na migracao.
:: ============================================================

echo ============================================================
echo   MIGRACAO PARA HISTORICO LIMPO  --  SysForge (SD-02)
echo ============================================================
echo.
echo Este script APAGA todo o historico de commits local e cria
echo um historico novo e limpo (sem os snapshots/URLs antigos que
echo expunham o nome real) e envia para a conta nova no GitHub.
echo.
echo ANTES DE CONTINUAR:
echo   1) Crie o repositorio VAZIO 'SysForge' na conta SingDot
echo      (github.com  -^>  New repository  -^>  sem README/licenca).
echo   2) O primeiro push vai abrir a janela de login do GitHub.
echo.
echo *** ACAO DESTRUTIVA E IRREVERSIVEL ***
echo.
set /p CONFIRM=Digite  SIM  para continuar:
if /I not "%CONFIRM%"=="SIM" ( echo Cancelado. & pause & exit /b 0 )

set "REPO_URL=https://github.com/SingDot/SysForge.git"

echo.
echo [*] Removendo historico antigo (.git)...
if exist ".git" rmdir /s /q ".git"

echo [*] Inicializando repositorio novo...
git init
git branch -M main
git add -A
git commit -m "SysForge v1.1.5 - Singularity Dot // SD-02 (historico limpo)"

echo [*] Conectando ao remoto %REPO_URL% ...
git remote add origin "%REPO_URL%"

echo [*] Enviando push inicial...
git push -u origin main
if errorlevel 1 (
    echo.
    echo [X] Falha no push. Verifique se o repo VAZIO existe na conta SingDot
    echo     e se a autenticacao do GitHub foi concluida.
    pause & exit /b 1
)

echo.
echo [OK] Migracao concluida. Historico limpo publicado em SingDot/SysForge.
echo      A partir de agora, use o deploy.bat para os proximos releases.
echo.
pause
