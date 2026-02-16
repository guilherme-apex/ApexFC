import requests
import json
import os

# mapeia os diretórios para salvar o cache
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def extrair_partidas():
    print("Conectando na API do Cartola e puxando o calendário...")
    url = "https://api.cartola.globo.com/partidas"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        dados = response.json()
        
        # salva o json localmente
        caminho_arquivo = os.path.join(DATA_DIR, 'partidas.json')
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
            
        print(f"Calendário salvo com sucesso em: {caminho_arquivo}")
        
        # filtrar apenas os jogos válidos
        clubes = dados.get('clubes', {})
        partidas = dados.get('partidas', [])
        
        print("\n--- JOGOS VÁLIDOS PARA A RODADA ---")
        jogos_validos = 0
        
        for p in partidas:
            if p.get('valida', False): 
                mandante = clubes[str(p['clube_casa_id'])]['abreviacao']
                visitante = clubes[str(p['clube_visitante_id'])]['abreviacao']
                print(f"[{mandante}] x [{visitante}]")
                jogos_validos += 1
                
        print(f"\nTotal de confrontos válidos: {jogos_validos}")
        
        if jogos_validos < 10:
            print("ATENÇÃO: Temos jogos adiados/inválidos nesta rodada.")
            
        return dados
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao bater na API de partidas: {e}")
        return None

if __name__ == "__main__":
    extrair_partidas()