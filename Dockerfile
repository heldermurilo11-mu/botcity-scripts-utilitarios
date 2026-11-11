# Usar a imagem oficial da BotCity para Python
FROM botcity/botcity-python-desktop:latest

# Definir o diretório de trabalho
WORKDIR /app

# Copiar os requisitos
COPY requirements.txt .

# Instalar pip e dependências
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copiar o restante do código
COPY . .

# Desativar o entrypoint padrão da BotCity que causava o erro
ENTRYPOINT []

# Comando padrão
CMD ["python3", "explorador_lista_datapools.py"]
