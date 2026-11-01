-- =====================================================================
-- Tabelas da IA de triagem (Sprint 4), conforme o modelo da Sprint 3
-- (README, seção "Dados necessários"). Rodar uma vez no schema do Oracle
-- da FIAP, o mesmo da API .NET.
--
-- Evoluções em relação à Sprint 3:
-- 1. T_ANIMAL não é criada: o cadastro de animais já existe na aplicação
--    da CLYVO VET (T_CP_ANIMAIS, mantida pela API .NET), com os mesmos
--    campos (NAME, SPECIES, BREED, BIRTH_DATE). SPECIES usa DOG | CAT.
-- 2. As chaves estrangeiras para T_CP_ANIMAIS usam ON DELETE CASCADE: a API
--    .NET apaga o animal fisicamente, e uma FK comum bloquearia o DELETE
--    (ORA-02292) assim que o animal tivesse leituras.
-- 3. T_AI_RECOMMENDATION ganhou ALERT_LEVEL (NORMAL | ATENCAO | ALERTA),
--    para a clínica filtrar o que precisa de atenção.
-- =====================================================================

-- Base de conhecimento curada por espécie e raça (fonte do RAG).
-- BREED = 'SRD' é a ficha genérica da espécie, usada quando a raça não
-- está na base; MIN_WEIGHT e MAX_WEIGHT nulos = sem faixa de peso.
CREATE TABLE T_BREED_CARE (
    ID               NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    SPECIES          VARCHAR2(20)  NOT NULL CHECK (SPECIES IN ('DOG', 'CAT')),
    BREED            VARCHAR2(100) NOT NULL,
    MIN_WEIGHT       NUMBER(10,2),
    MAX_WEIGHT       NUMBER(10,2),
    VACCINE_SCHEDULE CLOB,
    CARE_NOTES       CLOB,
    CONSTRAINT UQ_BREED_CARE UNIQUE (SPECIES, BREED)
);

-- Relato do tutor: texto livre e/ou foto do sintoma.
-- A imagem não fica no Oracle: IMAGE_URL aponta para o storage externo.
CREATE TABLE T_TUTOR_REPORT (
    ID           NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ANIMAL_ID    NUMBER(10) NOT NULL
                 REFERENCES T_CP_ANIMAIS(ID) ON DELETE CASCADE,
    REPORT_TEXT  VARCHAR2(2000),
    IMAGE_URL    VARCHAR2(500),
    REPORT_DATE  DATE DEFAULT SYSDATE NOT NULL,
    CONSTRAINT CK_TUTOR_REPORT_CONTEUDO
        CHECK (REPORT_TEXT IS NOT NULL OR IMAGE_URL IS NOT NULL)
);

-- Toda recomendação gerada pela IA, para rastreabilidade e auditoria.
CREATE TABLE T_AI_RECOMMENDATION (
    ID                  NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ANIMAL_ID           NUMBER(10) NOT NULL
                        REFERENCES T_CP_ANIMAIS(ID) ON DELETE CASCADE,
    SOURCE              VARCHAR2(20) NOT NULL
                        CHECK (SOURCE IN ('PESO', 'RELATO', 'CUIDADO_RACA')),
    ALERT_LEVEL         VARCHAR2(10) NOT NULL
                        CHECK (ALERT_LEVEL IN ('NORMAL', 'ATENCAO', 'ALERTA')),
    RECOMMENDATION_TEXT CLOB NOT NULL,
    CREATED_AT          DATE DEFAULT SYSDATE NOT NULL
);

-- Leituras da balança (gravadas pelo Node-RED), no modelo da Sprint 3:
-- o nome solto do animal (coluna ANIMAL das Sprints 1 e 2) vira ANIMAL_ID.
-- Fica neste schema, junto de T_CP_ANIMAIS, para a IA ler as duas.
CREATE TABLE T_EXAM_READING (
    ID         NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ANIMAL_ID  NUMBER(10) NOT NULL
               REFERENCES T_CP_ANIMAIS(ID) ON DELETE CASCADE,
    READING    NUMBER(10,2) NOT NULL,
    DATETIME   DATE DEFAULT SYSDATE NOT NULL
);

-- Conferência
SELECT TABLE_NAME FROM USER_TABLES
 WHERE TABLE_NAME IN ('T_BREED_CARE', 'T_TUTOR_REPORT', 'T_AI_RECOMMENDATION', 'T_EXAM_READING');
