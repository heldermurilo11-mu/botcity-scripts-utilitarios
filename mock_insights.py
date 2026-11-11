import os
import sys
import time
import random
from botcity.maestro import BotMaestroSDK, AutomationTaskFinishStatus

def popular_insights(activity_label: str, quantidade: int = 5):
    """
    Cria e finaliza execuções simuladas (fictícias) no BotCity Maestro para
    popular os gráficos de ROI, taxa de sucesso e performance no BotCity Insights.
    """
    # Inicializa o SDK (busca as credenciais do .env ou variáveis de ambiente locais)
    maestro = BotMaestroSDK.from_sys_args()

    print("=================================================================")
    print(f" Iniciando simulador de execuções para o BotCity Insights")
    print(f" Atividade Alvo: {activity_label}")
    print(f" Quantidade de Tasks: {quantidade}")
    print("=================================================================\n")

    for i in range(1, quantidade + 1):
        print(f"[{i}/{quantidade}] Criando tarefa simulada no Orchestrator...")
        try:
            # 1. Cria a tarefa no Maestro com parâmetros simulados
            task = maestro.create_task(
                activity_label=activity_label,
                parameters={
                    "simulado": True,
                    "id_lote": f"LOTE-MOCK-{random.randint(1000, 9999)}",
                    "iteracao": i
                },
                priority=random.randint(3, 8)
            )
            task_id = task.id
            print(f" -> Tarefa criada com ID: {task_id}")

            # 2. Simula um tempo de execução realista (entre 2 a 6 segundos)
            exec_duration = random.uniform(2.0, 6.0)
            print(f" -> Processando lote... (tempo estimado: {exec_duration:.2f}s)")
            time.sleep(exec_duration)

            # 3. Gera métricas aleatórias para o Insights
            total_items = random.randint(20, 180)
            # Simula até 10% de falhas
            failed_items = random.randint(0, int(total_items * 0.10))
            processed_items = total_items - failed_items

            # 4. Define o status final com base nos itens processados
            if failed_items == 0:
                status = AutomationTaskFinishStatus.SUCCESS
                message = f"Processamento concluído com sucesso total. Todos os {total_items} itens foram integrados."
            elif failed_items < (total_items * 0.05):
                status = AutomationTaskFinishStatus.PARTIALLY_COMPLETED
                message = f"Processamento concluído com falhas menores. Sucessos: {processed_items}, Falhas: {failed_items}."
            else:
                status = AutomationTaskFinishStatus.FAILED
                message = f"Lote interrompido por excesso de inconsistências. Falhas registradas: {failed_items}."

            # 5. Finaliza a tarefa no Maestro reportando os dados de ROI
            print(f" -> Finalizando task com status {status.value} (Itens: {total_items} | OK: {processed_items} | Erros: {failed_items})")
            maestro.finish_task(
                task_id=task_id,
                status=status,
                message=message,
                total_items=total_items,
                processed_items=processed_items,
                failed_items=failed_items
            )
            print(f" -> OK! Execução {i} integrada.\n")

        except Exception as e:
            print(f"[ERRO] Falha ao processar a simulação da execução {i}: {e}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python mock_insights.py <ACTIVITY_LABEL> [QUANTIDADE]")
        print("Exemplo: python mock_insights.py MinhaAutomacao 5")
        sys.exit(1)

    label = sys.argv[1]
    qty = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    popular_insights(label, qty)
