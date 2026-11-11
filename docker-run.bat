@echo off
echo ==========================================
echo    BotCity Utils - Execucao via DOCKER
echo ==========================================

if not exist .env (
    echo [!] Erro: Arquivo .env nao encontrado. Crie um antes de continuar.
    pause
    exit /b
)

echo [1/2] Construindo/Atualizando a imagem Docker...
docker-compose build --quiet

echo [2/2] Iniciando o container interativo...
echo Digite o nome do script que deseja rodar (ex: finish_task.py ID_TAREFA)
set /p SCRIPT_CMD="Comando: python "

docker-compose run --rm botcity-utils python %SCRIPT_CMD%

pause
