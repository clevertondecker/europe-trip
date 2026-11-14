# PROMPT MESTRE — Revisão permanente da pesquisa de cidades-base (Nossa Europa 2027)

Atue como pesquisador de viagens de longa duração, analista de evidências e engenheiro de dados, sem converter hipóteses em fatos.

## Escopo
Casal de dois adultos; casamento 04/09/2027; viagem somente depois do casamento; Itália primeiro, depois França; estadia 55–65 noites na base francesa; trabalho remoto, deslocamentos sem carro, comparação de orçamento global de R$60k e R$70k para a VIAGEM INTEIRA.

## Fontes e precedência
1. Estado/decisões e modelo financeiro no Google Drive do projeto (não modificar sem aprovação explícita).
2. Matriz histórica nas abas 11 RANK CIDADES, 12 PESOS CIDADES, 13 SCORE CIDADES, 14 LOGÍSTICA CIDADES, 15 IMÓVEIS HISTÓRICOS e 16 ALUGUÉIS 2027 do `Europa_2027_COMPLETO_ORGANIZADO.xlsm`.
3. Fontes primárias atuais: operador de transporte, sites oficiais de prefeitura e governo, anúncio individual, condições contratuais e cotação real para datas/ocupantes.
4. Dados colaborativos e sites agregadores apenas como corroboradores com amostra e data. Jamais converter aluguel de contrato anual em oferta de estadia curta.

## Para cada cidade — ficha obrigatória idêntica
- Identidade: cidade, país, bairro candidato, data da pesquisa, autor, estado de revisão e justificativa.
- Moradia: pelo menos 3 apartamentos independentes de 35–65m² preferencialmente, para duas pessoas, mobiliados, cozinha privada, mesa, internet, 55–65 noites. Para cada link registrar URL individual, €/noite ou €/mês, datas, custo total, contas, limpeza, depósito (em campo SEPARADO), plataforma, cancelamento, ocupação, mínimo de duração, elegibilidade legal, contato/retorno e validade. Registros indisponíveis, só para estudantes, pequenos demais ou sem contrato válido devem ser EXCLUÍDOS do conjunto de elegíveis, mas preservados no histórico de recusas.
- Consumo: cesta semanal e alimentação para dois, frequência de restaurante, lazer/bares, transporte local, academia; usar mesma metodologia e a mesma moeda para todas as cidades. Identificar preços observados vs estimativas.
- Transporte: 5 destinos realmente desejados, tempo porta-a-porta, ida e volta de fim de semana, última conexão, preço casal e fonte da operadora com data; custo Itália→base e base→Brasil incluindo bagagem e translados.
- Vida cotidiana: segurança por bairro, supermercado, academia, estação, transporte noturno, mobiliário para home office, estabilidade/velocidade de internet verificada, disponibilidade de serviços na volta do trabalho; não inferir apenas da nota de cidade.
- Perfil legal: modalidade do contrato francês e elegibilidade efetiva; não presumir elegibilidade a `bail mobilité` por ter cidadania UE ou trabalhar remoto.
- Evidência: separar OFICIAL, ANÚNCIO OBSERVADO, COTAÇÃO ESPECÍFICA, REFERÊNCIA HISTÓRICA, ESTIMATIVA, AVALIAÇÃO EDITORIAL e DADO AUSENTE. Para cada fato: data de publicação, acesso, URL, unidade, preço para 2 pessoas, período e ressalvas.
- Ranking: preservar notas históricas 0–5, recalcular pesos somente de forma exploratória; não atribuir novas notas sem rubrica objetiva e fontes. Mostrar cobertura e confiança por cidade.
- Revisão: declarar explicitamente itens faltantes, contradições entre abas, regras de exclusão, sensibilidade cambial e datas de revalidação.

## Qualidade bloqueante — oito gates
Usar os 8 gates versionados em `data/city_research_audit_2026.json`: rental_inventory, rental_total, living_cost, intercity, flights, daily_life, eligibility, evidence. Uma cidade nova sem esses campos não passa na validação automática. `decision_ready` só quando TODOS atendidos e existirem 3 cotações elegíveis para as datas reais; caso contrário status preliminar ou insuficiente.

## Etapas da tarefa
A. Abrir todas as fontes originais; reproduzir planilha e notas exatas (não inferir dados ausentes).
B. Verificar e comparar referências oficiais e anúncios individuais atuais.
C. Atualizar dados estruturados e relatório, preservando histórico e datas; nunca substituir pesquisas antigas silenciosamente.
D. Rodar validações de schema, evidência, unidades, soma financeira, igualdade de método e testes de regressão.
E. Integrar no Streamlit o nível de confiança e a lista de lacunas; separar custo referencial de cotações 2027.
F. Publicar no GitHub, verificar CI e pedir validação visual. NÃO selecionar automaticamente cidade-base.

## Critério de aceite
Quatro cidades com fichas uniformes, fontes e ressalvas; inclusão de uma quinta cidade requer os mesmos dados; rankings históricos preservados sem falsamente elevar confiança. Aluguel e gastos detalhados só podem ser marcados confiáveis com evidências comparáveis.