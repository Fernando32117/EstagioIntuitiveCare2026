from api.routes import operadoras, despesas, estatisticas
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


app = FastAPI(
    title="IntuitiveCare - API de Despesas de Operadoras",
    description="""
    API REST para consulta de dados de operadoras de saúde e suas despesas.
    
    Baseada nos dados consolidados dos TESTE 1, 2 e 3.
    
    ## Funcionalidades
    
    ### 4.1 Operadoras
    - Listar todas as operadoras (com paginação e filtros)
    - Buscar operadora por Registro ANS
    - Listar operadoras por UF
    
    ### 4.2 Despesas Consolidadas
    - Listar despesas consolidadas (com filtros)
    - Listar despesas de uma operadora específica
    
    ### 4.3 Análises Agregadas
    - Listar despesas agregadas por operadora e UF
    - Top UFs com maiores despesas
    - Top operadoras com maior crescimento percentual
    - Operadoras com despesas acima da média
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(operadoras.router, prefix="/api")
app.include_router(despesas.router, prefix="/api")
app.include_router(estatisticas.router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "IntuitiveCare - API de Despesas de Operadoras de Saúde",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "operadoras": "/api/operadoras",
            "despesas_consolidadas": "/api/despesas/consolidadas",
            "despesas_agregadas": "/api/despesas/agregadas",
            "top_ufs": "/api/despesas/top-ufs",
            "crescimento": "/api/despesas/crescimento",
            "acima_media": "/api/despesas/acima-media"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "intuitivecare-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
