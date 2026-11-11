@echo off
echo ==========================================
echo    CORRETOR AUTOMATICO - DOCKER
echo ==========================================

echo [1/3] Ajustando contexto do Docker para Windows...
docker context use default

echo [2/3] Limpando configuracoes antigas de rede/build...
docker-compose down --remove-orphans

echo [3/3] Forcando a construcao da imagem (isso vai baixar a imagem BotCity oficial)...
echo Isso pode demorar uns minutos (cerca de 500MB)...
docker-compose build --no-cache

echo.
echo ==========================================
echo    CONCLUIDO! 
echo    Verifique se a imagem 'botcity-utils:latest' 
echo    apareceu no seu Docker Desktop / IDE.
echo ==========================================
pause
