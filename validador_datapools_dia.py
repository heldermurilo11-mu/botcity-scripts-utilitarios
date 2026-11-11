import argparse
import datetime
from typing import List, Optional
from conexao_maestro import criar_maestro_local, resolve_datapool_prefixes


def check_datapool(
    cli_prefixes: Optional[List[str]] = None,
    date_label: Optional[str] = None,
) -> None:
    """Verifica a existência e status ativo/inativo das filas diárias no Maestro."""
    prefixes = resolve_datapool_prefixes(cli_prefixes)
    hoje_label = date_label or datetime.datetime.now().strftime("%y_%m_%d")

    print("📅 Verificando existência das filas no Maestro...")
    print(f"🔎 Prefixos: {', '.join(prefixes)} | Sufixo de data: {hoje_label}")

    maestro = criar_maestro_local()
    if not maestro:
        return

    labels_to_check = [f"{prefix}{hoje_label}" for prefix in prefixes]

    for target_label in labels_to_check:
        print(f"\nProcurando datapool: {target_label}")
        try:
            datapool = maestro.get_datapool(label=target_label)
            status = "ATIVO" if datapool.active else "INATIVO"
            print(f"✅ Encontrado! | Status: {status}")
        except Exception:
            print("❌ Não encontrado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Valida a existência dos Datapools diários no BotCity Maestro."
    )
    parser.add_argument(
        "--prefix",
        nargs="+",
        default=None,
        help="Prefixo(s) de Datapool a verificar (ou use DATAPOOL_PREFIXES no .env; padrão: fila_exemplo_).",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Sufixo de data no formato YY_MM_DD (padrão: data atual).",
    )
    args = parser.parse_args()
    check_datapool(cli_prefixes=args.prefix, date_label=args.date)
