# Teste 4 – API REST + Interface Web Vue.js

Este projeto implementa o Teste 4 do processo seletivo para Estágio na IntuitiveCare.

**Aplicação web completa:** Backend Python (FastAPI) + Frontend Vue.js para consulta de operadoras de saúde e suas despesas.

---

## 🎯 O que Foi Implementado

✅ **Backend FastAPI** com 4 endpoints REST  
✅ **Frontend Vue 3** com tabela, busca, gráfico e detalhes

---

## ⚙️ Pré-requisitos

✅ **PostgreSQL** rodando (banco `teste3_intuitivecare` do TESTE 3)  
✅ **Python 3.8+** instalado  
✅ **Node.js 16+** instalado

---

## 🚀 Como Executar

### 1️⃣ Configurar Banco de Dados

Crie o arquivo `.env` dentro da pasta `src/`:

```bash
# TESTE4/src/.env
DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost/teste3_intuitivecare
```

⚠️ **Importante:** Substitua `SUA_SENHA` pela senha do seu PostgreSQL!

### 2️⃣ Backend (FastAPI)

```bash
cd TESTE4
pip install -r requirements.txt
cd src
python main.py
```

✅ **API rodando em:** http://localhost:8000  
📖 **Docs interativos:** http://localhost:8000/docs

### 3️⃣ Frontend (Vue.js)

```bash
cd TESTE4/frontend
npm install
npm run dev
```

✅ **App rodando em:** http://localhost:5173

---

## 📡 API Endpoints

- `GET /api/operadoras` - Lista paginada
- `GET /api/operadoras/{cnpj}` - Detalhes
- `GET /api/operadoras/{cnpj}/despesas` - Histórico
- `GET /api/estatisticas` - Agregadas (cached 5min)

---

## 🏗️ Trade-offs Documentados

### Backend (4.2)

**4.2.1 Framework:** FastAPI ✅  
_Async nativo, validação automática, docs OpenAPI_

**4.2.2 Paginação:** Offset-based ✅  
_Simples, adequado para 1.1k registros_

**4.2.3 Cache:** 5 minutos in-memory ✅  
_Query pesada, dados trimestrais_

**4.2.4 Resposta:** Dados + metadados ✅  
_Frontend precisa de total_pages para UX_

### Frontend (4.3)

**4.3.1 Busca:** No servidor ✅  
_1.1k registros, aproveita índices PostgreSQL_

**4.3.2 Estado:** Pinia ✅  
_Compartilhamento entre views, cache de dados_

**4.3.3 Performance:** Paginação server-side ✅  
_10-20 registros por vez, renderização instantânea_

**4.3.4 Erros:** Mensagens específicas ✅  
_404/500/503/timeout com textos orientados_

---
