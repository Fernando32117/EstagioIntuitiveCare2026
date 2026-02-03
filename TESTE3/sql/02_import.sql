\set ON_ERROR_STOP on

-- ==============================================================================
-- IMPORTAÇÃO 1: OPERADORAS
-- ==============================================================================

CREATE TEMP TABLE temp_operadoras (
    registro_ans TEXT,
    cnpj TEXT,
    razao_social TEXT,
    nome_fantasia TEXT,
    modalidade TEXT,
    logradouro TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    cidade TEXT,
    uf TEXT,
    cep TEXT,
    ddd TEXT,
    telefone TEXT,
    fax TEXT,
    endereco_eletronico TEXT,
    representante TEXT,
    cargo_representante TEXT,
    regiao_comercializacao TEXT,
    data_registro_ans TEXT
);

\copy temp_operadoras FROM '../../TESTE2/data/cadastro/Relatorio_cadop.csv' WITH (FORMAT CSV, HEADER true, ENCODING 'LATIN1', DELIMITER ';')

INSERT INTO operadoras (registro_ans, cnpj, razao_social, modalidade, uf)
SELECT 
    REGEXP_REPLACE(TRIM(registro_ans), '[^0-9]', '', 'g') as registro_ans,
    CASE
        WHEN TRIM(cnpj) = '' THEN NULL
        ELSE REGEXP_REPLACE(TRIM(cnpj), '[^0-9]', '', 'g')
    END as cnpj,
    UPPER(TRIM(razao_social)) as razao_social,
    TRIM(modalidade) as modalidade,
    UPPER(TRIM(uf)) as uf
FROM temp_operadoras
WHERE TRIM(registro_ans) != ''
    AND LENGTH(REGEXP_REPLACE(TRIM(registro_ans), '[^0-9]', '', 'g')) = 6
    AND TRIM(razao_social) != ''
    AND TRIM(razao_social) != 'NÃO INFORMADO'
ON CONFLICT (registro_ans) DO UPDATE
SET cnpj = EXCLUDED.cnpj,
    razao_social = EXCLUDED.razao_social,
    modalidade = EXCLUDED.modalidade,
    uf = EXCLUDED.uf;

\echo 'Operadoras importadas:'
SELECT COUNT(*) as total_operadoras FROM operadoras;

DROP TABLE temp_operadoras;

-- ==============================================================================
-- IMPORTAÇÃO 2: DESPESAS CONSOLIDADAS
-- ==============================================================================

CREATE TEMP TABLE temp_despesas_consolidadas (
    cnpj TEXT,
    razao_social TEXT,
    trimestre TEXT,
    ano TEXT,
    valor_despesas TEXT
);

\copy temp_despesas_consolidadas FROM '../../TESTE1/output/consolidado_despesas.csv' WITH (FORMAT CSV, HEADER true, ENCODING 'UTF8', DELIMITER ',')

INSERT INTO operadoras (registro_ans, razao_social)
SELECT DISTINCT
    REGEXP_REPLACE(TRIM(cnpj), '[^0-9]', '', 'g') as registro_ans,
    COALESCE(NULLIF(UPPER(TRIM(razao_social)), ''), 'OPERADORA NÃO CADASTRADA') as razao_social
FROM temp_despesas_consolidadas
WHERE LENGTH(REGEXP_REPLACE(TRIM(cnpj), '[^0-9]', '', 'g')) = 6
    AND NOT EXISTS (
        SELECT 1 FROM operadoras o 
        WHERE o.registro_ans = REGEXP_REPLACE(TRIM(temp_despesas_consolidadas.cnpj), '[^0-9]', '', 'g')
    )
ON CONFLICT (registro_ans) DO NOTHING;

INSERT INTO despesas_consolidadas (registro_ans, razao_social, trimestre, ano, valor_despesas)
SELECT 
    REGEXP_REPLACE(TRIM(cnpj), '[^0-9]', '', 'g') as registro_ans,
    UPPER(TRIM(razao_social)) as razao_social,
    CAST(TRIM(trimestre) AS SMALLINT) as trimestre,
    CAST(TRIM(ano) AS SMALLINT) as ano,
    CAST(
        REGEXP_REPLACE(
            REPLACE(REPLACE(TRIM(valor_despesas), 'R$', ''), ' ', ''),
            '[^0-9.]',
            '',
            'g'
        ) AS DECIMAL(15, 2)
    ) as valor_despesas
FROM temp_despesas_consolidadas
WHERE TRIM(cnpj) != ''
    AND TRIM(trimestre) ~ '^\d+$'
    AND TRIM(ano) ~ '^\d{4}$'
    AND TRIM(valor_despesas) != ''
    AND CAST(TRIM(trimestre) AS INT) BETWEEN 1 AND 4
    AND CAST(
        REGEXP_REPLACE(
            REPLACE(REPLACE(TRIM(valor_despesas), 'R$', ''), ' ', ''),
            '[^0-9.]',
            '',
            'g'
        ) AS NUMERIC
    ) >= 0;

\echo 'Despesas consolidadas importadas:'
SELECT COUNT(*) as total_registros FROM despesas_consolidadas;

\echo 'Período coberto:'
SELECT MIN(ano) as ano_inicial, MAX(ano) as ano_final, COUNT(DISTINCT (ano || '-' || trimestre)) as trimestres_distintos FROM despesas_consolidadas;

DROP TABLE temp_despesas_consolidadas;

-- ==============================================================================
-- IMPORTAÇÃO 3: DESPESAS AGREGADAS
-- ==============================================================================

CREATE TEMP TABLE temp_despesas_agregadas (
    razao_social TEXT,
    uf TEXT,
    total_despesas TEXT,
    media_despesas_trimestre TEXT,
    desvio_padrao_despesas TEXT
);

\copy temp_despesas_agregadas FROM '../../TESTE2/output/despesas_agregadas.csv' WITH (FORMAT CSV, HEADER true, ENCODING 'UTF8', DELIMITER ',')

INSERT INTO despesas_agregadas (razao_social, uf, total_despesas, media_despesas_trimestre, desvio_padrao_despesas)
SELECT 
    UPPER(TRIM(razao_social)) as razao_social,
    UPPER(TRIM(uf)) as uf,
    CAST(TRIM(total_despesas) AS DECIMAL(15, 2)) as total_despesas,
    CAST(TRIM(media_despesas_trimestre) AS DECIMAL(15, 2)) as media_despesas_trimestre,
    CAST(TRIM(desvio_padrao_despesas) AS DECIMAL(15, 2)) as desvio_padrao_despesas
FROM temp_despesas_agregadas
WHERE TRIM(razao_social) != ''
    AND TRIM(uf) != ''
    AND TRIM(total_despesas) ~ '^[0-9.]+$'
    AND TRIM(media_despesas_trimestre) ~ '^[0-9.]+$'
    AND TRIM(desvio_padrao_despesas) ~ '^[0-9.]+$';

\echo 'Despesas agregadas importadas:'
SELECT COUNT(*) as total_grupos FROM despesas_agregadas;

DROP TABLE temp_despesas_agregadas;

-- ==============================================================================
-- VALIDAÇÃO FINAL
-- ==============================================================================

\echo ''
\echo 'Resumo da Base de Dados:'
SELECT 'Operadoras' as tabela, COUNT(*) as total_registros, pg_size_pretty(pg_total_relation_size('operadoras')) as tamanho FROM operadoras
UNION ALL
SELECT 'Despesas Consolidadas', COUNT(*), pg_size_pretty(pg_total_relation_size('despesas_consolidadas')) FROM despesas_consolidadas
UNION ALL
SELECT 'Despesas Agregadas', COUNT(*), pg_size_pretty(pg_total_relation_size('despesas_agregadas')) FROM despesas_agregadas;

ANALYZE operadoras;
ANALYZE despesas_consolidadas;
ANALYZE despesas_agregadas;

\echo ''
\echo 'Importação concluída com sucesso!'
