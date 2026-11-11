import os
import sys
from botcity.maestro import BotMaestroSDK

def upload_artefato(task_id: str, artifact_name: str, filepath: str):
    # Inicializa o SDK
    maestro = BotMaestroSDK.from_sys_args()

    if not os.path.exists(filepath):
        print(f"[ERRO] O arquivo especificado nao foi encontrado no caminho: {filepath}")
        return

    print(f"Fazendo upload de '{filepath}' como '{artifact_name}' para a task {task_id}...")
    try:
        maestro.post_artifact(
            task_id=task_id,
            artifact_name=artifact_name,
            filepath=filepath
        )
        print("Upload concluido com sucesso!")
    except Exception as e:
        print(f"[ERRO] Falha ao enviar o artefato para a API: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python upload_artefato.py <TASK_ID> <ARTIFACT_NAME> <LOCAL_FILEPATH>")
        print("Exemplo: python upload_artefato.py 123456 relatorio.xlsx ./output/relatorio.xlsx")
        sys.exit(1)

    tid = sys.argv[1]
    name = sys.argv[2]
    path = sys.argv[3]

    upload_artefato(tid, name, path)
