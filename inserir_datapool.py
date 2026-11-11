import sys
import json
from botcity.maestro import BotMaestroSDK

def inserir_item_datapool(datapool_label: str, item_json: str):
    # Inicializa o SDK
    maestro = BotMaestroSDK.from_sys_args()

    try:
        values = json.loads(item_json)
    except json.JSONDecodeError as e:
        print(f"[ERRO] Falha ao parsear string JSON fornecida: {e}")
        print("Certifique-se de usar aspas duplas internas para propriedades e valores. Ex: '{\"cpf\": \"123\"}'")
        return

    print(f"Inserindo item no Datapool '{datapool_label}'...")
    item = maestro.create_datapool_item(
        datapool_label=datapool_label,
        values=values
    )

    if item:
        print(f"Sucesso! Item criado no Maestro com ID: {item.id}")
    else:
        print("[ERRO] Falha ao criar o item. Verifique se o label do Datapool existe.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python inserir_datapool.py <DATAPOOL_LABEL> <ITEM_JSON_STRING>")
        print("Exemplo: python inserir_datapool.py MEU_DATAPOOL '{\"nome\": \"Joao\", \"idade\": 30}'")
        sys.exit(1)

    label = sys.argv[1]
    item_str = sys.argv[2]
    
    inserir_item_datapool(label, item_str)
