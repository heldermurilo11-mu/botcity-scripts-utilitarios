import argparse
import os
import sys
from datetime import datetime
from typing import Optional
import requests
from botcity.maestro import BotMaestroSDK

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        clean_str = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except Exception:
        return None


def parse_cli_date(date_str: str, end_of_day: bool = False) -> datetime:
    """Converte DD/MM/AAAA ou AAAA-MM-DD para datetime."""
    cleaned = date_str.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(cleaned, fmt)
            if end_of_day:
                return dt.replace(hour=23, minute=59, second=59)
            return dt
        except ValueError:
            pass
    raise ValueError(f"Formato de data inválido: '{date_str}'. Utilize DD/MM/AAAA ou AAAA-MM-DD.")


def buscar_todas_tarefas_filtro_data(start_str: str, end_str: str, size: int = 1000) -> None:
    dt_inicio = parse_cli_date(start_str, end_of_day=False)
    dt_fim = parse_cli_date(end_str, end_of_day=True)
    if dt_inicio > dt_fim:
        raise ValueError(f"Data inicial ({start_str}) não pode ser maior que a data final ({end_str}).")

    server = os.getenv("BOTCITY_SERVER", "https://developers.botcity.dev").strip()
    if not server.startswith("http"):
        server = f"https://{server}"

    login = os.getenv("BOTCITY_LOGIN")
    key = os.getenv("BOTCITY_KEY")
    workspace = os.getenv("BOTCITY_WORKSPACE", login)

    if not login or not key:
        raise ValueError("Variáveis BOTCITY_LOGIN e BOTCITY_KEY não configuradas no ambiente ou .env.")

    maestro = BotMaestroSDK(server=server, login=login, key=key)
    maestro.login()
    token = maestro.access_token

    headers = {
        "Authorization": f"Bearer {token}",
        "organization": workspace,
    }

    periodo_label = f"{dt_inicio.strftime('%d/%m/%Y')} a {dt_fim.strftime('%d/%m/%Y')}"
    print("=" * 80)
    print(f" 🔍 BUSCANDO TAREFAS NO MAESTRO (FILTRO: {periodo_label})")
    print("=" * 80)
    print(f"Servidor: {server} | Workspace: {workspace}\n")

    url_base = f"{server}/api/v2/task"
    tasks_filtradas = []

    resp = requests.get(url_base, headers=headers, params={"size": size})
    resp.raise_for_status()
    data = resp.json()
    items = data if isinstance(data, list) else data.get("tasks", data.get("content", []))

    for item in items:
        dt_c = parse_iso(item.get("dateCreation"))
        if dt_c:
            dt_c_naive = dt_c.replace(tzinfo=None)
            if dt_inicio <= dt_c_naive <= dt_fim:
                tasks_filtradas.append(item)

    print(f"Total de tarefas encontradas no período ({periodo_label}): {len(tasks_filtradas)}\n")

    atividades = {}
    for t in tasks_filtradas:
        lbl = t.get("activityLabel") or t.get("activityName") or t.get("activityId") or "Desconhecido"
        repo = t.get("repositoryLabel") or "N/A"
        key_group = f"{lbl} (Repo: {repo})"
        atividades.setdefault(key_group, []).append(t)

    print("📌 ATIVIDADES ENCONTRADAS NO PERÍODO:")
    for group_name, task_list in atividades.items():
        print(f"\n👉 Atividade: {group_name} | Total: {len(task_list)} tarefas")
        print(f"   {'Task ID':<10} | {'Status':<10} | {'Máquina':<12} | {'Data Criação':<20} | {'Mensagem':<30}")
        print("   " + "-" * 90)
        for t in task_list[:15]:
            tid = t.get("id")
            st = t.get("finishStatus") or t.get("state") or "UNKNOWN"
            mach = t.get("machineId") or "N/A"
            dt_c = t.get("dateCreation") or "N/A"
            msg = (t.get("finishMessage") or "")[:30]
            print(f"   #{tid:<9} | {st:<10} | {mach:<12} | {dt_c:<20} | {msg:<30}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pesquisa tarefas executadas no BotCity Maestro em um intervalo de datas.",
        epilog="Exemplo: python pesquisar_tarefas_datas.py --start 01/01/2026 --end 31/01/2026",
    )
    parser.add_argument(
        "--start",
        required=True,
        help="Data inicial no formato DD/MM/AAAA ou AAAA-MM-DD (ex: 01/01/2026).",
    )
    parser.add_argument(
        "--end",
        required=True,
        help="Data final no formato DD/MM/AAAA ou AAAA-MM-DD (ex: 31/01/2026).",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=1000,
        help="Quantidade máxima de registros consultados na API (padrão: 1000).",
    )

    args = parser.parse_args()
    buscar_todas_tarefas_filtro_data(args.start, args.end, size=args.size)
