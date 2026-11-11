import argparse
import os
from botcity.maestro import AutomationTaskFinishStatus, BotMaestroSDK

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv não instalado. As variáveis devem estar no ambiente.")


def encerrar_tarefa(
    task_id: str,
    status: str = "FAILED",
    message: str = "Encerrada via API a pedido do usuario.",
) -> None:
    """Autentica via .env e finaliza a tarefa especificada no BotCity Maestro."""
    server = os.getenv("BOTCITY_SERVER", "https://developers.botcity.dev").strip()
    if server and not server.startswith("http"):
        server = f"https://{server}"

    login = os.getenv("BOTCITY_LOGIN")
    key = os.getenv("BOTCITY_KEY")

    if not login or not key:
        raise ValueError(
            "Variáveis BOTCITY_LOGIN e BOTCITY_KEY não configuradas no ambiente ou .env."
        )

    maestro = BotMaestroSDK(
        server=server,
        login=login,
        key=key,
    )
    maestro.login()

    status_map = {
        "FAILED": AutomationTaskFinishStatus.FAILED,
        "SUCCESS": AutomationTaskFinishStatus.SUCCESS,
        "PARTIALLY_COMPLETED": AutomationTaskFinishStatus.PARTIALLY_COMPLETED,
    }
    status_enum = status_map[status.upper()]

    print(f"Finalizando task {task_id} no Maestro como {status_enum.value}...")
    maestro.finish_task(
        task_id=task_id,
        status=status_enum,
        message=message,
    )
    print("Tarefa finalizada com sucesso!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Encerra uma ou mais tarefas travadas no BotCity Maestro via CLI.",
        epilog="Exemplo: python encerrar_task.py 123456 FAILED 'Tarefa interrompida'",
    )
    parser.add_argument(
        "task_id",
        help="ID da tarefa (ou IDs separados por vírgula, ex: 123456).",
    )
    parser.add_argument(
        "status",
        nargs="?",
        default="FAILED",
        type=str.upper,
        choices=["FAILED", "SUCCESS", "PARTIALLY_COMPLETED"],
        help="Status final da tarefa (padrão: FAILED).",
    )
    parser.add_argument(
        "message",
        nargs="?",
        default="Encerrada via API a pedido do usuario.",
        help="Mensagem de encerramento registrada no Maestro.",
    )

    args = parser.parse_args()
    for tid in [item.strip() for item in args.task_id.split(",") if item.strip()]:
        try:
            encerrar_tarefa(tid, args.status, args.message)
        except Exception as exc:
            print(f"Erro ao encerrar a task {tid}: {exc}")
