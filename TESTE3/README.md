# Teste 3 – Banco de Dados e Análise SQL

Este projeto implementa o Teste 3 do processo seletivo para Estágio na IntuitiveCare.

O objetivo é criar uma estrutura de banco de dados PostgreSQL, importar os dados consolidados dos testes anteriores e desenvolver queries analíticas para extrair insights sobre despesas de operadoras de saúde.

---

## 🛠️ Tecnologias Utilizadas

- **PostgreSQL 14+**
- **psql** – cliente de linha de comando
- Dados dos TESTE 1 e TESTE 2

---

## Estrutura do Projeto

```
TESTE3/
├── sql/
│   ├── 01_schema.sql          # DDL - Criação de tabelas, indexes, constraints
│   ├── 02_import.sql          # Importação dos CSVs (Item 3.3)
│   └── 03_queries.sql         # Queries analíticas (Item 3.4)
│
└── README.md
```

---

## Como Executar

### Pré-requisitos

1. PostgreSQL 14+ instalado e rodando
2. Usuário com permissões de criação de database
3. CSVs gerados pelos TESTE 1 e TESTE 2

### Passo 1: Criar o banco de dados

```bash
createdb -U postgres teste3_intuitivecare
```

Ou via psql:

```sql
CREATE DATABASE teste3_intuitivecare WITH ENCODING 'UTF8';
```

### Passo 2: Executar o schema DDL

```bash
psql -U postgres -d teste3_intuitivecare -f sql/01_schema.sql
```

### Passo 3: Importar os dados

```bash
psql -U postgres -d teste3_intuitivecare -f sql/02_import.sql
```

**Nota:** Os caminhos dos CSVs já estão configurados para:

- `../../TESTE1/output/consolidado_despesas.csv`
- `../../TESTE2/output/despesas_agregadas.csv`
- `../../TESTE2/data/cadastro/Relatorio_cadop.csv`

### Passo 4: Executar queries analíticas

```bash
psql -U postgres -d teste3_intuitivecare -f sql/03_queries.sql
```

---

## 🏗️ Decisões de Arquitetura

### 3.2.1 Trade-off: Normalização

**Escolha:** Abordagem **SEMI-NORMALIZADA** (híbrida)

**Estrutura:**

- `operadoras` – Tabela normalizada com dados cadastrais
- `despesas_consolidadas` – Referencia operadoras via FK
- `despesas_agregadas` – Tabela desnormalizada para análises

**Justificativa:**

| Critério                       | Análise                                                                         | Decisão                              |
| ------------------------------ | ------------------------------------------------------------------------------- | ------------------------------------ |
| **Volume de dados**            | ~410k registros consolidados, ~750 agregados, ~400 operadoras (volume moderado) | Normalização é viável                |
| **Frequência de atualizações** | APPEND-ONLY (novos trimestres), sem UPDATEs                                     | Normalização não impacta performance |
| **Complexidade de queries**    | JOINs frequentes entre despesas e cadastro                                      | FK garante consistência              |
| **Consistência**               | Dados cadastrais devem ser fonte única de verdade                               | Normalização é essencial             |

**Trade-off escolhido:**

- ✅ **Operadoras normalizadas**: Garante consistência e facilita manutenção
- ✅ **Despesas com FK**: Integridade referencial automática
- ✅ **Agregados desnormalizados**: Performance em análises complexas

---

### 3.2.2 Trade-off: Tipos de Dados

#### Valores Monetários

**Escolha:** `DECIMAL(15, 2)`

**Alternativas consideradas:**

| Tipo                   | Prós                                        | Contras                                              | Decisão       |
| ---------------------- | ------------------------------------------- | ---------------------------------------------------- | ------------- |
| **FLOAT/REAL**         | Rápido, menos espaço                        | ❌ Erros de arredondamento (INACEITÁVEL p/ finanças) | Rejeitado     |
| **INTEGER** (centavos) | Precisão total                              | ❌ Dificulta leitura e queries (R$ 1.50 = 150)       | Rejeitado     |
| **DECIMAL(15,2)**      | ✅ Precisão exata, queries naturais, padrão | Pouco mais lento que FLOAT                           | **ESCOLHIDO** |

**Justificativa:**

- Precisão exata até 2 casas decimais (requisito legal)
- Suporta até R$ 9.999.999.999.999,99 (trilhões)
- Operações aritméticas sem perda de precisão
- Padrão da indústria financeira (GAAP, IFRS)

#### Datas

**Escolha:** `DATE` para datas, `SMALLINT` para trimestre/ano

**Alternativas consideradas:**

| Tipo          | Prós                                    | Contras                                   | Decisão       |
| ------------- | --------------------------------------- | ----------------------------------------- | ------------- |
| **VARCHAR**   | Flexível                                | ❌ Sem validação, ordenação complexa      | Rejeitado     |
| **TIMESTAMP** | Suporta hora                            | ❌ Overhead desnecessário (4 bytes extra) | Rejeitado     |
| **DATE**      | ✅ Validação nativa, queries eficientes | Nenhum significativo                      | **ESCOLHIDO** |

**Justificativa:**

- Validação automática de datas inválidas
- Funções nativas (EXTRACT, DATE_TRUNC, intervalos)
- Índices B-tree otimizados
- 4 bytes vs 8 bytes do TIMESTAMP

---

## 📊 Importação de Dados

### 3.3 Tratamento de Inconsistências

#### Problema 1: Valores NULL em campos obrigatórios

**Abordagem:** **REJEITAR** linha inteira

**Justificativa:**

- Para campos críticos (`registro_ans`, `valor_despesas`): NULL invalida o registro
- Melhor rejeitar que inserir dados inconsistentes
- Registros rejeitados são logados para análise posterior

#### Problema 2: Strings em campos numéricos

**Abordagem:** **TENTATIVA DE CONVERSÃO** com fallback para rejeição

**Justificativa:**

- PostgreSQL faz conversão automática em `COPY`
- Se conversão falhar, linha é rejeitada automaticamente
- Para casos edge (ex: "R$ 1.500,00"), usa-se tabela temporária com `REGEXP_REPLACE`

#### Problema 3: Datas em formatos inconsistentes

**Abordagem:** **CONVERSÃO via tabela temporária**

**Justificativa:**

- Carregar primeiro em `VARCHAR`
- Aplicar `CASE WHEN` com múltiplos formatos
- Rejeitar apenas datas completamente inválidas
- Trimestre+Ano como campos separados (mais robusto)

---

## 🔍 Queries Analíticas

### Query 1: Top 5 Operadoras com Maior Crescimento Percentual

**Objetivo:** Identificar operadoras com maior crescimento entre 1º e último trimestre

**Desafio:** Operadoras podem não ter dados em todos os trimestres

**Abordagem escolhida:** Comparar **primeiro vs último registro disponível**

**Alternativas consideradas:**

| Abordagem                        | Prós                                | Contras                                | Decisão       |
| -------------------------------- | ----------------------------------- | -------------------------------------- | ------------- |
| Exigir dados em todos trimestres | Mais justo                          | ❌ Excluiria muitas operadoras         | Rejeitado     |
| Usar médias                      | Suaviza outliers                    | ❌ Mascara crescimento real            | Rejeitado     |
| Primeiro vs último disponível    | ✅ Inclusivo, mede crescimento real | Períodos podem variar entre operadoras | **ESCOLHIDO** |

**Tratamento de edge cases:**

- Operadoras com apenas 1 trimestre: crescimento = NULL (excluídas)
- Valor inicial = 0: usa valor absoluto do último trimestre
- Múltiplos registros no mesmo trimestre: soma agregada

---

### Query 2: Distribuição de Despesas por UF

**Objetivo:** Top 5 estados com maiores despesas + média por operadora em cada UF

**Desafio adicional:** Calcular média por operadora (não apenas total)

**Abordagem:** Agregação em dois níveis

1. Soma total por UF
2. Contagem de operadoras distintas por UF
3. Média = Total / Número de operadoras

**Métricas calculadas:**

- Total de despesas por UF
- Número de operadoras por UF
- Média simples (total ÷ num_operadoras)
- Média real (média das somas individuais)
- Mediana por operadora (mais robusta a outliers)
- Participação percentual no total nacional

---

### Query 3: Operadoras Acima da Média em 2+ Trimestres

**Objetivo:** Contar operadoras com despesas acima da média geral em pelo menos 2 dos 3 trimestres

**Trade-off técnico:** Múltiplas abordagens possíveis

**Alternativas consideradas:**

| Abordagem                                        | Prós                         | Contras                                 | Decisão       |
| ------------------------------------------------ | ---------------------------- | --------------------------------------- | ------------- |
| **1. Subqueries aninhadas**                      | Fácil de entender            | ❌ Lento, calcula média múltiplas vezes | Rejeitado     |
| **2. Window functions**                          | ✅ Performático, single-pass | Sintaxe mais complexa                   | **ESCOLHIDO** |
| **3. Tabela temporária com média pré-calculada** | Modular, fácil debug         | ❌ Overhead de I/O                      | Rejeitado     |

**Escolha: Window functions (alternativa 2)**

**Justificativa:**

- **Performance:** Uma única passada nos dados (single-pass)
- **Manutenibilidade:** Código auto-contido (sem dependências externas)
- **Legibilidade:** Aceitável com bons comentários

**Implementação:**

1. `WITH media_por_trimestre` – Calcula média geral por trimestre
2. `WITH comparacao_com_media` – Compara cada operadora com a média
3. `WITH contagem_trimestres_acima` – Conta trimestres acima da média
4. `SELECT final` – Filtra operadoras com 2+ trimestres acima

---

## 📈 Índices e Performance

### Índices Criados

**Tabela `operadoras`:**

- `PRIMARY KEY (registro_ans)` – B-tree automático
- `idx_operadoras_uf` – Análises por estado
- `idx_operadoras_modalidade` – Análises por tipo
- `idx_operadoras_cnpj` – Lookup rápido

**Tabela `despesas_consolidadas`:**

- `PRIMARY KEY (id)` – Chave surrogada
- `idx_despesas_registro_ans` – JOINs com operadoras
- `idx_despesas_trimestre_ano` – Filtros temporais
- `idx_despesas_valor DESC` – Rankings de despesas
- `idx_despesas_operadora_tempo` – Análises de crescimento temporal

**Tabela `despesas_agregadas`:**

- `PRIMARY KEY (id)` – Chave surrogada
- `UNIQUE (razao_social, uf)` – Garante consistência
- `idx_agregado_uf` – Análises por estado
- `idx_agregado_total_desc` – Rankings

### Otimizações

- `ANALYZE` após importação – Atualiza estatísticas do planner
- `FOREIGN KEY` com `ON UPDATE CASCADE` – Mantém integridade
- `CHECK constraints` – Valida dados na inserção
- Views materializadas preparadas (comentadas no schema)

---

## 🎯 Queries Implementadas

### Query 1: Top 5 Operadoras com Maior Crescimento Percentual

Identifica operadoras com maior crescimento entre primeiro e último trimestre disponível.

**Implementação:** CTEs com ROW_NUMBER para encontrar primeiro e último trimestre de cada operadora.

### Query 2: Top 5 UFs com Maior Despesa Total

Lista os 5 estados com maiores despesas totais, incluindo média por operadora em cada UF.

**Implementação:** Agregação em múltiplos níveis com cálculo de média simples, real e mediana.

### Query 3: Operadoras Acima da Média em 2+ Trimestres

Conta quantas operadoras tiveram despesas acima da média geral em pelo menos 2 dos 3 trimestres.

**Implementação:** Window functions com COUNT FILTER para performance otimizada.

---

## 🔧 Troubleshooting

### Erro de encoding no Windows

**Sintoma:** Caracteres especiais aparecem como `Ã`, `Ã§`, etc.

**Solução:** Configurar terminal PowerShell antes de executar:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

### Erro de caminho de arquivo

Os caminhos no `02_import.sql` são relativos. Certifique-se de executar o psql a partir da pasta `TESTE3/sql/`:

```bash
cd TESTE3/sql
psql -U postgres -d teste3_intuitivecare -f 02_import.sql
```

### Erro: database já existe

```bash
psql -U postgres -c "DROP DATABASE teste3_intuitivecare;"
psql -U postgres -c "CREATE DATABASE teste3_intuitivecare;"
```

---

## 📚 Documentação Adicional

### Referências PostgreSQL

- [PostgreSQL COPY Documentation](https://www.postgresql.org/docs/current/sql-copy.html)
- [PostgreSQL Window Functions](https://www.postgresql.org/docs/current/tutorial-window.html)
- [PostgreSQL Indexes](https://www.postgresql.org/docs/current/indexes.html)

---
