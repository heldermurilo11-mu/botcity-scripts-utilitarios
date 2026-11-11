import argparse
import io
import os
from typing import List, Optional
import pandas as pd
import requests
from conexao_maestro import (
    criar_maestro_local,
    filtrar_datapools_por_prefixos,
    resolve_datapool_prefixes,
)


def calculate_lifecycle(cli_prefixes: Optional[List[str]] = None) -> None:
    """Calcula métricas histórica, mensal e semanal de ciclo de vida dos Datapools."""
    prefixes = resolve_datapool_prefixes(cli_prefixes)
    print("🚀 Iniciando análise de Ciclo de Vida dos Datapools...")
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

    # 2. Filtrar apenas datapools correspondentes aos prefixos informados
    datapools_alvo = filtrar_datapools_por_prefixos(content, prefixes)
    print(f"📊 Total de datapools filtrados para análise: {len(datapools_alvo)}\n")

    all_dataframes = []

    # 3. Baixar dados via API e carregar no Pandas
    for idx, (dp_name, dp_label) in enumerate(datapools_alvo, 1):
        print(f"[{idx}/{len(datapools_alvo)}] Extraindo dados de: {dp_name}...")

        url_export = f"{server}/api/v2/datapool/{dp_label}/export"
        try:
            r = requests.get(url_export, headers=headers, timeout=30, verify=maestro.VERIFY_SSL_CERT)
            if r.status_code == 200:
                df = pd.read_csv(io.BytesIO(r.content), encoding="utf-8", encoding_errors="replace")

                if "date Register" in df.columns and "date Finished" in df.columns:
                    df = df[["date Register", "date Processing", "date Finished", "state"]].copy()
                    df["Datapool"] = dp_label
                    all_dataframes.append(df)
            else:
                print(f"      ⚠️ Erro {r.status_code}: Falha ao exportar.")
        except Exception as e:
            print(f"      ⚠️ Erro de conexão ao baixar {dp_label}: {e}")

    if not all_dataframes:
        print("\n❌ Nenhum dado com datas válidas encontrado.")
        return

    # Concatenar todos os dataframes
    df_all = pd.concat(all_dataframes, ignore_index=True)

    # Converter colunas para datetime
    df_all["date Register"] = pd.to_datetime(df_all["date Register"], errors="coerce")
    df_all["date Finished"] = pd.to_datetime(df_all["date Finished"], errors="coerce")

    # Filtrar itens com data de término
    df_calc = df_all.dropna(subset=["date Register", "date Finished"]).copy()

    if len(df_calc) == 0:
        print("❌ Nenhum item válido para calcular médias.")
        return

    # Cálculo do Ciclo de Vida
    df_calc["Lifecycle"] = df_calc["date Finished"] - df_calc["date Register"]
    df_calc["Lifecycle_hours"] = df_calc["Lifecycle"].dt.total_seconds() / 3600.0

    # Agrupamentos
    df_calc["YearMonth"] = df_calc["date Register"].dt.to_period("M")
    df_calc["YearWeek"] = df_calc["date Register"].dt.to_period("W")

    media_historica = df_calc["Lifecycle_hours"].mean()
    media_mensal = df_calc.groupby("YearMonth")["Lifecycle_hours"].mean()
    media_semanal = df_calc.groupby("YearWeek")["Lifecycle_hours"].mean()

    # --- RESULTADOS ---
    print("\n" + "=" * 60)
    print("🏆 RELATÓRIO DE MÉTRICAS DE CICLO DE VIDA")
    print("=" * 60)
    print(f"Média Histórica Global: {media_historica:.2f} horas\n")

    print("Média Mensal (em horas):")
    for mes, valor in media_mensal.items():
        print(f"  📅 {mes}: {valor:.2f} h")

    print("\nMédia Semanal (em horas):")
    for sem, valor in media_semanal.items():
        print(f"  🗓️ {sem}: {valor:.2f} h")

    print("=" * 60)

    # Salvar Consolidação
    os.makedirs("output", exist_ok=True)
    arquivo_saida = "output/consolidado_lifecycle.csv"
    df_calc.to_csv(arquivo_saida, index=False)
    print(f"✅ Dados salvos em: {arquivo_saida}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analisa métricas de ciclo de vida de Datapools no BotCity Maestro."
    )
    parser.add_argument(
        "--prefix",
        nargs="+",
        default=None,
        help="Prefixo(s) de Datapool para filtrar (ou use DATAPOOL_PREFIXES no .env; padrão: fila_exemplo_).",
    )
    args = parser.parse_args()
    calculate_lifecycle(cli_prefixes=args.prefix)
