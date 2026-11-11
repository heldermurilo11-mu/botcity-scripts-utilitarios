import argparse
import math
import os
import sys
from datetime import datetime
from typing import List, Optional
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


def desvio_padrao(valores: List[float]) -> float:
    if len(valores) < 2:
        return 0.0
    media = sum(valores) / len(valores)
    variancia = sum((x - media) ** 2 for x in valores) / (len(valores) - 1)
    return math.sqrt(variancia)


def calcular_percentil(valores: List[float], percentil: float) -> float:
    if not valores:
        return 0.0
    sorted_v = sorted(valores)
    k = (len(sorted_v) - 1) * (percentil / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_v[int(k)])
    d0 = sorted_v[int(f)] * (c - k)
    d1 = sorted_v[int(c)] * (k - f)
    return float(d0 + d1)


def buscar_todas_tarefas_maestro(
    start_str: str,
    end_str: str,
    activity_filter: Optional[str] = None,
    size: int = 1000,
) -> None:
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

    periodo_label = f"{dt_inicio.strftime('%d/%m/%Y')} A {dt_fim.strftime('%d/%m/%Y')}"
    print("=" * 80)
    print(f" 🔍 ANALISANDO HISTÓRICO DO MAESTRO (FILTRO: {periodo_label})")
    print("=" * 80)
    print(f"Servidor: {server} | Workspace: {workspace}\n")

    resp = requests.get(f"{server}/api/v2/task", headers=headers, params={"size": size})
    resp.raise_for_status()

    raw_data = resp.json()
    items = raw_data if isinstance(raw_data, list) else raw_data.get("tasks", raw_data.get("content", []))

    print(f"Total de tarefas retornadas pelo Orquestrador: {len(items)}\n")

    tasks_periodo = []
    atividades_count = {}

    for t in items:
        dt_c = parse_iso(t.get("dateCreation"))
        if not dt_c:
            continue
        dt_c_naive = dt_c.replace(tzinfo=None)
        if dt_inicio <= dt_c_naive <= dt_fim:
            lbl = t.get("activityLabel") or t.get("activityName") or t.get("activityId") or "Desconhecido"
            if activity_filter and activity_filter.lower() not in str(lbl).lower():
                continue
            tasks_periodo.append(t)
            atividades_count[lbl] = atividades_count.get(lbl, 0) + 1

    print(f"Tarefas no período de {dt_inicio.strftime('%d/%m/%Y')} a {dt_fim.strftime('%d/%m/%Y')}: {len(tasks_periodo)}")
    print("Distribuição por Atividade:")
    for k, v in atividades_count.items():
        print(f" • {k}: {v} tarefas")
    print("-" * 80 + "\n")

    # Analisar distribuição de tempo por atividade encontrada no período
    for target_label in atividades_count.keys():
        tasks_bot = [
            t
            for t in tasks_periodo
            if (t.get("activityLabel") or t.get("activityName") or t.get("activityId") or "Desconhecido") == target_label
        ]

        print("=" * 80)
        print(f" ⏱️ ANÁLISE DE TEMPO (EM MINUTOS) — ATIVIDADE: {str(target_label).upper()}")
        print("=" * 80)
        print(f"Total de Execuções Encontradas: {len(tasks_bot)}\n")

        tempos_fila_min = []
        tempos_exec_min = []
        tempos_total_min = []
        tabela = []

        for t in tasks_bot:
            tid = t.get("id")
            dt_c = parse_iso(t.get("dateCreation"))
            dt_s = parse_iso(t.get("dateStartRunning"))
            dt_f = parse_iso(t.get("dateLastModified"))

            f_sec = (dt_s - dt_c).total_seconds() if (dt_s and dt_c) else 0.0
            e_sec = (dt_f - dt_s).total_seconds() if (dt_f and dt_s) else 0.0
            t_sec = (dt_f - dt_c).total_seconds() if (dt_f and dt_c) else 0.0

            f_min = f_sec / 60.0
            e_min = e_sec / 60.0
            tot_min = t_sec / 60.0

            pct_f = (f_min / tot_min * 100.0) if tot_min > 0 else 0.0
            pct_e = (e_min / tot_min * 100.0) if tot_min > 0 else 0.0

            tempos_fila_min.append(f_min)
            tempos_exec_min.append(e_min)
            tempos_total_min.append(tot_min)

            tabela.append({
                "id": tid,
                "dt_c": dt_c.strftime("%d/%m/%Y %H:%M") if dt_c else "N/A",
                "dt_s": dt_s.strftime("%H:%M:%S") if dt_s else "N/A",
                "dt_f": dt_f.strftime("%H:%M:%S") if dt_f else "N/A",
                "f_min": f_min,
                "e_min": e_min,
                "tot_min": tot_min,
                "pct_f": pct_f,
                "pct_e": pct_e,
                "status": t.get("finishStatus") or t.get("state") or "UNKNOWN",
            })

        tabela.sort(
            key=lambda x: (0, int(x["id"])) if str(x["id"]).isdigit() else (1, str(x["id"] or ""))
        )

        print(" ┌──────────┬──────────────────┬──────────┬──────────┬──────────────┬──────────────┬──────────────┬──────────┬──────────┬────────────┐")
        print(" │ Task ID  │ Data/Hora Criar  │ Início   │ Término  │ Fila (min)   │ Exec (min)   │ Total (min)  │ % Fila   │ % Exec   │ Status     │")
        print(" ├──────────┼──────────────────┼──────────┼──────────┼──────────────┼──────────────┼──────────────┼──────────┼──────────┼────────────┤")
        for row in tabela[:30]:
            print(
                f" │ #{str(row['id']):<7} │ {row['dt_c']} │ {row['dt_s']} │ {row['dt_f']} │ "
                f"{row['f_min']:>10.2f}m │ {row['e_min']:>10.2f}m │ {row['tot_min']:>10.2f}m │ "
                f"{row['pct_f']:>6.1f}% │ {row['pct_e']:>6.1f}% │ {row['status']:<10} │"
            )
        print(" └──────────┴──────────────────┴──────────┴──────────┴──────────────┴──────────────┴──────────────┴──────────┴──────────┴────────────┘")
        if len(tabela) > 30:
            print(f"   ... e mais {len(tabela) - 30} tarefas.")

        if tempos_exec_min:
            m_f = sum(tempos_fila_min) / len(tempos_fila_min)
            m_e = sum(tempos_exec_min) / len(tempos_exec_min)
            m_t = sum(tempos_total_min) / len(tempos_total_min)
            med_f = calcular_percentil(tempos_fila_min, 50)
            med_e = calcular_percentil(tempos_exec_min, 50)
            med_t = calcular_percentil(tempos_total_min, 50)
            p90_f = calcular_percentil(tempos_fila_min, 90)
            p90_e = calcular_percentil(tempos_exec_min, 90)
            p90_t = calcular_percentil(tempos_total_min, 90)

            print(f"\n📊 RESUMO ESTATÍSTICO DE TEMPO ({target_label}):")
            print(
                f" • Tempo em Fila (min):      Médio: {m_f:.2f} min | Mediana: {med_f:.2f} min | "
                f"Mín: {min(tempos_fila_min):.2f} min | Máx: {max(tempos_fila_min):.2f} min | P90: {p90_f:.2f} min"
            )
            print(
                f" • Tempo de Execução (min):  Médio: {m_e:.2f} min | Mediana: {med_e:.2f} min | "
                f"Mín: {min(tempos_exec_min):.2f} min | Máx: {max(tempos_exec_min):.2f} min | P90: {p90_e:.2f} min"
            )
            print(
                f" • Tempo Total (min):        Médio: {m_t:.2f} min | Mediana: {med_t:.2f} min | "
                f"Mín: {min(tempos_total_min):.2f} min | Máx: {max(tempos_total_min):.2f} min | P90: {p90_t:.2f} min\n"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analisa tempos de fila e execução das tarefas do BotCity Maestro em um período.",
        epilog="Exemplo: python analise_historica_completa.py --start 01/01/2026 --end 31/01/2026",
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
        "--activity",
        default=None,
        help="Filtro opcional por nome/label da atividade (ex: MinhaAutomacao).",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=1000,
        help="Quantidade máxima de tarefas consultadas na API (padrão: 1000).",
    )

    args = parser.parse_args()
    buscar_todas_tarefas_maestro(
        start_str=args.start,
        end_str=args.end,
        activity_filter=args.activity,
        size=args.size,
    )
