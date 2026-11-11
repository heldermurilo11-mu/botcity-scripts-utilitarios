import os
import sys
import time
import requests
from dotenv import load_dotenv
from botcity.maestro import BotMaestroSDK

# Garantir UTF-8 no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

def obter_cliente_maestro():
    server = os.getenv("BOTCITY_SERVER", "https://developers.botcity.dev")
    if not server.startswith("http"):
        server = f"https://{server}"

    login = os.getenv("BOTCITY_LOGIN")
    key = os.getenv("BOTCITY_KEY")
    workspace = os.getenv("BOTCITY_WORKSPACE", login)

    if not login or not key:
        raise ValueError("Variáveis BOTCITY_LOGIN e BOTCITY_KEY não configuradas no ambiente ou .env.")

    maestro = BotMaestroSDK(server=server, login=login, key=key)
    maestro.login()

    headers = {
        "Authorization": f"Bearer {maestro.access_token}",
        "organization": workspace
    }
    return server, workspace, headers

def cancelar_todas_tasks_aguardando(batch_size=50):
    server, workspace, headers = obter_cliente_maestro()

    print("=" * 80)
    print(" 🗑️  CANCELAMENTO EM MASSA DE TAREFAS 'AGUARDANDO' (START)")
    print("=" * 80)
    print(f"Servidor:  {server}")
    print(f"Workspace: {workspace}\n")

    total_canceladas = 0
    atividades_canceladas = {}

    while True:
        # Busca a primeira página de tarefas em START
        url_search = f"{server}/api/v2/task"
        params = {
            "states": "START",
            "page": 0,
            "size": batch_size,
            "sort": "id,asc"
        }
        
        resp = requests.get(url_search, headers=headers, params=params)
        if resp.status_code != 200:
            print(f"[ERRO] Falha ao consultar tarefas: {resp.status_code} - {resp.text}")
            break

        data = resp.json()
        tarefas = data.get("content", [])
        total_restantes = data.get("totalElements", 0)

        if not tarefas:
            print("Nenhuma tarefa com status 'Aguardando' (START) encontrada.")
            break

        print(f"-> Localizadas {len(tarefas)} tarefas para cancelamento (Restantes na fila: {total_restantes})...")

        task_ids = [t["id"] for t in tarefas]

        # Registrar estatísticas por atividade
        for t in tarefas:
            lbl = t.get("activityLabel") or "Sem Label"
            atividades_canceladas[lbl] = atividades_canceladas.get(lbl, 0) + 1

        # Tentar exclusão em lote (Bulk Delete)
        url_bulk = f"{server}/api/v2/task/bulk"
        bulk_resp = requests.delete(url_bulk, headers=headers, json={"labels": task_ids})

        if bulk_resp.status_code in [200, 204]:
            total_canceladas += len(task_ids)
            print(f"   [OK] Lote de {len(task_ids)} tarefas cancelado com sucesso. (Total acumulado: {total_canceladas})")
        else:
            print(f"   [AVISO] Falha no bulk delete ({bulk_resp.status_code}). Tentando individualmente...")
            for tid in task_ids:
                single_resp = requests.delete(f"{server}/api/v2/task/{tid}", headers=headers)
                if single_resp.status_code in [200, 204]:
                    total_canceladas += 1
                else:
                    print(f"   [FALHA] Não foi possível cancelar tarefa #{tid}: {single_resp.status_code}")

        # Pequena pausa para evitar sobrecarregar o orquestrador
        time.sleep(0.3)

    print("\n" + "=" * 80)
    print(" 🏁 RELATÓRIO FINAL DE CANCELAMENTO")
    print("=" * 80)
    print(f"Total de tarefas canceladas/removidas: {total_canceladas}")
    print("\nDetalhamento por automação:")
    for lbl, qtd in sorted(atividades_canceladas.items(), key=lambda x: x[1], reverse=True):
        print(f" • {lbl:<30}: {qtd:>4} tarefas")
    print("=" * 80)

if __name__ == "__main__":
    cancelar_todas_tasks_aguardando()
