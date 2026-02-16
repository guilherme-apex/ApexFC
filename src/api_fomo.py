import requests
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def atualizar_mais_escalados():
    print("Buscando os Mais Escalados em tempo real...")
    
    url = "https://provaveisdocartola.com.br/api/mais-escalados"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        dados = response.json()
        
        caminho_arquivo = os.path.join(DATA_DIR, 'mais_escalados.json')
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
            
        total_jogadores = len(dados.get('data', []))
        print(f"Sucesso! {total_jogadores} jogadores mais populares capturados e atualizados.")
        return True
        
    except Exception as e:
        print(f"Erro ao atualizar o FOMO: {e}")
        return False

if __name__ == "__main__":
    atualizar_mais_escalados()