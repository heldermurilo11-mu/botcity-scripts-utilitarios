# BotCity Maestro — Scripts Utilitários, Governança de Datapools & Dashboard

Este repositório reúne um conjunto consolidado de scripts Python, utilitários Docker e um Dashboard HTML interativo (offline-ready) para automatizar ações administrativas, monitoramento de filas (Datapools), análise histórica de execuções e gerenciamento operacional no orquestrador **BotCity Maestro**.

---

## 🚀 Visão Geral das Ferramentas

### 1. Ferramentas CLI para Tarefas, Alertas e Insights
* **`encerrar_task.py`**: Finaliza tarefas travadas autenticando via `.env` (`BotMaestroSDK` + `maestro.login()`) e parâmetros posicional/CLI.
* **`finish_task.py`**: Finaliza tarefas com reporte completo de métricas para o BotCity Insights (`--total`, `--processed`, `--failed`).
* **`status_task.py`**: Consulta metadados completos de uma tarefa diretamente via REST API v2 do Maestro.
* **`enviar_alerta.py`**: Dispara alertas visuais (`INFO`, `WARN`, `ERROR`) vinculados a uma tarefa.
* **`inserir_datapool.py`**: Insere um registro JSON programaticamente em um Datapool.
* **`upload_artefato.py`**: Faz upload de relatórios, logs ou planilhas para a guia *Result Files* da tarefa.
* **`mock_insights.py`**: Gera execuções simuladas com itens de sucesso e falha para validar gráficos de ROI no **BotCity Insights**.
* **`cancelar_tasks_aguardando.py`**: Cancela em lote tarefas presas no estado `START` (*Aguardando*), com fallback individual.
* **`pesquisar_tarefas_datas.py`**: Lista e agrupa tarefas por atividade dentro de uma janela de datas informada via CLI (`--start` / `--end`).
* **`analise_historica_completa.py`**: Calcula média, mediana, mínimo, máximo e P90 de tempo de fila, execução e ciclo total por atividade no período (`--start` / `--end`).

### 2. Governança de Datapools & Métricas
* **`conexao_maestro.py`**: Módulo centralizado para autenticação local via `.env` e resolução de prefixos (`--prefix` ou variável `DATAPOOL_PREFIXES`).
* **`explorador_lista_datapools.py`**: Lista todos os Datapools cadastrados no workspace com nome e label.
* **`validador_datapools_dia.py`**: Verifica a existência e status (`ATIVO`/`INATIVO`) das filas diárias com base nos prefixos configurados (padrão: `fila_exemplo_`).
* **`exportador_historico_datapools.py`**: Exporta em CSV o histórico recente dos Datapools filtrados por prefixo para `output/exportacao_datapools/`.
* **`analisador_metricas_ciclo_vida.py`**: Consolida CSVs dos Datapools, calcula tempos médios de ciclo de vida (global, mensal e semanal) e salva `output/consolidado_lifecycle.csv`.
* **`inativar_datapools.py`**: Inativa em massa Datapools dentro de um período e prefixo explícitos (`--start`, `--end`, `--prefix`), com suporte a `--dry-run`, `--force` e `--preservar`.

### 3. Runner Docker & Scripts Windows
* **`Dockerfile` & `docker-compose.yml`**: Container isolado (`botcity-utils:latest`) baseado na imagem oficial `botcity/botcity-python-desktop:latest`.
* **`docker-run.bat`**: Constrói a imagem e executa qualquer script dentro do container interativo.
* **`consertar_docker.bat`**: Redefine o contexto Docker e reconstrói a imagem sem cache (`--no-cache`).
* **`start.bat`**: Cria o ambiente virtual `.venv`, instala dependências e abre um menu interativo no Windows.

### 4. Dashboard Interativo Offline
* **`scripts_dashboard.html`**: Painel web responsivo (BotCity Sidekick) para parametrização em tempo real com realce de sintaxe (Prism.js), cópia rápida e download de scripts `.py`.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem**: Python 3.8+
* **SDK Oficial**: `botcity-maestro-sdk`
* **Dependências**: `python-dotenv`, `pandas`, `requests` (listadas em `requirements.txt`)
* **Containerização**: Docker & Docker Compose
* **Interface Offline**: HTML5 / CSS3 / JavaScript Vanilla + Prism.js

---

## 🔑 Segurança e Boas Práticas

* **Zero segredos no código**: Nenhuma chave de API, credencial ou identificador interno fica gravado nos scripts.
* **Isolamento por `.env`**: Todas as credenciais residem localmente em `.env` (ignorado pelo `.gitignore`), usando `.env.example` como modelo.
* **Filtros explícitos e simulação**: Operações destrutivas ou em lote suportam `--dry-run` e parâmetros obrigatórios (`--start`, `--end`, `--prefix`).

---

## ⚙️ Configuração e Instalação

### 1. Clonar o Repositório
```bash
git clone https://github.com/heldermurilo11-mu/botcity-scripts-utilitarios.git
cd botcity-scripts-utilitarios
```

### 2. Instalar Dependências (Local)
```bash
python -m venv .venv
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente
Copie o modelo `.env.example` para `.env`:
```bash
cp .env.example .env
```
Preencha o arquivo `.env` com suas credenciais do BotCity Maestro:
```env
BOTCITY_SERVER=https://developers.botcity.dev
BOTCITY_LOGIN=seu-login
BOTCITY_KEY=sua-chave
BOTCITY_WORKSPACE=seu-workspace
```
Opcionalmente, defina `DATAPOOL_PREFIXES=fila_exemplo_` no `.env` para configurar prefixos padrão nos scripts de análise, validação e exportação de Datapools.

---

## 🐳 Execução via Docker

Com o Docker instalado e o arquivo `.env` configurado:
```bash
# Construir imagem botcity-utils:latest
docker compose build

# Executar qualquer script dentro do container
docker compose run --rm botcity-utils python3 explorador_lista_datapools.py
docker compose run --rm botcity-utils python3 finish_task.py 123456 --status SUCCESS
```
No Windows, também é possível usar os atalhos **`docker-run.bat`**, **`consertar_docker.bat`** ou **`start.bat`** (execução local com `.venv`).

---

## 📝 Guia de Execução dos Scripts CLI

### 1. Encerrar Tarefa Travada (`encerrar_task.py` / `finish_task.py`)
```bash
# Modo simples (posicional)
python encerrar_task.py <TASK_ID> [STATUS] [MENSAGEM]
python encerrar_task.py 123456 FAILED "Execução encerrada manualmente via CLI por tempo limite excedido."

# Modo completo com métricas de Insights
python finish_task.py 123456 --status SUCCESS --total 50 --processed 48 --failed 2 --message "Processamento concluído"
```
* **STATUS**: `FAILED`, `SUCCESS` ou `PARTIALLY_COMPLETED`.

### 2. Popular o BotCity Insights (`mock_insights.py`)
```bash
python mock_insights.py <ACTIVITY_LABEL> [QUANTIDADE]
python mock_insights.py MinhaAutomacao 5
```

### 3. Consultar Status da Tarefa (`status_task.py`)
```bash
python status_task.py <TASK_ID>
python status_task.py 123456
```

### 4. Enviar Alerta (`enviar_alerta.py`)
```bash
python enviar_alerta.py <TASK_ID> <TITULO> <MENSAGEM> [ALERT_TYPE]
python enviar_alerta.py 123456 "Integração Interrompida" "O serviço de destino não respondeu." ERROR
```

### 5. Inserir Item no Datapool (`inserir_datapool.py`)
```bash
python inserir_datapool.py <DATAPOOL_LABEL> <ITEM_JSON_STRING>
python inserir_datapool.py MEU_DATAPOOL '{"codigo": "123", "nome": "Exemplo", "valor": 150.50}'
```

### 6. Upload de Artefatos (`upload_artefato.py`)
```bash
python upload_artefato.py <TASK_ID> <NOME_DO_ARQUIVO_NO_ORQUESTRADOR> <CAMINHO_LOCAL>
python upload_artefato.py 123456 relatorio_mensal.xlsx ./output/relatorio_mensal.xlsx
```

### 7. Pesquisar e Analisar Histórico de Tarefas (`pesquisar_tarefas_datas.py` / `analise_historica_completa.py`)
```bash
python pesquisar_tarefas_datas.py --start 01/01/2026 --end 31/01/2026
python analise_historica_completa.py --start 01/01/2026 --end 31/01/2026 --activity MinhaAutomacao
```

### 8. Cancelar Tarefas Aguardando em Lote (`cancelar_tasks_aguardando.py`)
```bash
python cancelar_tasks_aguardando.py
```

### 9. Governança, Validação e Métricas de Datapools
```bash
# Listar todos os Datapools
python explorador_lista_datapools.py

# Validar existência das filas do dia (ou data específica YY_MM_DD)
python validador_datapools_dia.py --prefix fila_exemplo_*

# Exportar CSVs dos Datapools mais recentes
python exportador_historico_datapools.py --prefix fila_exemplo_* --limit 31

# Calcular métricas de ciclo de vida e gerar output/consolidado_lifecycle.csv
python analisador_metricas_ciclo_vida.py --prefix fila_exemplo_*

# Simular inativação em massa de Datapools (obrigatório --start, --end, --prefix)
python inativar_datapools.py --start 01/01/2026 --end 31/01/2026 --prefix fila_exemplo_* --dry-run

# Executar inativação direta preservando exceções específicas
python inativar_datapools.py --start 01/01/2026 --end 31/01/2026 --prefix fila_exemplo_* --preservar fila_principal --force
```

---

## 💡 Dica da API REST (Datapool View)
Ao consultar as entradas ativas de um Datapool específico usando apenas o label, a API REST v2 pode retornar `404 Not Found` em rotas de listagem convencionais. Para renderizar a grade de dados com base no label:
* **Método**: `GET`
* **Rota**: `/api/v2/datapool/{datapoolLabel}/view`
* **Headers Necessários**:
  - `Authorization: Bearer {accessToken}`
  - `organization: {workspace}`

---

## 🎨 Como usar o Dashboard Interativo Offline
1. Navegue até a pasta do repositório.
2. Abra o arquivo `scripts_dashboard.html` em qualquer navegador web.
3. Ajuste os parâmetros na barra lateral **Configurações** (`123456`, `MEU_DATAPOOL`, mensagens e alertas).
4. Clique em **Copiar** ou **Baixar** no cartão desejado para obter o script `.py` pronto para uso.
