import os
import sys
import requests

def obter_status_tarefa(task_id: str):
    # Carrega credenciais do .env ou ambiente
    server = os.getenv("BOTCITY_SERVER", "developers.botcity.dev")
    if not server.startswith("http"):
        server = f"https://{server}"

    login = os.getenv("BOTCITY_LOGIN")
    key = os.getenv("BOTCITY_KEY")
    workspace = os.getenv("BOTCITY_WORKSPACE", login)

    if not login or not key:
        print("[ERRO] Variaveis BOTCITY_LOGIN e BOTCITY_KEY precisam estar configuradas no seu .env ou no sistema.")
        return

    # 1. Login para adquirir o token JWT
    login_url = f"{server}/api/v2/workspace/{workspace}/login"
    print(f"Efetuando login no Orchestrator ({server})...")
    response = requests.post(login_url, json={"login": login, "key": key})
    response.raise_for_status()
    token = response.json()["accessToken"]

    # 2. Consultar detalhes da tarefa
    task_url = f"{server}/api/v2/task/{task_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "organization": workspace
    }

    print(f"Requisitando dados da task {task_id}...")
    task_resp = requests.get(task_url, headers=headers)
    task_resp.raise_for_status()

    data = task_resp.json()
    print("\n================ DADOS DA TAREFA ================")
    print(f"ID:              {data.get('id')}")
    print(f"Atividade (ID):  {data.get('activityId')} ({data.get('activityLabel')})")
    print(f"Status Atual:    {data.get('status')}")
    print(f"Criada em:       {data.get('creationDate')}")
    print(f"Iniciada em:     {data.get('startDate')}")
    print(f"Finalizada em:   {data.get('finishDate')}")
    print(f"Mensagem Fim:    {data.get('finishMessage')}")
    print(f"Usuario/Runner:  {data.get('user') or data.get('runnerId')}")
    print("=================================================")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python status_task.py <TASK_ID>")
        print("Exemplo: python status_task.py 123456")
        sys.exit(1)

    tid = sys.argv[1]
    obter_status_tarefa(tid)
