import argparse
import os
from typing import List, Optional
import requests
from conexao_maestro import (
    criar_maestro_local,
    filtrar_datapools_por_prefixos,
    resolve_datapool_prefixes,
)


def exportar_historico(cli_prefixes: Optional[List[str]] = None, limit: int = 31) -> None:
    """Exporta em CSV o histórico recente dos Datapools filtrados por prefixo."""
    prefixes = resolve_datapool_prefixes(cli_prefixes)
    print(f"📥 Iniciando download em massa de CSVs dos Datapools (até {limit} mais recentes)...")
    print(f"🔎 Prefixos configurados: {', '.join(prefixes)}")

    maestro = criar_maestro_local()
    if not maestro:
        return

    server = maestro.server.rstrip("/")
    headers = maestro._headers()

    # 1. Obter a lista de datapools
    url_list = f"{server}/api/v2/datapool?size=500&sort=id,desc"

    try:
        resp = requests.get(url_list, headers=headers, timeout=30, verify=maestro.VERIFY_SSL_CERT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"❌ Falha ao listar datapools: {e}")
        return

    content = data if isinstance(data, list) else data.get("content", [])

    # 2. Filtrar os últimos N relevantes
    datapools_alvo = filtrar_datapools_por_prefixos(content, prefixes, limit=limit)
    print(f"📂 Total de datapools identificados: {len(datapools_alvo)}\n")

    output_dir = "output/exportacao_datapools"
    os.makedirs(output_dir, exist_ok=True)

    # 3. Baixar os arquivos
    for idx, (_dp_name, dp_label) in enumerate(datapools_alvo, 1):
        print(f"[{idx}/{len(datapools_alvo)}] Baixando: {dp_label}.csv...")

        url_export = f"{server}/api/v2/datapool/{dp_label}/export"
        try:
            r = requests.get(url_export, headers=headers, timeout=30, verify=maestro.VERIFY_SSL_CERT)

            if r.status_code == 200:
                arquivo_csv = f"{output_dir}/{dp_label}.csv"
                with open(arquivo_csv, "wb") as f:
                    f.write(r.content)
                print("      ✅ Salvo!")
            else:
                print(f"      ⚠️ Falha (Status {r.status_code})")

        except Exception as e:
            print(f"      ❌ Erro de conexão: {e}")

    print(f"\n✨ Exportação concluída em: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Exporta CSVs do histórico de Datapools do BotCity Maestro."
    )
    parser.add_argument(
        "--prefix",
        nargs="+",
        default=None,
        help="Prefixo(s) de Datapool para filtrar (ou use DATAPOOL_PREFIXES no .env; padrão: fila_exemplo_).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=31,
        help="Quantidade máxima de Datapools recentes para exportar (padrão: 31).",
    )
    args = parser.parse_args()
    exportar_historico(cli_prefixes=args.prefix, limit=args.limit)
