-- Query 1: Top 5 operadoras com maior crescimento percentual
WITH primeiro_trimestre AS (
    SELECT dc.registro_ans,
        o.razao_social,
        o.uf,
        o.modalidade,
        dc.ano * 4 + dc.trimestre as periodo,
        dc.valor_despesas,
        ROW_NUMBER() OVER (
            PARTITION BY dc.registro_ans
            ORDER BY dc.ano,
                dc.trimestre
        ) as rn_primeiro
    FROM despesas_consolidadas dc
        INNER JOIN operadoras o ON dc.registro_ans = o.registro_ans
),
ultimo_trimestre AS (
    SELECT dc.registro_ans,
        dc.ano * 4 + dc.trimestre as periodo,
        dc.valor_despesas,
        ROW_NUMBER() OVER (
            PARTITION BY dc.registro_ans
            ORDER BY dc.ano DESC,
                dc.trimestre DESC
        ) as rn_ultimo
    FROM despesas_consolidadas dc
),
crescimento AS (
    SELECT p.registro_ans,
        p.razao_social,
        p.uf,
        p.modalidade,
        p.periodo as periodo_inicial,
        u.periodo as periodo_final,
        p.valor_despesas as valor_inicial,
        u.valor_despesas as valor_final,
        u.valor_despesas - p.valor_despesas as variacao_absoluta,
        CASE
            WHEN p.valor_despesas > 0 THEN (
                (u.valor_despesas - p.valor_despesas) / p.valor_despesas * 100
            )
            WHEN p.valor_despesas = 0
            AND u.valor_despesas > 0 THEN 999.99
            ELSE 0
        END as crescimento_percentual
    FROM primeiro_trimestre p
        INNER JOIN ultimo_trimestre u ON p.registro_ans = u.registro_ans
    WHERE p.rn_primeiro = 1
        AND u.rn_ultimo = 1
        AND p.periodo < u.periodo
)
SELECT razao_social,
    uf,
    modalidade,
    (periodo_inicial / 4) as ano_inicial,
    (periodo_inicial % 4 + 1) as trimestre_inicial,
    (periodo_final / 4) as ano_final,
    (periodo_final % 4 + 1) as trimestre_final,
    ROUND(valor_inicial::numeric, 2) as despesa_inicial,
    ROUND(valor_final::numeric, 2) as despesa_final,
    ROUND(variacao_absoluta::numeric, 2) as variacao_absoluta,
    ROUND(crescimento_percentual::numeric, 2) as crescimento_percentual
FROM crescimento
WHERE valor_final > valor_inicial
ORDER BY crescimento_percentual DESC,
    variacao_absoluta DESC
LIMIT 5;
-- Query 2: Top 5 UFs com maior despesa total
WITH despesas_por_uf AS (
    SELECT o.uf,
        COUNT(DISTINCT dc.registro_ans) as num_operadoras,
        SUM(dc.valor_despesas) as total_despesas,
        AVG(dc.valor_despesas) as media_por_registro,
        MIN(dc.valor_despesas) as menor_despesa,
        MAX(dc.valor_despesas) as maior_despesa,
        STDDEV(dc.valor_despesas) as desvio_padrao
    FROM despesas_consolidadas dc
        INNER JOIN operadoras o ON dc.registro_ans = o.registro_ans
    WHERE o.uf IS NOT NULL
    GROUP BY o.uf
),
despesas_por_operadora_uf AS (
    SELECT o.uf,
        dc.registro_ans,
        o.razao_social,
        SUM(dc.valor_despesas) as total_operadora_uf
    FROM despesas_consolidadas dc
        INNER JOIN operadoras o ON dc.registro_ans = o.registro_ans
    WHERE o.uf IS NOT NULL
    GROUP BY o.uf,
        dc.registro_ans,
        o.razao_social
),
media_por_operadora AS (
    SELECT uf,
        AVG(total_operadora_uf) as media_por_operadora_uf,
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY total_operadora_uf
        ) as mediana_por_operadora
    FROM despesas_por_operadora_uf
    GROUP BY uf
)
SELECT duf.uf,
    duf.num_operadoras,
    CONCAT(
        'R$ ',
        TO_CHAR(duf.total_despesas, 'FM999G999G999G999G999D00')
    ) as total_despesas_formatado,
    ROUND(duf.total_despesas::numeric, 2) as total_despesas,
    ROUND(
        (duf.total_despesas / duf.num_operadoras)::numeric,
        2
    ) as media_simples_por_operadora,
    ROUND(mpo.media_por_operadora_uf::numeric, 2) as media_real_por_operadora,
    ROUND(mpo.mediana_por_operadora::numeric, 2) as mediana_por_operadora,
    ROUND(
        (
            (
                duf.total_despesas / SUM(duf.total_despesas) OVER ()
            )::numeric * 100
        ),
        2
    ) as percentual_nacional
FROM despesas_por_uf duf
    INNER JOIN media_por_operadora mpo ON duf.uf = mpo.uf
ORDER BY duf.total_despesas DESC
LIMIT 5;
\ echo '' \ echo 'Top 3 operadoras por UF (nos 5 maiores estados):' WITH top_ufs AS (
    SELECT o.uf
    FROM despesas_consolidadas dc
        INNER JOIN operadoras o ON dc.registro_ans = o.registro_ans
    WHERE o.uf IS NOT NULL
    GROUP BY o.uf
    ORDER BY SUM(dc.valor_despesas) DESC
    LIMIT 5
), operadoras_por_uf AS (
    SELECT o.uf,
        o.razao_social,
        SUM(dc.valor_despesas) as total_despesas,
        ROW_NUMBER() OVER (
            PARTITION BY o.uf
            ORDER BY SUM(dc.valor_despesas) DESC
        ) as ranking
    FROM despesas_consolidadas dc
        INNER JOIN operadoras o ON dc.registro_ans = o.registro_ans
    WHERE o.uf IN (
            SELECT uf
            FROM top_ufs
        )
    GROUP BY o.uf,
        o.razao_social
)
SELECT uf,
    ranking as posicao,
    razao_social,
    CONCAT(
        'R$ ',
        TO_CHAR(total_despesas, 'FM999G999G999G999D00')
    ) as total_despesas
FROM operadoras_por_uf
WHERE ranking <= 3
ORDER BY uf,
    ranking;
-- Query 3: Operadoras com despesas acima da média em 2+ trimestres
WITH media_por_trimestre AS (
    SELECT ano,
        trimestre,
        AVG(valor_despesas) as media_geral
    FROM despesas_consolidadas
    GROUP BY ano,
        trimestre
),
comparacao_com_media AS (
    SELECT dc.registro_ans,
        o.razao_social,
        dc.ano,
        dc.trimestre,
        dc.valor_despesas,
        m.media_geral,
        CASE
            WHEN dc.valor_despesas > m.media_geral THEN 1
            ELSE 0
        END as acima_da_media
    FROM despesas_consolidadas dc
        INNER JOIN operadoras o ON dc.registro_ans = o.registro_ans
        INNER JOIN media_por_trimestre m ON dc.ano = m.ano
        AND dc.trimestre = m.trimestre
),
contagem_trimestres_acima AS (
    SELECT registro_ans,
        razao_social,
        SUM(acima_da_media) as trimestres_acima_media,
        COUNT(*) as total_trimestres,
        AVG(valor_despesas) as media_despesas_operadora,
        MAX(
            CASE
                WHEN acima_da_media = 1 THEN valor_despesas
            END
        ) as maior_despesa_acima_media
    FROM comparacao_com_media
    GROUP BY registro_ans,
        razao_social
)
SELECT COUNT(*) as total_operadoras,
    COUNT(*) FILTER (
        WHERE trimestres_acima_media >= 2
    ) as operadoras_acima_media_2plus,
    ROUND(
        (
            COUNT(*) FILTER (
                WHERE trimestres_acima_media >= 2
            )::NUMERIC / COUNT(*) * 100
        ),
        2
    ) as percentual
FROM contagem_trimestres_acima;
\ echo '' \ echo 'Exemplos de operadoras acima da média em 2+ trimestres:' WITH media_por_trimestre AS (
    SELECT ano,
        trimestre,
        AVG(valor_despesas) as media_geral
    FROM despesas_consolidadas
    GROUP BY ano,
        trimestre
),
comparacao_com_media AS (
    SELECT dc.registro_ans,
        o.razao_social,
        o.uf,
        dc.ano,
        dc.trimestre,
        dc.valor_despesas,
        m.media_geral,
        CASE
            WHEN dc.valor_despesas > m.media_geral THEN 1
            ELSE 0
        END as acima_da_media
    FROM despesas_consolidadas dc
        INNER JOIN operadoras o ON dc.registro_ans = o.registro_ans
        INNER JOIN media_por_trimestre m ON dc.ano = m.ano
        AND dc.trimestre = m.trimestre
),
contagem_trimestres_acima AS (
    SELECT registro_ans,
        razao_social,
        uf,
        SUM(acima_da_media) as trimestres_acima_media,
        COUNT(*) as total_trimestres,
        AVG(valor_despesas) as media_despesas_operadora
    FROM comparacao_com_media
    GROUP BY registro_ans,
        razao_social,
        uf
)
SELECT razao_social,
    uf,
    trimestres_acima_media,
    total_trimestres,
    ROUND(media_despesas_operadora::numeric, 2) as media_despesas,
    CONCAT(
        ROUND(
            (
                trimestres_acima_media::NUMERIC / total_trimestres * 100
            ),
            0
        ),
        '%'
    ) as percentual_acima_media
FROM contagem_trimestres_acima
WHERE trimestres_acima_media >= 2
ORDER BY trimestres_acima_media DESC,
    media_despesas_operadora DESC
LIMIT 10;
-- Query complementar: Distribuição por modalidade
SELECT o.modalidade,
    COUNT(DISTINCT o.registro_ans) as num_operadoras,
    CONCAT(
        'R$ ',
        TO_CHAR(SUM(dc.valor_despesas), 'FM999G999G999G999D00')
    ) as total_despesas,
    ROUND(AVG(dc.valor_despesas)::numeric, 2) as media_por_registro
FROM despesas_consolidadas dc
    INNER JOIN operadoras o ON dc.registro_ans = o.registro_ans
WHERE o.modalidade IS NOT NULL
GROUP BY o.modalidade
ORDER BY SUM(dc.valor_despesas) DESC;
\ echo '' \ echo 'Evolução temporal das despesas:'
SELECT ano,
    trimestre,
    COUNT(DISTINCT registro_ans) as num_operadoras,
    CONCAT(
        'R$ ',
        TO_CHAR(SUM(valor_despesas), 'FM999G999G999G999D00')
    ) as total_despesas,
    ROUND(AVG(valor_despesas)::numeric, 2) as media_por_registro
FROM despesas_consolidadas
GROUP BY ano,
    trimestre
ORDER BY ano,
    trimestre;