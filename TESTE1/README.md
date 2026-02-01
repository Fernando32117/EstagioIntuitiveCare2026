# Teste 1 – Integração com API Pública (ANS)

Este projeto implementa o Teste 1 do processo seletivo para Estágio na IntuitiveCare.

O objetivo é realizar a integração com a base pública de dados da ANS (Agência Nacional de Saúde Suplementar), realizando o download automático dos arquivos de Demonstrações Contábeis mais recentes, extraindo, processando e consolidando informações de despesas em um único arquivo CSV.

---

## 🛠️ Tecnologias Utilizadas

-Python 3.14.2
-requests – download de arquivos
-pandas – processamento e consolidação de dados
-pathlib – manipulação de caminhos
-logging – rastreabilidade do pipeline

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

TESTE1/
├── data/
│   ├── raw/
│   └── extracted/
│
├── output/
│   ├── consolidado_despesas.csv
│   └── consolidado_despesas.zip
│
├── src/
│   ├── cleaners/
│   │   └── __init__.py
│   ├── downloader/
│   │   └── ans_downloader.py
│   ├── extractor/
│   │   └── zip_extractor.py
│   ├── filters/
│   │   └── __init__.py
│   ├── normalizer/
│   │   └── expenses_normalizer.py
│   ├── processor/
│   │   └── expenses_processor.py
│   ├── readers/
│   │   └── __init__.py
│   ├── utils/
│   │   └── zip_utils.py
│   └── main.py
│
├── README.md
└── requirements.txt
```

---

## Como Executar

1. Instale as dependências:

```bash
   pip install -r requirements.txt
```

2. Execute o pipeline:

```bash
   python src/main.py
```

3. O arquivo final será gerado em:
   - output/consolidado_despesas.csv (formato: CNPJ, RazaoSocial, Trimestre, Ano, ValorDespesas)
   - output/consolidado_despesas.zip

---

## 🧠 Decisões Técnicas e Trade-offs

### 1.2 Processamento de Arquivos - Trade-off de Memória

**Decisão:** Processamento INCREMENTAL (arquivo por arquivo)

**Alternativas consideradas:**

- ✅ **INCREMENTAL** (escolhida): Processa um arquivo por vez, concatena ao final
  - **Prós:** Usa menos memória, melhor para arquivos grandes (100MB+), progresso visível
  - **Contras:** Mais lento em I/O, múltiplas operações de leitura
- ❌ **EM MEMÓRIA**: Carregar todos os arquivos de uma vez
  - **Prós:** Mais rápido para arquivos pequenos
  - **Contras:** Risco de estouro de memória com arquivos grandes da ANS

**Justificativa:** Os arquivos da ANS podem ter centenas de MB. O processamento incremental garante que o sistema funcione mesmo com recursos limitados e fornece feedback contínuo do progresso.

---

### 1.2 Suporte a Múltiplos Formatos

**Implementação:** Suporte automático a CSV, TXT e XLSX

O sistema detecta automaticamente:

- Separadores (;, ,, \t, |)
- Encoding (latin1, utf-8)
- Estrutura de colunas variadas

**Estratégia:** Identificação inteligente de colunas por palavras-chave (REG_ANS, CNPJ, RAZAO_SOCIAL, etc.)

---

### 1.2 Identificação de Despesas com Eventos/Sinistros

**Critérios adotados:**

- Código contábil iniciando com **411** (Despesas com Eventos/Sinistros)
- Palavras-chave na descrição: EVENTO, SINISTRO, ASSISTENCIA, INTERNACAO, CONSULTA, EXAME, PROCEDIMENTO

**Justificativa:** A ANS não fornece campo explícito. Essa abordagem combina identificação contábil com análise textual para maximizar cobertura.

---

## ⚠️ Tratamento de Inconsistências (1.3)

### Estratégias Implementadas:

#### 1. CNPJs duplicados com razões sociais diferentes

- **Estratégia:** MANTÉM todos os registros, registra no log para análise posterior
- **Justificativa:** Pode representar:
  - Mudança legítima de razão social
  - Erro nos dados da ANS
  - Fusões/aquisições
- **Ação recomendada:** Análise manual dos casos marcados no log

#### 2. Valores zerados ou negativos

- **Valores negativos:** REMOVIDOS (indicam erro de processamento)
- **Valores zerados:** MANTIDOS (podem representar ausência de despesa no período)
- **Justificativa:** Zeros são informação válida, negativos não fazem sentido contábil

#### 3. Trimestres com formatos inconsistentes

- **Estratégia:** Extração automática do padrão "XTyyyy" das pastas
- **Padronização:** Formato numérico (1-4)
- **Registros inválidos:** Marcados como trimestre 0 para revisão

---

## 📋 Formato do CSV Final

Conforme especificação do teste, o CSV consolidado contém exatamente as colunas:

```
CNPJ,RazaoSocial,Trimestre,Ano,ValorDespesas
```

**Observações:**

- CNPJ pode ser o REG_ANS quando CNPJ não está disponível nos arquivos da ANS
- RazaoSocial preenchida como "NÃO INFORMADO" quando ausente
- Separador: vírgula (,)
- Encoding: UTF-8

---

## 🔗 Limitação dos Dados e Enriquecimento Cadastral

Os arquivos de Demonstrações Contábeis disponibilizados pela ANS **não contêm**
informações cadastrais como CNPJ ou Razão Social das operadoras.

Esses arquivos utilizam o identificador **REG_ANS** como chave primária da operadora,
enquanto os dados cadastrais (CNPJ, Razão Social, Modalidade, UF) estão disponíveis
em um conjunto de dados separado, no arquivo `Relatorio_cadop.csv`, conforme
documentado pela própria ANS.

**Solução:** O enriquecimento com dados cadastrais será realizado no **TESTE 2**.

---
