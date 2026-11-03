-- =====================================================================
-- Base de cuidados por espécie e raça (contexto do RAG).
-- Valores de referência para adultos, compilados de guias gerais de
-- vacinação (WSAVA) e de padrões de raça: servem para a triagem orientar
-- o tutor, e não substituem a avaliação do veterinário.
-- Pode rodar de novo: apaga e recria as fichas.
-- =====================================================================

DELETE FROM T_BREED_CARE;

-- ---------- Cães ----------
INSERT INTO T_BREED_CARE (SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES) VALUES (
  'DOG', 'SRD', NULL, NULL,
  'Polivalente (V8 ou V10): 1a dose entre 6 e 8 semanas, reforços a cada 3 a 4 semanas até 16 semanas e reforço anual. Antirrábica: a partir de 12 semanas, reforço anual. Opcionais conforme o risco: gripe canina (tosse dos canis), giárdia e leishmaniose.',
  'Sem raça definida: o peso ideal varia com o porte, então acompanhe pela variação entre pesagens e pelo escore corporal (costelas palpáveis, cintura visível). Vermifugação e controle de pulgas e carrapatos regulares.'
);
INSERT INTO T_BREED_CARE (SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES) VALUES (
  'DOG', 'Labrador Retriever', 25.00, 36.00,
  'Polivalente (V8 ou V10): 1a dose entre 6 e 8 semanas, reforços a cada 3 a 4 semanas até 16 semanas e reforço anual. Antirrábica: a partir de 12 semanas, reforço anual.',
  'Forte tendência à obesidade: controlar a porção e garantir exercício diário. Predisposição a displasia de quadril e cotovelo; mancar ou relutar em levantar merece avaliação.'
);
INSERT INTO T_BREED_CARE (SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES) VALUES (
  'DOG', 'Golden Retriever', 25.00, 34.00,
  'Polivalente (V8 ou V10): 1a dose entre 6 e 8 semanas, reforços a cada 3 a 4 semanas até 16 semanas e reforço anual. Antirrábica: a partir de 12 semanas, reforço anual.',
  'Predisposição a displasia de quadril, dermatites e otites: escovação frequente e orelhas secas após o banho. Tendência a ganhar peso.'
);
INSERT INTO T_BREED_CARE (SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES) VALUES (
  'DOG', 'Pastor Alemão', 22.00, 40.00,
  'Polivalente (V8 ou V10): 1a dose entre 6 e 8 semanas, reforços a cada 3 a 4 semanas até 16 semanas e reforço anual. Antirrábica: a partir de 12 semanas, reforço anual.',
  'Predisposição a displasia de quadril e problemas digestivos; barriga distendida com tentativa de vômito sem sucesso é emergência (torção gástrica).'
);
INSERT INTO T_BREED_CARE (SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES) VALUES (
  'DOG', 'Bulldog Francês', 8.00, 14.00,
  'Polivalente (V8 ou V10): 1a dose entre 6 e 8 semanas, reforços a cada 3 a 4 semanas até 16 semanas e reforço anual. Antirrábica: a partir de 12 semanas, reforço anual.',
  'Raça braquicefálica: muito sensível ao calor e ao esforço; respiração ruidosa ou cansaço fácil merecem atenção; gengiva arroxeada ou dificuldade para respirar é emergência. Limpar e secar as dobras da pele. O sobrepeso piora a respiração.'
);
INSERT INTO T_BREED_CARE (SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES) VALUES (
  'DOG', 'Shih Tzu', 4.00, 7.50,
  'Polivalente (V8 ou V10): 1a dose entre 6 e 8 semanas, reforços a cada 3 a 4 semanas até 16 semanas e reforço anual. Antirrábica: a partir de 12 semanas, reforço anual.',
  'Raça braquicefálica: evitar calor e esforço intenso. Olhos proeminentes, sujeitos a úlceras: olho vermelho ou fechado merece avaliação rápida. Higiene da face e escovação dos dentes.'
);
INSERT INTO T_BREED_CARE (SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES) VALUES (
  'DOG', 'Yorkshire Terrier', 2.00, 3.50,
  'Polivalente (V8 ou V10): 1a dose entre 6 e 8 semanas, reforços a cada 3 a 4 semanas até 16 semanas e reforço anual. Antirrábica: a partir de 12 semanas, reforço anual.',
  'Porte muito pequeno: pequenas variações de peso já são proporcionalmente grandes. Doença periodontal comum (escovação dos dentes) e luxação de patela (pular ao andar).'
);

INSERT INTO T_BREED_CARE (SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES) VALUES (
  'DOG', 'Pug', 6.00, 9.00,
  'Polivalente (V8 ou V10): 1a dose entre 6 e 8 semanas, reforços a cada 3 a 4 semanas até 16 semanas e reforço anual. Antirrábica: a partir de 12 semanas, reforço anual.',
  'Raça braquicefálica: muito sensível ao calor e ao esforço; ronco alto e cansaço fácil merecem atenção; gengiva arroxeada ou dificuldade para respirar é emergência. Tendência forte à obesidade, que piora a respiração e as articulações. Olhos proeminentes e dobras do focinho exigem limpeza diária.'
);

-- ---------- Gatos ----------
INSERT INTO T_BREED_CARE (SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES) VALUES (
  'CAT', 'SRD', 3.50, 5.50,
  'Polivalente felina (V3, V4 ou V5): 1a dose entre 6 e 8 semanas, reforços a cada 3 a 4 semanas até 16 semanas e reforço anual. Antirrábica: a partir de 12 semanas, reforço anual. A V5 inclui FeLV: testar o gato antes de vacinar.',
  'Gatos escondem sinais de doença: perda de peso e falta de apetite por mais de 24 horas merecem atenção. Estimular a ingestão de água (fonte, sachê) para prevenir doença do trato urinário; gato macho que não consegue urinar é emergência.'
);
INSERT INTO T_BREED_CARE (SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES) VALUES (
  'CAT', 'Siamês', 3.00, 5.00,
  'Polivalente felina (V3, V4 ou V5): 1a dose entre 6 e 8 semanas, reforços a cada 3 a 4 semanas até 16 semanas e reforço anual. Antirrábica: a partir de 12 semanas, reforço anual.',
  'Raça esguia: o peso ideal é menor que o de outros gatos. Predisposição a problemas dentários e respiratórios. Muito sociável: mudanças de comportamento costumam indicar desconforto.'
);
INSERT INTO T_BREED_CARE (SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES) VALUES (
  'CAT', 'Persa', 3.00, 5.50,
  'Polivalente felina (V3, V4 ou V5): 1a dose entre 6 e 8 semanas, reforços a cada 3 a 4 semanas até 16 semanas e reforço anual. Antirrábica: a partir de 12 semanas, reforço anual.',
  'Raça braquicefálica: lacrimejamento e dificuldade respiratória. Predisposição a doença renal policística: beber e urinar mais que o normal merece exame. Escovação diária do pelo.'
);
INSERT INTO T_BREED_CARE (SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES) VALUES (
  'CAT', 'Maine Coon', 5.50, 11.00,
  'Polivalente felina (V3, V4 ou V5): 1a dose entre 6 e 8 semanas, reforços a cada 3 a 4 semanas até 16 semanas e reforço anual. Antirrábica: a partir de 12 semanas, reforço anual.',
  'Raça de porte grande. Predisposição a cardiomiopatia hipertrófica: cansaço, respiração com a boca aberta ou fraqueza nas patas traseiras são urgentes. Também displasia de quadril.'
);

COMMIT;

SELECT SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT FROM T_BREED_CARE ORDER BY SPECIES, BREED;
