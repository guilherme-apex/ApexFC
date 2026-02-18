import requests
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware

from main import processar_jogadores
from otimizador import otimizar_escalacao

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/proxy-imagem")
def proxy_imagem(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL da imagem não fornecida.")
    try:
        headers_fake = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers_fake, stream=True)
        resp.raise_for_status()
        return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get('content-type'))
    except Exception as e:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")

class OtimizacaoRequest(BaseModel):
    orcamento: float = 110.0
    esquema: str = "4-3-3"
    modo: str = "classico" # Agora aceita 'valorizacao'
    times_ignorados: List[str] = []
    jogadores_travados: List[str] = []
    jogadores_ignorados: List[str] = [] # --- A NOVA BLACKLIST ---
    evitar_confrontos: bool = True

@app.post("/api/v1/otimizar")
def gerar_escalacao(req: OtimizacaoRequest):
    try:
        df_jogadores = processar_jogadores()
        
        if df_jogadores is None or df_jogadores.empty:
            raise HTTPException(status_code=500, detail="Erro ao carregar a base de dados.")

        df_provaveis = df_jogadores[df_jogadores['Status'] == 'Provável'].copy()

        time_ideal = otimizar_escalacao(
            df=df_provaveis,
            orcamento=req.orcamento,
            esquema=req.esquema,
            modo=req.req.modo if hasattr(req, 'modo') else req.modo,
            times_ignorados=req.times_ignorados,
            jogadores_travados=req.jogadores_travados,
            jogadores_ignorados=req.jogadores_ignorados, # Repassando para o motor
            evitar_confrontos=req.evitar_confrontos
        )

        if time_ideal is None:
            raise HTTPException(status_code=400, detail="Orçamento baixo ou filtro impossível.")

        colunas_exportar = ['Nome', 'Clube', 'Escudo', 'Adv', 'Mando', 'Pos', 'Status', 'C$', 'Pontuacao_Projetada', 'Score', 'MPV', 'MB']
        escalacao_json = time_ideal[colunas_exportar].to_dict(orient='records')

        custo_real = float(time_ideal['C$'].sum())
        score_projetado = float(time_ideal['Pontuacao_Projetada'].sum())

        return {
            "status": "sucesso",
            "parametros": req.model_dump(),
            "resumo": {
                "custo_total": round(custo_real, 2),
                "score_projetado": round(score_projetado, 2)
            },
            "titulares": escalacao_json
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/v1/jogadores")
def listar_jogadores():
    try:
        df_jogadores = processar_jogadores()
        if df_jogadores is None or df_jogadores.empty:
            raise HTTPException(status_code=500, detail="Erro ao carregar a base de dados.")
            
        colunas = ['Nome', 'Clube', 'Escudo', 'Adv', 'Mando', 'Pos', 'Status', 'C$', 'Pontuacao_Projetada', 'Score', 'MPV', 'MB']
        df_limpo = df_jogadores[colunas].fillna(0).copy()
        
        return {
            "status": "sucesso",
            "jogadores": df_limpo.to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar jogadores: {str(e)}")