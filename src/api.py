import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import processar_jogadores
from otimizador import otimizar_escalacao

app = FastAPI(
    title="Apex FC",
    description="Otimização linear e DFS para dominar ligas clássicas e de tiro curto no Cartola FC",
    version="1.0.0",
    contact={
        "name": "Guilherme Lopes de Souza"
    }
)

class OtimizacaoRequest(BaseModel):
    orcamento: float = 110.0
    esquema: str = "4-3-3"
    modo: str = "classico"
    times_ignorados: List[str] = []
    evitar_confrontos: bool = True

@app.post("/api/v1/otimizar")
def gerar_escalacao(req: OtimizacaoRequest):
    try:
        print("Engrenando o motor de dados via API...")
        df_jogadores = processar_jogadores()
        
        if df_jogadores is None or df_jogadores.empty:
            raise HTTPException(status_code=500, detail="Erro ao carregar a base de dados.")

        time_ideal = otimizar_escalacao(
            df=df_jogadores,
            orcamento=req.orcamento,
            esquema=req.esquema,
            modo=req.modo,
            times_ignorados=req.times_ignorados,
            evitar_confrontos=req.evitar_confrontos
        )

        if time_ideal is None:
            raise HTTPException(status_code=400, detail="Orçamento muito baixo ou filtro impossível.")

        #exporta só as colunas que interessam pro Front-end
        colunas_exportar = ['Nome', 'Clube', 'Adv', 'Pos', 'C$', 'Score']
        escalacao_json = time_ideal[colunas_exportar].to_dict(orient='records')

        custo_real = float(time_ideal['C$'].sum())
        score_projetado = float(time_ideal['Score'].sum())

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
        raise HTTPException(status_code=500, detail=f"Erro interno no motor: {str(e)}")