import os
import json
import pandas as pd
from config import SCOUTS_ATAQUE, SCOUTS_DEFESA

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def carregar_json_local(nome_arquivo):
    caminho_arquivo = os.path.join(DATA_DIR, nome_arquivo)
    if not os.path.exists(caminho_arquivo):
        print(f"Arquivo {nome_arquivo} não encontrado.")
        return None
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        return json.load(f)

def calcular_media_basica(atleta, scouts_realizados):
    jogos = atleta.get('jogos_num', 0)
    if jogos == 0: return 0.0
    media_geral = atleta.get('media_num', 0.0)
    pontos_totais = media_geral * jogos
    gols = scouts_realizados.get('G', 0)
    assistencias = scouts_realizados.get('A', 0)
    sg = scouts_realizados.get('SG', 0)
    pontos_variancia = (gols * SCOUTS_ATAQUE['G']) + (assistencias * SCOUTS_ATAQUE['A']) + (sg * SCOUTS_DEFESA['SG'])
    media_basica = (pontos_totais - pontos_variancia) / jogos
    return round(media_basica, 2)

def calcular_mpv(preco_atual):
    return round(preco_atual * 0.52, 2)

def obter_status_confrontos(dados_partidas, dicionario_clubes):
    status_clubes = {}
    for p in dados_partidas.get('partidas', []):
        if p.get('valida', False):
            id_casa = p['clube_casa_id']
            id_fora = p['clube_visitante_id']
            sigla_casa = dicionario_clubes.get(str(id_casa), 'N/A')
            sigla_fora = dicionario_clubes.get(str(id_fora), 'N/A')
            
            status_clubes[id_casa] = {'Mando': 'Casa', 'Adv': sigla_fora}
            status_clubes[id_fora] = {'Mando': 'Fora', 'Adv': sigla_casa}
    return status_clubes

def processar_jogadores():
    dados_mercado = carregar_json_local('mercado.json')
    dados_partidas = carregar_json_local('partidas.json')
    dados_odds = carregar_json_local('odds.json')
    
    if not dados_mercado or not dados_partidas: return
        
    clubes = {str(k): v['abreviacao'] for k, v in dados_mercado['clubes'].items()}
    status_confrontos = obter_status_confrontos(dados_partidas, clubes)
    clubes_validos = set(status_confrontos.keys())
    
    DE_PARA_TIMES = {
        "Atletico Paranaense": "CAP", "Corinthians": "COR", "Bahia": "BAH",
        "Chapecoense": "CHA", "Botafogo": "BOT", "Vitoria": "VIT",
        "Flamengo": "FLA", "Mirassol": "MIR", "Bragantino-SP": "RBB",
        "Internacional": "INT", "Remo": "REM", "Cruzeiro": "CRU",
        "Atletico Mineiro": "CAM", "Grêmio": "GRE", "Fluminense": "FLU",
        "Palmeiras": "PAL", "Santos": "SAN", "Vasco da Gama": "VAS",
        "Coritiba": "CFC", "Sao Paulo": "SAO"
    }
    
    odds_por_sigla = {}
    if dados_odds:
        for nome_gringo, odd in dados_odds.items():
            sigla = DE_PARA_TIMES.get(nome_gringo)
            if sigla: odds_por_sigla[sigla] = odd

    posicoes = {str(k): v['abreviacao'] for k, v in dados_mercado['posicoes'].items()}
    status_dict = {str(k): v['nome'] for k, v in dados_mercado['status'].items()}
    
    jogadores_processados = []
    
    for atleta in dados_mercado['atletas']:
        clube_id = atleta['clube_id']
        if clube_id not in clubes_validos: continue
            
        status_atual = status_dict.get(str(atleta['status_id']), 'N/A')
        jogos = atleta.get('jogos_num', 0)
        posicao_atual = posicoes.get(str(atleta['posicao_id']), 'N/A')
        
        if status_atual == 'Provável' and (jogos > 0 or posicao_atual == 'tec'):
            scouts = atleta.get('scout', {})
            mb = calcular_media_basica(atleta, scouts) if posicao_atual != 'tec' else 0.0
            preco = atleta['preco_num']
            sigla_clube = clubes.get(str(clube_id), 'N/A')
            
            info_confronto = status_confrontos[clube_id]
            mando = info_confronto['Mando']
            adversario = info_confronto['Adv']
            
            mpv = calcular_mpv(preco)
            prob_vitoria = odds_por_sigla.get(sigla_clube, 30.0)
            
            if posicao_atual in ['gol', 'zag', 'lat']: peso_posicao = 5.0
            elif posicao_atual == 'ata': peso_posicao = 4.0
            else: peso_posicao = 3.5
            
            if posicao_atual == 'tec':
                score_final = (prob_vitoria / 100) * 8.0 
            else:
                score_final = mb + ((prob_vitoria / 100) * peso_posicao)
            
            jogadores_processados.append({
                'Nome': atleta['apelido'],
                'Clube': sigla_clube,
                'Adv': adversario,
                'Pos': posicao_atual,
                'Mando': mando,
                'C$': preco,
                'MB': mb,
                'MPV': mpv,
                'Vit(%)': prob_vitoria,
                'Score': round(score_final, 2)
            })
            
    df = pd.DataFrame(jogadores_processados)
    df = df.sort_values(by='Score', ascending=False).reset_index(drop=True)
    df.index += 1
    
    return df

if __name__ == "__main__":
    processar_jogadores()