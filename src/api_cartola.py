import requests
import json
import os

# mapeia os diretórios para salvar o arquivo no lugar correto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def extrair_mercado():
    print("Conectando na API do Cartola e baixando o mercado...")
    url = "https://api.cartola.globo.com/atletas/mercado"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        dados = response.json()
        
        # salva o cache local na pasta data
        caminho_arquivo = os.path.join(DATA_DIR, 'mercado.json')
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
            
        print(f"Banco de dados salvo com sucesso em: {caminho_arquivo}")
        
        # imprime o dicionário de scouts direto da fonte
        print("\n--- PROVA REAL DOS SCOUTS ---")
        encontrou_scout = False
        for atleta in dados['atletas']:
            if atleta.get('scout'):
                print(f"Jogador Teste: {atleta['apelido']}")
                print(f"Scouts brutos recebidos da API: {atleta['scout']}")
                encontrou_scout = True
                break
                
        if not encontrou_scout:
            print("Nenhum jogador pontuou ainda no campeonato.")
            
        return dados
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao bater na API: {e}")
        return None

if __name__ == "__main__":
    extrair_mercado()