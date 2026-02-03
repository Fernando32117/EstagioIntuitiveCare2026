DROP TABLE IF EXISTS despesas_consolidadas CASCADE;
DROP TABLE IF EXISTS despesas_agregadas CASCADE;
DROP TABLE IF EXISTS operadoras CASCADE;
CREATE TABLE operadoras (
    registro_ans VARCHAR(6) PRIMARY KEY,
    cnpj VARCHAR(14),
    razao_social VARCHAR(255) NOT NULL,
    modalidade VARCHAR(100),
    uf CHAR(2),
    data_cadastro DATE DEFAULT CURRENT_DATE,
    CONSTRAINT chk_uf CHECK (uf ~ '^[A-Z]{2}$'),
    CONSTRAINT chk_registro_ans CHECK (registro_ans ~ '^\d{6}$')
);
CREATE INDEX idx_operadoras_uf ON operadoras(uf);
CREATE INDEX idx_operadoras_modalidade ON operadoras(modalidade);
CREATE INDEX idx_operadoras_cnpj ON operadoras(cnpj);
CREATE TABLE despesas_consolidadas (
    id SERIAL PRIMARY KEY,
    registro_ans VARCHAR(6) NOT NULL,
    razao_social VARCHAR(255),
    trimestre SMALLINT NOT NULL,
    ano SMALLINT NOT NULL,
    valor_despesas DECIMAL(15, 2) NOT NULL,
    data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_operadora FOREIGN KEY (registro_ans) REFERENCES operadoras(registro_ans) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_trimestre CHECK (
        trimestre BETWEEN 1 AND 4
    ),
    CONSTRAINT chk_ano CHECK (
        ano BETWEEN 2000 AND 2100
    ),
    CONSTRAINT chk_valor_despesas CHECK (valor_despesas >= 0)
);
CREATE INDEX idx_despesas_registro_ans ON despesas_consolidadas(registro_ans);
CREATE INDEX idx_despesas_trimestre_ano ON despesas_consolidadas(trimestre, ano);
CREATE INDEX idx_despesas_ano_trimestre ON despesas_consolidadas(ano, trimestre);
CREATE INDEX idx_despesas_valor ON despesas_consolidadas(valor_despesas DESC);
CREATE INDEX idx_despesas_operadora_tempo ON despesas_consolidadas(registro_ans, ano, trimestre);
CREATE TABLE despesas_agregadas (
    id SERIAL PRIMARY KEY,
    razao_social VARCHAR(255) NOT NULL,
    uf CHAR(2) NOT NULL,
    total_despesas DECIMAL(15, 2) NOT NULL,
    media_despesas_trimestre DECIMAL(15, 2) NOT NULL,
    desvio_padrao_despesas DECIMAL(15, 2) NOT NULL,
    data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_agregado_uf CHECK (uf ~ '^[A-Z]{2}$'),
    CONSTRAINT chk_agregado_total CHECK (total_despesas >= 0),
    CONSTRAINT chk_agregado_media CHECK (media_despesas_trimestre >= 0),
    CONSTRAINT chk_agregado_desvio CHECK (desvio_padrao_despesas >= 0),
    CONSTRAINT uq_operadora_uf UNIQUE (razao_social, uf)
);
CREATE INDEX idx_agregado_uf ON despesas_agregadas(uf);
CREATE INDEX idx_agregado_total_desc ON despesas_agregadas(total_despesas DESC);
CREATE INDEX idx_agregado_razao_social ON despesas_agregadas(razao_social);
COMMENT ON TABLE despesas_agregadas IS 'Dados agregados de despesas por operadora e UF';
COMMENT ON COLUMN despesas_agregadas.total_despesas IS 'Soma total de despesas da operadora no estado';
CREATE OR REPLACE VIEW vw_despesas_enriquecidas AS
SELECT dc.id,
    dc.registro_ans,
    COALESCE(o.razao_social, dc.razao_social) as razao_social,
    o.modalidade,
    o.uf,
    dc.trimestre,
    dc.ano,
    dc.valor_despesas,
    TO_DATE(
        dc.ano::text || '-' || (dc.trimestre * 3)::text || '-01',
        'YYYY-MM-DD'
    ) as data_referencia
FROM despesas_consolidadas dc
    LEFT JOIN operadoras o ON dc.registro_ans = o.registro_ans;
COMMENT ON VIEW vw_despesas_enriquecidas IS 'Despesas consolidadas enriquecidas com dados cadastrais';
ANALYZE operadoras;
ANALYZE despesas_consolidadas;
ANALYZE despesas_agregadas;