import requests
import json
import os

# mapeia os diretórios para salvar o cache
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def extrair_matchup_terceiros():
    print("Conectando na API oculta e puxando os dados de matchup...")
    url = "https://pb89hpsof3.execute-api.us-east-1.amazonaws.com/prod/escalar/rodadas_anteriores/10"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        dados = response.json()
        
        # salva o arquivo localmente
        caminho_arquivo = os.path.join(DATA_DIR, 'matchup.json')
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
            
        print(f"Dados de Matchup e Pontos Cedidos salvos com sucesso em: {caminho_arquivo}")
        
        # faz uma leitura rápida só para ver o que veio no pacote
        if isinstance(dados, list) and len(dados) > 0:
            print("\n--- AMOSTRA DOS DADOS RECEBIDOS ---")
            print(f"Total de registros encontrados: {len(dados)}")
            print("Chaves do primeiro item para mapearmos no algoritmo:")
            print(list(dados[0].keys()))
        elif isinstance(dados, dict):
             print("\n--- AMOSTRA DOS DADOS RECEBIDOS ---")
             print("Chaves do dicionário principal:")
             print(list(dados.keys()))
             
        return dados
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao bater na API de terceiros: {e}")
        return None

if __name__ == "__main__":
    extrair_matchup_terceiros()