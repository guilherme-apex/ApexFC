import os
import json
import pandas as pd
import pulp
from main import processar_jogadores

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

FORMACAOS = {
    '3-4-3': {'gol': 1, 'lat': 0, 'zag': 3, 'mei': 4, 'ata': 3, 'tec': 1},
    '3-5-2': {'gol': 1, 'lat': 0, 'zag': 3, 'mei': 5, 'ata': 2, 'tec': 1},
    '4-3-3': {'gol': 1, 'lat': 2, 'zag': 2, 'mei': 3, 'ata': 3, 'tec': 1},
    '4-4-2': {'gol': 1, 'lat': 2, 'zag': 2, 'mei': 4, 'ata': 2, 'tec': 1},
    '4-5-1': {'gol': 1, 'lat': 2, 'zag': 2, 'mei': 5, 'ata': 1, 'tec': 1},
    '5-3-2': {'gol': 1, 'lat': 2, 'zag': 3, 'mei': 3, 'ata': 2, 'tec': 1},
    '5-4-1': {'gol': 1, 'lat': 2, 'zag': 3, 'mei': 4, 'ata': 1, 'tec': 1}
}

def carregar_mais_escalados():
    caminho = os.path.join(DATA_DIR, 'mais_escalados.json')
    if not os.path.exists(caminho): return {}, 1
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            total_times = dados.get('times_escalados', 200000)
            fomo_dict = {item['Atleta']['apelido']: item['escalacoes'] for item in dados.get('data', [])}
            return fomo_dict, total_times
    except Exception: return {}, 1

def otimizar_escalacao(df, orcamento=100.0, esquema='4-3-3', modo='tiro_curto', times_ignorados=None, jogadores_travados=None, evitar_confrontos=True):
    if times_ignorados is None: times_ignorados = []
    if jogadores_travados is None: jogadores_travados = []
    
    df_filtrado = df[~df['Clube'].isin(times_ignorados)].copy()
    
    if esquema not in FORMACAOS: esquema = '4-3-3'
    restricoes_taticas = FORMACAOS[esquema].copy()

    tecnicos = df_filtrado[df_filtrado['Pos'] == 'tec'].sort_values('C$')
    if tecnicos.empty: return None
    tec_escolhido = tecnicos.iloc[0]
    orcamento_linha = orcamento - tec_escolhido['C$']
    
    df_linha = df_filtrado[df_filtrado['Pos'] != 'tec'].copy()
    jogadores = df_linha.index.tolist()

    dados_fomo, total_times = {}, 1
    if modo == 'classico': 
        dados_fomo, total_times = carregar_mais_escalados()

    setor_luxo = 'ata' if restricoes_taticas.get('ata', 0) > 0 else 'mei'
    restricoes_taticas[setor_luxo] += 1

    prob = pulp.LpProblem("Cartola_Otimizacao", pulp.LpMaximize)
    escolha = pulp.LpVariable.dicts("escolha", jogadores, cat='Binary')

    termos_objetivo = []
    fomo_threshold = total_times * 0.40

    for i in jogadores:
        proj_base = df_linha.loc[i, 'Pontuacao_Projetada']
        nome_jogador = df_linha.loc[i, 'Nome']
        
        peso = proj_base
        if modo == 'valorizacao': peso = proj_base - df_linha.loc[i, 'MPV']
        elif modo == 'classico' and nome_jogador in dados_fomo:
            escalacoes = dados_fomo[nome_jogador]
            if escalacoes >= fomo_threshold:
                peso += 1000.0 
            else:
                peso += (escalacoes / 100000) * 5.0 
                
        termos_objetivo.append(peso * escolha[i])

    prob += pulp.lpSum(termos_objetivo), "Objetivo_Principal"
    
    prob += pulp.lpSum(df_linha.loc[i, 'C$'] * escolha[i] for i in jogadores) <= orcamento_linha, "Custo_Total"

    custo_frente = pulp.lpSum(df_linha.loc[i, 'C$'] * escolha[i] for i in jogadores if df_linha.loc[i, 'Pos'] in ['ata', 'mei'])
    prob += custo_frente >= (orcamento_linha * 0.55), "Orcamento_Frente_Minimo"

    prob += pulp.lpSum(escolha[i] for i in jogadores if df_linha.loc[i, 'Pos'] == 'gol') == restricoes_taticas['gol']
    prob += pulp.lpSum(escolha[i] for i in jogadores if df_linha.loc[i, 'Pos'] == 'lat') == restricoes_taticas['lat']
    prob += pulp.lpSum(escolha[i] for i in jogadores if df_linha.loc[i, 'Pos'] == 'zag') == restricoes_taticas['zag']
    prob += pulp.lpSum(escolha[i] for i in jogadores if df_linha.loc[i, 'Pos'] == 'mei') == restricoes_taticas['mei']
    prob += pulp.lpSum(escolha[i] for i in jogadores if df_linha.loc[i, 'Pos'] == 'ata') == restricoes_taticas['ata']

    # --- A MÁGICA DO CADEADO ---
    for nome_travado in jogadores_travados:
        idx_lista = df_linha[df_linha['Nome'] == nome_travado].index.tolist()
        if idx_lista:
            # Força o motor a escalar o jogador (variável == 1)
            prob += escolha[idx_lista[0]] == 1, f"Trava_{idx_lista[0]}"

    if evitar_confrontos:
        confrontos_processados = set()
        for i in jogadores:
            time_a, time_b = df_linha.loc[i, 'Clube'], df_linha.loc[i, 'Adv']
            confronto_str = tuple(sorted([time_a, time_b]))
            if confronto_str not in confrontos_processados:
                confrontos_processados.add(confronto_str)
                off_a = [j for j in jogadores if df_linha.loc[j, 'Clube'] == time_a and df_linha.loc[j, 'Pos'] in ['mei', 'ata']]
                def_b = [j for j in jogadores if df_linha.loc[j, 'Clube'] == time_b and df_linha.loc[j, 'Pos'] in ['gol', 'zag', 'lat']]
                if off_a and def_b:
                    b1 = pulp.LpVariable(f"conflito_1_{time_a}_{time_b}", cat='Binary')
                    prob += pulp.lpSum(escolha[j] for j in off_a) <= 6 * b1 
                    prob += pulp.lpSum(escolha[j] for j in def_b) <= 5 * (1 - b1) 
                    
                off_b = [j for j in jogadores if df_linha.loc[j, 'Clube'] == time_b and df_linha.loc[j, 'Pos'] in ['mei', 'ata']]
                def_a = [j for j in jogadores if df_linha.loc[j, 'Clube'] == time_a and df_linha.loc[j, 'Pos'] in ['gol', 'zag', 'lat']]
                if off_b and def_a:
                    b2 = pulp.LpVariable(f"conflito_2_{time_a}_{time_b}", cat='Binary')
                    prob += pulp.lpSum(escolha[j] for j in off_b) <= 6 * b2
                    prob += pulp.lpSum(escolha[j] for j in def_a) <= 5 * (1 - b2)

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    escolhidos_idx = [i for i in jogadores if escolha[i].varValue == 1]
    
    if not escolhidos_idx:
        print("O algoritmo não encontrou escalação possível (tente afrouxar o orçamento ou tirar alguns cadeados).")
        return None

    time_bruto = df_linha.loc[escolhidos_idx].copy()

    jogadores_setor_luxo = time_bruto[time_bruto['Pos'] == setor_luxo].sort_values('C$')
    
    reserva_luxo = jogadores_setor_luxo.iloc[0].copy()
    reserva_luxo['Tipo'] = setor_luxo.upper()
    
    time_ideal = time_bruto.drop(reserva_luxo.name)
    time_ideal = pd.concat([time_ideal, pd.DataFrame([tec_escolhido])])

    atas = time_ideal[time_ideal['Pos'] == 'ata']
    meis = time_ideal[time_ideal['Pos'] == 'mei']
    max_ata_score = atas['Pontuacao_Projetada'].max() if not atas.empty else 0
    max_mei_score = meis['Pontuacao_Projetada'].max() if not meis.empty else 0
    
    if max_mei_score > (max_ata_score * 1.20): capitao_idx = meis['Pontuacao_Projetada'].idxmax()
    elif not atas.empty: capitao_idx = atas['Pontuacao_Projetada'].idxmax()
    else: capitao_idx = time_ideal[time_ideal['Pos'] != 'tec']['Pontuacao_Projetada'].idxmax()

    # Ajuste na coroa do Capitão
    time_ideal.loc[capitao_idx, 'Nome'] = f"👑 {time_ideal.loc[capitao_idx, 'Nome']} (C)"
    time_ideal.loc[capitao_idx, 'Pontuacao_Projetada'] = round(time_ideal.loc[capitao_idx, 'Pontuacao_Projetada'] * 1.5, 2)

    banco_reservas = [reserva_luxo]
    restricoes_taticas[setor_luxo] -= 1 
    
    for pos, qtd in restricoes_taticas.items():
        if qtd > 0 and pos != 'tec' and pos != setor_luxo:
            titulares_pos = time_ideal[time_ideal['Pos'] == pos]
            if not titulares_pos.empty:
                preco_corte = titulares_pos['C$'].min()
                candidatos = df_linha[(~df_linha.index.isin(time_bruto.index)) & 
                                     (df_linha['Pos'] == pos) & 
                                     (df_linha['C$'] <= preco_corte)]
                if not candidatos.empty:
                    melhor_reserva = candidatos.loc[candidatos['Pontuacao_Projetada'].idxmax()].copy()
                    melhor_reserva['Tipo'] = pos.upper()
                    banco_reservas.append(melhor_reserva)

    ordem_posicoes = {'gol': 1, 'lat': 2, 'zag': 3, 'mei': 4, 'ata': 5, 'tec': 6}
    time_ideal['Ordem'] = time_ideal['Pos'].map(ordem_posicoes)
    time_ideal = time_ideal.sort_values('Ordem').drop('Ordem', axis=1).reset_index(drop=True)
    time_ideal.index = range(1, len(time_ideal) + 1)

    custo_total = time_ideal['C$'].sum()
    score_projetado = time_ideal['Pontuacao_Projetada'].sum()

    print(f"\n==================================================")
    print(f"ESCALAÇÃO: {esquema} | MODO: {modo.upper()} | ANTI-ZIKA: {'LIGADO' if evitar_confrontos else 'DESLIGADO'}")
    print(f"==================================================")
    print(f"Orçamento Utilizado: C$ {custo_total:.2f} / C$ {orcamento:.2f}")
    print(f"Pontuação Projetada:     {score_projetado:.2f} pts\n")
    
    print(time_ideal[['Nome', 'Clube', 'Adv', 'Pos', 'C$', 'Pontuacao_Projetada', 'Score']].to_string())
    
    print(f"\n==================================================")
    print(f"BANCO DE RESERVAS")
    print(f"==================================================")
    if banco_reservas:
        df_banco = pd.DataFrame(banco_reservas)
        df_banco['Nome'] = df_banco['Nome'].apply(lambda x: f"{x} [LUXO]" if x == reserva_luxo['Nome'] else x)
        print(df_banco[['Nome', 'Clube', 'Adv', 'Pos', 'C$', 'Pontuacao_Projetada', 'Score']].to_string(index=False))

    return time_ideal

if __name__ == "__main__":
    df_jogadores = processar_jogadores()
    if df_jogadores is not None:
        otimizar_escalacao(
            df=df_jogadores, 
            orcamento=120.0,
            esquema='4-3-3', 
            modo='classico', 
            times_ignorados=[],
            jogadores_travados=["Piquerez"], # Teste de trava
            evitar_confrontos=True 
        )