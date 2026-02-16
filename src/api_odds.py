import requests
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

API_KEY = '91f79b6602809d4f8538ee0ed7f4c555' 
SPORT = 'soccer_brazil_campeonato'
REGIONS = 'eu,uk'
MARKETS = 'h2h'

def extrair_odds():
    print("Acessando o mercado de apostas e capturando Odds...")
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/?apiKey={API_KEY}&regions={REGIONS}&markets={MARKETS}&oddsFormat=decimal'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        dados = response.json()
        
        odds_processadas = {}
        casas_pro = ['pinnacle', 'betfair', 'betano']
        
        for jogo in dados:
            selected_bookmaker = None
            
            for b in jogo.get('bookmakers', []):
                if b['key'] in casas_pro:
                    selected_bookmaker = b
                    break
            
            if not selected_bookmaker and jogo.get('bookmakers'):
                selected_bookmaker = jogo['bookmakers'][0]
            
            if selected_bookmaker:
                market = selected_bookmaker['markets'][0]
                outcomes = market['outcomes']
                
                for outcome in outcomes:
                    time = outcome['name']
                    if time.lower() == 'draw':
                        continue
                        
                    odd = outcome['price']
                    probabilidade = (1 / odd) * 100
                    odds_processadas[time] = round(probabilidade, 2)
        
        caminho_arquivo = os.path.join(DATA_DIR, 'odds.json')
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(odds_processadas, f, ensure_ascii=False, indent=4)
            
        print(f"Odds automatizadas salvas em: {caminho_arquivo}")
        print(f"Total de times mapeados: {len(odds_processadas)}")
        
        return odds_processadas

    except Exception as e:
        print(f"Erro ao capturar Odds: {e}")
        return None

if __name__ == "__main__":
    extrair_odds()