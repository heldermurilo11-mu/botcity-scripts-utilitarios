import sys
from botcity.maestro import BotMaestroSDK, AlertType

def enviar_alerta(task_id: str, title: str, message: str, alert_type: str = "ERROR"):
    # Inicializa o SDK
    maestro = BotMaestroSDK.from_sys_args()

    # Mapeamento do tipo de alerta
    type_enum = AlertType.ERROR
    if alert_type.upper() == "WARN":
        type_enum = AlertType.WARN
    elif alert_type.upper() == "INFO":
        type_enum = AlertType.INFO

    print(f"Enviando alerta de tipo {type_enum.value} para a task {task_id}...")
    maestro.alert(
        task_id=task_id,
        title=title,
        message=message,
        alert_type=type_enum
    )
    print("Alerta registrado com sucesso no Maestro!")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python enviar_alerta.py <TASK_ID> <TITULO> <MENSAGEM> [ALERT_TYPE: INFO/WARN/ERROR]")
        print("Exemplo: python enviar_alerta.py 123456 'Erro na Planilha' 'A aba principal nao foi localizada' ERROR")
        sys.exit(1)

    tid = sys.argv[1]
    ttl = sys.argv[2]
    msg = sys.argv[3]
    tp = sys.argv[4] if len(sys.argv) > 4 else "ERROR"

    enviar_alerta(tid, ttl, msg, tp)
