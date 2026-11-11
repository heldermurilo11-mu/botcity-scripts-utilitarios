import argparse
import os
from botcity.maestro import AutomationTaskFinishStatus, BotMaestroSDK
from dotenv import load_dotenv

load_dotenv()


def finish_task(
    task_id: str,
    status: str,
    message: str,
    total_items: int,
    processed_items: int,
    failed_items: int,
) -> None:
    """Finaliza uma tarefa no BotCity Maestro usando o SDK com métricas de itens."""
    server = os.getenv("BOTCITY_SERVER", "https://developers.botcity.dev").strip()
    if server and not server.startswith("http"):
        server = f"https://{server}"

    login = os.getenv("BOTCITY_LOGIN")
    key = os.getenv("BOTCITY_KEY")

    if not all([login, key]):
        print("Erro: Credenciais do Maestro não encontradas.")
        print("Configure as variáveis BOTCITY_LOGIN e BOTCITY_KEY no arquivo .env")
        return

    status_map = {
        "SUCCESS": AutomationTaskFinishStatus.SUCCESS,
        "FAILED": AutomationTaskFinishStatus.FAILED,
        "PARTIALLY_COMPLETED": AutomationTaskFinishStatus.PARTIALLY_COMPLETED,
    }
    finish_status = status_map[status.upper()]

    try:
        print(f"Conectando ao Maestro em: {server}...")
        maestro = BotMaestroSDK(server=server, login=login, key=key)
        maestro.login()

        print(f"Finalizando tarefa {task_id} com status {status.upper()}...")
        maestro.finish_task(
            task_id=task_id,
            status=finish_status,
            message=message,
            total_items=total_items,
            processed_items=processed_items,
            failed_items=failed_items,
        )
        print(f"✅ Sucesso: Tarefa {task_id} finalizada corretamente.")
    except Exception as exc:
        print(f"❌ Erro ao finalizar tarefa {task_id}: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Utilitário BotCity para finalizar tarefas presas com reporte de métricas.",
        epilog="Exemplo: python finish_task.py 123456 --status SUCCESS --total 10 --processed 10",
    )
    parser.add_argument("task_id", help="ID da tarefa (ou lista separada por vírgula, ex: 123456)")
    parser.add_argument(
        "--status",
        type=str.upper,
        choices=["SUCCESS", "FAILED", "PARTIALLY_COMPLETED"],
        default="SUCCESS",
        help="Status final da tarefa (padrão: SUCCESS)",
    )
    parser.add_argument("--message", default="Finalizada via CLI Utility", help="Mensagem de conclusão")
    parser.add_argument("--total", type=int, default=0, help="Total de itens")
    parser.add_argument("--processed", type=int, default=0, help="Itens processados")
    parser.add_argument("--failed", type=int, default=0, help="Itens com falha")

    args = parser.parse_args()
    for tid in [item.strip() for item in args.task_id.split(",") if item.strip()]:
        finish_task(
            task_id=tid,
            status=args.status,
            message=args.message,
            total_items=args.total,
            processed_items=args.processed,
            failed_items=args.failed,
        )
