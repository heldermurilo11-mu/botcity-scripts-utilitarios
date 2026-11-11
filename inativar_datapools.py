import argparse
import os
import re
import sys
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
import requests
from botcity.maestro import BotMaestroSDK
from dotenv import load_dotenv

# Garantir UTF-8 no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()


def obter_cliente_maestro() -> BotMaestroSDK:
    """Inicializa e autentica o SDK do BotCity Maestro."""
    server = os.getenv("BOTCITY_SERVER", "https://developers.botcity.dev").strip()
    if not server.startswith("http"):
        server = f"https://{server}"

    login = os.getenv("BOTCITY_LOGIN")
    key = os.getenv("BOTCITY_KEY")

    if not login or not key:
        raise ValueError(
            "[ERRO] Variáveis BOTCITY_LOGIN e BOTCITY_KEY não configuradas no ambiente ou no arquivo .env."
        )

    maestro = BotMaestroSDK(server=server, login=login, key=key)
    maestro.login()
    return maestro


def parse_data(data_str: str) -> date:
    """Converte string no formato DD/MM/AAAA ou AAAA-MM-DD para objeto date."""
    data_str = data_str.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(data_str, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Formato de data inválido: '{data_str}'. Utilize DD/MM/AAAA ou AAAA-MM-DD.")


def normalizar_prefixos(raw_prefixes: List[str]) -> List[str]:
    """Normaliza prefixos informados via CLI (aceita itens separados por espaço ou vírgula)."""
    parsed = [
        p.strip().rstrip("*")
        for item in raw_prefixes
        for p in item.split(",")
        if p.strip().rstrip("*")
    ]
    if not parsed:
        raise ValueError("Informe ao menos um prefixo válido em --prefix (ex: fila_exemplo_).")
    return parsed


def extrair_data_datapool(label: str, name: str) -> Optional[date]:
    """
    Identifica a data de referência do Datapool a partir do label ou name.

    Formatos suportados:
      - processo_exemplo_15_01_2026 (DD_MM_YYYY)
      - fila_exemplo_26_01_15 (YY_MM_DD)
      - 15/01/26 - Fila Exemplo (DD/MM/YY ou DD/MM/YYYY no nome)
    """
    label = label or ""
    name = name or ""

    # 1. DD_MM_YYYY no label (ex: processo_exemplo_15_01_2026)
    m = re.search(r"(\d{2})_(\d{2})_(\d{4})", label)
    if m:
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date()
        except ValueError:
            pass

    # 2. YY_MM_DD no label (ex: fila_exemplo_26_01_15)
    m = re.search(r"(?:^|_)(\d{2})_(\d{2})_(\d{2})(?:$|_)", label)
    if m:
        try:
            ano = int(m.group(1)) + 2000
            mes = int(m.group(2))
            dia = int(m.group(3))
            return datetime(ano, mes, dia).date()
        except ValueError:
            pass

    # 3. DD/MM/YY ou DD/MM/YYYY no nome (ex: 15/01/26 - Fila Exemplo)
    m = re.search(r"(\d{2})/(\d{2})/(\d{2,4})", name)
    if m:
        try:
            dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if ano < 100:
                ano += 2000
            return datetime(ano, mes, dia).date()
        except ValueError:
            pass

    return None


def listar_todos_datapools(maestro: BotMaestroSDK) -> List[Dict[str, Any]]:
    """Consulta paginada para recuperar todos os Datapools da organização."""
    headers = maestro._headers()
    url = f"{maestro.server}/api/v2/datapool"

    page = 0
    total_pages = 1
    todos = []

    while page < total_pages:
        resp = requests.get(url, headers=headers, params={"size": 100, "page": page})
        resp.raise_for_status()
        data = resp.json()
        total_pages = data.get("totalPages", 1)
        itens = data.get("content", [])
        todos.extend(itens)
        page += 1

    return todos


def inativar_datapools_por_periodo(
    data_inicio_str: str,
    data_fim_str: str,
    prefixes: List[str],
    dry_run: bool = False,
    force: bool = False,
    preservar_extra: Optional[List[str]] = None,
) -> None:
    """
    Filtra os Datapools ativos pelos prefixos e pela data de referência,
    inativando os que estiverem dentro do intervalo [data_inicio, data_fim].
    """
    dt_inicio = parse_data(data_inicio_str)
    dt_fim = parse_data(data_fim_str)
    prefixes_norm = normalizar_prefixos(prefixes)
    prefixes_lower = [p.lower() for p in prefixes_norm]

    if dt_inicio > dt_fim:
        raise ValueError(f"Data inicial ({dt_inicio}) não pode ser maior que data final ({dt_fim}).")

    preservar_set = set(p.lower().strip() for p in (preservar_extra or []) if p.strip())

    print("=" * 80)
    print(" ⏸️  INATIVAÇÃO DE DATAPOOLS POR PERÍODO — BOTCITY MAESTRO")
    print("=" * 80)
    print(f"Período Alvo:   {dt_inicio.strftime('%d/%m/%Y')} até {dt_fim.strftime('%d/%m/%Y')} (inclusive)")
    print(f"Prefixos Alvo:  {', '.join(prefixes_norm)}")
    print(f"Modo:           {'SIMULAÇÃO (--dry-run)' if dry_run else 'EXECUÇÃO REAL'}")

    maestro = obter_cliente_maestro()
    workspace = getattr(maestro, "organization", None) or os.getenv("BOTCITY_WORKSPACE") or os.getenv("BOTCITY_LOGIN")
    print(f"Servidor:       {maestro.server}")
    print(f"Workspace:      {workspace}\n")

    print("-> Consultando Datapools cadastrados no Orchestrator...")
    todos_dps = listar_todos_datapools(maestro)
    print(f"-> Total geral de Datapools encontrados: {len(todos_dps)}")

    ativos = [dp for dp in todos_dps if dp.get("active") is True]
    ja_inativos = [dp for dp in todos_dps if dp.get("active") is not True]

    print(f"   • Já inativos: {len(ja_inativos)}")
    print(f"   • Ativos:      {len(ativos)}\n")

    para_inativar: List[Tuple[Dict[str, Any], date]] = []
    permanecem_ativos: List[Tuple[Dict[str, Any], Optional[date], str]] = []

    for dp in ativos:
        label = (dp.get("label") or "").strip()
        nome = (dp.get("name") or "").strip()
        lbl_lower = label.lower()
        nm_lower = nome.lower()

        if lbl_lower in preservar_set or nm_lower in preservar_set:
            permanecem_ativos.append((dp, None, "Exceção configurada (--preservar)"))
            continue

        if not any(p in lbl_lower or p in nm_lower for p in prefixes_lower):
            permanecem_ativos.append((dp, None, "Fora do filtro (--prefix)"))
            continue

        dt_referencia = extrair_data_datapool(label, nome)

        if dt_referencia is None:
            permanecem_ativos.append((dp, None, "Sem data identificada (preservado)"))
            continue

        if dt_inicio <= dt_referencia <= dt_fim:
            para_inativar.append((dp, dt_referencia))
        else:
            motivo = f"Fora do período ({dt_referencia.strftime('%d/%m/%Y')})"
            permanecem_ativos.append((dp, dt_referencia, motivo))

    para_inativar.sort(key=lambda x: (x[1], x[0].get("label", "")))

    print("-" * 80)
    print(f" 🛡️  DATAPOOLS QUE PERMANECERÃO ATIVOS ({len(permanecem_ativos)})")
    print("-" * 80)
    for dp, dt, motivo in permanecem_ativos:
        dt_str = dt.strftime("%d/%m/%Y") if dt else "  --/--/----  "
        print(f" [MANTIDO ATIVO] {dt_str} | Label: {dp.get('label'):<30} | {motivo}")

    print("\n" + "-" * 80)
    print(f" 🎯 DATAPOOLS IDENTIFICADOS PARA INATIVAÇÃO ({len(para_inativar)})")
    print("-" * 80)

    if not para_inativar:
        print("Nenhum datapool ativo encontrado para os filtros informados.")
        return

    for idx, (dp, dt) in enumerate(para_inativar, 1):
        print(
            f" {idx:2d}. {dt.strftime('%d/%m/%Y')} | Label: {dp.get('label'):<30} | Nome: {dp.get('name')}"
        )

    if dry_run:
        print("\n[INFO] Modo --dry-run ativo. Nenhuma alteração foi realizada no BotCity Maestro.")
        return

    if not force and sys.stdin.isatty():
        print()
        resp = input(
            f"Deseja inativar os {len(para_inativar)} Datapools listados acima? [s/N]: "
        ).strip().lower()
        if resp not in ["s", "sim", "y", "yes"]:
            print("[CANCELADO] Operação cancelada pelo usuário. Nenhuma alteração foi efetuada.")
            return

    print("\n" + "=" * 80)
    print(" 🚀 INICIANDO INATIVAÇÃO DOS DATAPOOLS...")
    print("=" * 80)

    sucessos = 0
    falhas = 0

    for idx, (dp, dt) in enumerate(para_inativar, 1):
        label = dp.get("label")
        print(
            f"[{idx:2d}/{len(para_inativar)}] {dt.strftime('%d/%m/%Y')} -> Inativando '{label}'...",
            end=" ",
            flush=True,
        )

        try:
            dp_obj = maestro.get_datapool(label)
            if dp_obj.deactivate():
                print("✅ [INATIVADO]")
                sucessos += 1
            else:
                print("⚠️ [STATUS NÃO ALTERADO]")
                falhas += 1
        except Exception as exc:
            print(f"❌ [ERRO: {exc}]")
            falhas += 1

        time.sleep(0.15)  # Respeito ao rate limit da API BotCity

    print("\n" + "=" * 80)
    print(" 🏁 RELATÓRIO FINAL")
    print("=" * 80)
    print(f"Período processado:     {dt_inicio.strftime('%d/%m/%Y')} até {dt_fim.strftime('%d/%m/%Y')}")
    print(f"Total avaliado:         {len(para_inativar)}")
    print(f"Inativados com sucesso: {sucessos}")
    print(f"Falhas / Erros:         {falhas}")
    print(f"Permanecem ativos:      {len(permanecem_ativos)}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inativa Datapools ativos no BotCity Maestro dentro de um intervalo de datas e prefixo.",
        epilog="Exemplo: python inativar_datapools.py --start 01/01/2026 --end 31/01/2026 --prefix fila_exemplo_ --dry-run",
    )
    parser.add_argument(
        "--start",
        "--data-inicio",
        dest="start",
        required=True,
        help="Data inicial no formato DD/MM/AAAA ou AAAA-MM-DD (ex: 01/01/2026).",
    )
    parser.add_argument(
        "--end",
        "--data-fim",
        dest="end",
        required=True,
        help="Data final no formato DD/MM/AAAA ou AAAA-MM-DD (ex: 31/01/2026).",
    )
    parser.add_argument(
        "--prefix",
        nargs="+",
        required=True,
        help="Prefixo(s) de label/nome de Datapools a inativar (ex: fila_exemplo_).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula a execução e lista os Datapools sem efetuar nenhuma inativação.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        "--force",
        dest="force",
        action="store_true",
        help="Executa a inativação direta sem solicitar confirmação interativa no terminal.",
    )
    parser.add_argument(
        "--preservar",
        nargs="*",
        default=[],
        help="Labels ou nomes de Datapools adicionais para preservar ativos (ex: fila_principal).",
    )

    args = parser.parse_args()
    inativar_datapools_por_periodo(
        data_inicio_str=args.start,
        data_fim_str=args.end,
        prefixes=args.prefix,
        dry_run=args.dry_run,
        force=args.force,
        preservar_extra=args.preservar,
    )
