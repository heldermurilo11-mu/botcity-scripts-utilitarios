@echo off
setlocal enabledelayedexpansion

:: Navega para a pasta do script
cd /d "%~dp0"

echo ==========================================
echo    BotCity Maestro Utilities - Local
echo ==========================================

:: 1. Verifica se o Python está no PATH
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Erro: Python nao encontrado no PATH.
    pause
    exit /b
)

:: 2. Gerencia o Ambiente Virtual
if not exist .venv (
    echo [1/2] Criando ambiente virtual...
    python -m venv .venv
)

echo [2/2] Ativando ambiente e instalando dependencias...
call .venv\Scripts\activate
pip install -r requirements.txt --quiet

echo.
echo --- PRONTO PARA USO ---
echo Escolha o script que deseja rodar:
echo 1. Finalizar Tarefas (finish_task.py)
echo 2. Analisar Ciclo de Vida (analisador_metricas_ciclo_vida.py)
echo 3. Exportar Datapools (exportador_historico_datapools.py)
echo 4. Listar Datapools (explorador_lista_datapools.py)
echo 5. Validar Filas de Hoje (validador_datapools_dia.py)
echo.

set /p OPCAO="Digite o numero da opcao: "

if "%OPCAO%"=="1" (
    set /p TID="Digite o ID da tarefa: "
    python finish_task.py !TID!
) else if "%OPCAO%"=="2" (
    python analisador_metricas_ciclo_vida.py
) else if "%OPCAO%"=="3" (
    python exportador_historico_datapools.py
) else if "%OPCAO%"=="4" (
    python explorador_lista_datapools.py
) else if "%OPCAO%"=="5" (
    python validador_datapools_dia.py
) else (
    echo Opcao invalida.
)

echo.
echo Processo concluido.
pause
