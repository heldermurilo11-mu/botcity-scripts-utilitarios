import os
import re
from typing import Iterable, List, Optional, Tuple
from botcity.maestro import BotMaestroSDK
from dotenv import load_dotenv

DEFAULT_DATAPOOL_PREFIXES = ["fila_exemplo_"]


def normalize_server_url(server: str) -> str:
    """Garante esquema https:// e remove barra final da URL do Maestro."""
    value = (server or "").strip()
    if not value:
        return value
    if not re.match(r"^https?://", value, flags=re.IGNORECASE):
        value = f"https://{value}"
    return value.rstrip("/")


def resolve_datapool_prefixes(
    cli_prefixes: Optional[Iterable[str]] = None,
    default: Optional[List[str]] = None,
) -> List[str]:
    """
    Resolve a lista de prefixos de Datapool por ordem de prioridade:
    1) Argumento CLI (--prefix)
    2) Variavel de ambiente DATAPOOL_PREFIXES (separada por virgula)
    3) Padrao generico ['fila_exemplo_']
    """
    load_dotenv()

    if cli_prefixes:
        parsed = [
            p.strip().rstrip("*")
            for item in cli_prefixes
            for p in item.split(",")
            if p.strip().rstrip("*")
        ]
        if parsed:
            return parsed

    env_prefixes = os.getenv("DATAPOOL_PREFIXES", "").strip()
    if env_prefixes:
        parsed = [
            p.strip().rstrip("*")
            for p in env_prefixes.split(",")
            if p.strip().rstrip("*")
        ]
        if parsed:
            return parsed

    return list(default if default is not None else DEFAULT_DATAPOOL_PREFIXES)


def filtrar_datapools_por_prefixos(
    content: Iterable[dict],
    prefixes: Iterable[str],
    limit: Optional[int] = None,
) -> List[Tuple[str, str]]:
    """Filtra Datapools cujo nome ou label corresponda a algum prefixo."""
    normalized = [p.lower() for p in prefixes if p]
    datapools_alvo: List[Tuple[str, str]] = []

    for dp in content:
        label = dp.get("label", "") or ""
        name = dp.get("name", "") or ""
        label_lower = label.lower()
        name_lower = name.lower()

        if any(p in name_lower or p in label_lower for p in normalized):
            datapools_alvo.append((name, label))
            if limit is not None and len(datapools_alvo) >= limit:
                break

    return datapools_alvo


def criar_maestro_local() -> Optional[BotMaestroSDK]:
    """Inicializa o Maestro para execução local/manual usando .env."""
    load_dotenv()

    server = normalize_server_url(os.getenv("BOTCITY_SERVER", ""))
    login = os.getenv("BOTCITY_LOGIN", "").strip()
    key = os.getenv("BOTCITY_KEY", "").strip()

    if not all([server, login, key]):
        print("❌ Erro: Faltam credenciais do Maestro no arquivo .env")
        return None

    try:
        maestro = BotMaestroSDK(server=server, login=login, key=key)
        maestro.login()
        # Mock task_id para evitar erros em chamadas que dependem dele
        maestro.task_id = "LOCAL_UTILITY"
        return maestro
    except Exception as e:
        print(f"❌ Erro ao conectar ao Maestro: {e}")
        return None
