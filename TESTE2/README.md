# Teste 2 – Transformação e Validação de Dados

Este projeto implementa o Teste 2 do processo seletivo para Estágio na IntuitiveCare.

O objetivo é validar, enriquecer e agregar os dados consolidados do Teste 1, aplicando estratégias de tratamento de inconsistências e realizando análises estatísticas.

---

## 🛠️ Tecnologias Utilizadas

- Python 3.14.2
- pandas – processamento e análise de dados
- requests – download de arquivos da ANS
- numpy – cálculos estatísticos

---

## Estrutura do Projeto

```
# Configuração Centralizada (raiz do projeto)
config/
├── consts/
│   ├── accounts.py
│   ├── directories.py
│   ├── file_formats.py
│   ├── filenames.py
│   └── ...
├── __init__.py
├── settings.py
└── .env

TESTE2/
├── data/
│   ├── cadastro/
│   │   └── Relatorio_cadop.csv
│   └── input/
│       └── consolidado_despesas.csv (do TESTE 1)
│
├── output/
│   ├── despesas_agregadas.csv
│   └── Teste_FranciscoFernando.zip
│
├── src/
│   ├── aggregators/
│   │   └── data_aggregator.py
│   ├── enrichers/
│   │   └── data_enricher.py
│   ├── utils/
│   │   ├── aggregation.py
│   │   ├── enrichment.py
│   │   └── validation.py
│   ├── validators/
│   │   └── data_validator.py
│   └── main.py
│
├── README.md
└── requirements.txt
```

---

## Como Executar

1. **Execute o TESTE 1 primeiro** (ou garanta que `TESTE1/output/consolidado_despesas.csv` existe)
   - O TESTE 2 busca automaticamente o arquivo gerado pelo TESTE 1

2. Instale as dependências:

```bash
   pip install -r requirements.txt
```

3. Execute o pipeline:

```bash
   python src/main.py
```

4. O arquivo final será gerado em:
   - output/despesas_agregadas.csv
   - output/Teste_FranciscoFernando.zip

**Nota:** Se o arquivo do TESTE 1 não for encontrado, você pode copiá-lo manualmente para `TESTE2/data/input/consolidado_despesas.csv`

---

## 🧠 Decisões Técnicas e Trade-offs

### 2.1 Validação de Dados - Estratégia de CNPJs/REG_ANS Inválidos

**Decisão Implementada:** **MARCAR** como inválido e MANTER no dataset

**Justificativa:**

- Os dados da ANS utilizam **REG_ANS** (Registro da Operadora - 6 dígitos), não CNPJs tradicionais de 14 dígitos
- O validador aceita ambos os formatos: REG_ANS (6 dígitos) e CNPJ (14 dígitos com validação de dígitos verificadores)
- Registros inválidos são marcados com `VALIDO=False` e `MOTIVO_INVALIDACAO` preenchido
- **Prós:** Transparência total, rastreabilidade, permite análise posterior dos problemas
- **Contras:** Necessário filtrar por `df['VALIDO'] == True` em análises subsequentes

**Resultado:** 410.025 registros válidos (99,08%) de 413.837 totais

---

### 2.2 Enriquecimento - Estratégia de Join

**Decisão Implementada:** Processamento **EM MEMÓRIA** com pandas merge (LEFT JOIN)

**Justificativa:**

- Dataset da ANS (~410k registros) cabe confortavelmente em memória (< 100MB)
- Pandas merge é otimizado e extremamente rápido para este volume
- LEFT JOIN mantém todos os registros do consolidado, mesmo sem match no cadastro
- Simplicidade do código vs. complexidade de streaming

**Trade-off considerado:**

- ✅ **Em memória** (escolhido): Simples, rápido, suficiente para o volume atual
- ❌ **Streaming**: Desnecessariamente complexo para este caso, só seria necessário para datasets > 10M registros

**Resultado:** Join realizado por `REGISTRO_OPERADORA` (não CNPJ), com enriquecimento de Razão Social, Modalidade, UF e RegistroANS

---

### 2.2 Tratamento de Registros sem Match

**Decisão Implementada:** Manter registros com valores nulos e remover apenas na agregação

**Estratégia:**

1. **Enriquecimento:** Mantém todos os registros (LEFT JOIN)
2. **Razão Social vazia:** Preenchida com dados do cadastro quando possível
3. **Agregação:** Remove apenas registros sem RazaoSocial OU UF (necessários para agrupamento)

**Resultado:** 3.993 registros removidos na agregação por falta de UF ou RazaoSocial (< 1%)

---

### 2.3 Agregação - Estratégia de Ordenação

**Decisão Implementada:** **Ordenação in-memory** com pandas sort_values

**Justificativa:**

- Após agregação: apenas 756 grupos (RazaoSocial + UF)
- Pandas implementa quicksort/mergesort otimizados
- Ordenação externa (em disco) só seria necessária para datasets > 100M registros
- Performance: < 0.01 segundos para ordenar 756 grupos

**Trade-off considerado:**

- ✅ **In-memory** (escolhido): Simples, rápido, adequado para o volume
- ❌ **Externa**: Complexo, lento, desnecessário

**Resultado:** Ordenação por TotalDespesas (decrescente) com taxa de compressão de 542.4x

---

## 📊 Validações Implementadas

### 2.1 Validação de CNPJ/REG_ANS

**Aceita dois formatos:**

- **REG_ANS:** 6 dígitos (identificador da ANS) - aceito automaticamente
- **CNPJ:** 14 dígitos com validação completa de dígitos verificadores

**Estratégia:** MARCAR como inválido, mas MANTER no dataset para transparência

**Resultado:** 3.812 identificadores inválidos (0,92%)

---

### 2.1 Validação de Valores

- ✅ Valores numéricos positivos (≥ 0)
- ✅ Valores zerados mantidos (podem representar ausência de despesa no período)
- ✅ Valores negativos já foram removidos no TESTE 1

**Resultado:** 100% dos valores são válidos

---

### 2.1 Validação de Razão Social

- **Estratégia:** NÃO invalida registros com Razão Social vazia
- **Motivo:** A Razão Social é preenchida durante o enriquecimento (2.2) com dados do cadastro da ANS
- **Normalização:** Conversão para string, preenchimento de valores nulos com 'NÃO INFORMADO'

**Resultado:** 410.025 registros tiveram Razão Social preenchida no enriquecimento

---

## 🔗 Enriquecimento com Dados Cadastrais

**Fonte:** Arquivo `Relatorio_cadop.csv` da ANS (baixado automaticamente)

**Método:** LEFT JOIN usando `REGISTRO_OPERADORA` como chave (não CNPJ)

**Dados adicionados:**

- **RegistroANS:** Número de registro da operadora na ANS
- **Razão Social:** Nome oficial da operadora (preenchido do cadastro)
- **Modalidade:** Tipo de operadora (Medicina de Grupo, Cooperativa Médica, etc.)
- **UF:** Estado de registro da operadora

**Observação importante:** O campo "CNPJ" no arquivo consolidado do TESTE 1 contém na verdade o `REGISTRO_OPERADORA` da ANS (6 dígitos), não o CNPJ tradicional. Por isso, o join é feito por este identificador.

**Resultado:** 406.032 registros enriquecidos com sucesso

---

## 📊 Análises Estatísticas e Resultados

### Agregação por RazaoSocial e UF:

**Métricas calculadas:**

- **TotalDespesas:** Soma de todas as despesas da operadora naquele estado
- **MediaDespesasTrimestre:** Média de despesas por trimestre
- **DesvioPadraoDespesas:** Desvio padrão das despesas (mede variabilidade)
- **CoeficienteVariacao (CV):** Desvio padrão / Média (identifica operadoras com despesas muito variáveis)

**Resultados obtidos:**

- **756 grupos** (Operadora + UF)
- **Taxa de compressão:** 542.4x (de 410k registros para 756 grupos)
- **Total de despesas:** R$ 3,126 trilhões
- **Média por grupo:** R$ 4,135 bilhões
- **Mediana por grupo:** R$ 796 milhões

### Top 3 Operadoras com Maiores Despesas:

1. **AMIL ASSISTÊNCIA MÉDICA INTERNACIONAL S.A. (SP)** - R$ 329,2 bilhões
2. **NOTRE DAME INTERMÉDICA SAÚDE S.A. (SP)** - R$ 151,6 bilhões
3. **HAPVIDA ASSISTENCIA MEDICA S.A. (CE)** - R$ 150,7 bilhões

### Análise de Variabilidade:

- **731 operadoras** com alta variabilidade (CV > 0.5)
- Indica despesas muito variáveis entre trimestres
- Possíveis causas: sazonalidade, eventos atípicos, ou inconsistências nos dados originais

---

## 📁 Arquivos Gerados

1. **`output/despesas_agregadas.csv`**
   - Formato: RazaoSocial, UF, TotalDespesas, MediaDespesasTrimestre, DesvioPadraoDespesas
   - 756 linhas (operadoras agregadas)
   - Ordenado por TotalDespesas (decrescente)

2. **`output/Teste_FranciscoFernando.zip`**
   - Contém o arquivo despesas_agregadas.csv compactado

---
