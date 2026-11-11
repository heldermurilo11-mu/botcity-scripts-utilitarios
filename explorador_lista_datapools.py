import requests
from conexao_maestro import criar_maestro_local

def list_datapools():
    print("🔍 Listando todos os Datapools disponíveis no Maestro...")
    
    maestro = criar_maestro_local()
    if not maestro:
        return

    # Acessando via API para obter detalhes completos do JSON
    url = f'{maestro.server}/api/v2/datapool?size=1000'
    try:
        with requests.get(url, headers=maestro._headers(), verify=maestro.VERIFY_SSL_CERT) as req:
            if req.ok:
                data = req.json()
                content = data if isinstance(data, list) else data.get('content', [])
                
                print(f"{'NOME':<40} | {'LABEL':<30}")
                print("-" * 75)
                for dp in content:
                    print(f"{dp.get('name', 'N/A'):<40} | {dp.get('label', 'N/A'):<30}")
            else:
                print(f"❌ Falha ao consultar API: {req.status_code}")
    except Exception as e:
        print(f"❌ Erro na consulta: {e}")

if __name__ == "__main__":
    list_datapools()
