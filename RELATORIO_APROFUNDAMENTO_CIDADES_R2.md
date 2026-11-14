# Segunda rodada de pesquisa: lacunas por cidade — 14/11/2026

## Escopo
Casal de duas pessoas, cerca de 55–65 noites em uma base francesa após a etapa italiana, entre setembro e novembro de 2027, sem carro, trabalhando remotamente. Fontes consultadas em novembro/2026; não há cotações contratuais completas para as datas de 2027.

## Achado 1 — Outra fonte comparável de aluguel, com MÉTODO DIFERENTE
MeilleursAgents apresenta estimativas de aluguel mensal de apartamentos residenciais convencionais em €/m² em 01/11/2026, fonte: https://www.meilleursagents.com/prix-immobilier/grand-est/

| Cidade | Aluguel residencial estimado €/m²/mês |
|---|---:|
| Mulhouse | 13,70 |
| Strasbourg | 15,60 |
| Metz | 14,20 |
| Nancy | 14,20 |

**Limite crítico:** o índice não é cotação de aluguel mobiliado, de plataforma, nem da temporada de 55–65 noites. Não multiplicar área por €/m² e chamar de aluguel real do casal. Usar apenas como contexto independente para avaliar posicionamento relativo de mercado.

## Achado 2 — Preço comparável de alimentação fora de casa
Numbeo, tabela colaborativa de preços por cidade, consultada em 14/11/2026. Item idêntico: refeição de três pratos em restaurante intermediário para duas pessoas, sem bebidas.

| Cidade | €/refeição para duas pessoas | Fonte |
|---|---:|---|
| Mulhouse | 67,50 | https://fr.numbeo.com/co%C3%BBt-de-la-vie/ville/Mulhouse |
| Strasbourg | 62,50 | https://fr.numbeo.com/co%C3%BBt-de-la-vie/ville/Strasbourg |
| Metz | 60,00 | https://fr.numbeo.com/co%C3%BBt-de-la-vie/ville/Metz-France |
| Nancy | 60,00 | https://fr.numbeo.com/co%C3%BBt-de-la-vie/ville/Nancy |

Dados colaborativos de cobertura irregular, particularmente em Metz, onde diversos itens de supermercado não têm observações. Não inferir que Mulhouse é sistematicamente mais cara ou que esses preços podem ser convertidos em custo exato de 8 semanas. A cesta histórica de €137,06/semana do Drive continua um parâmetro compartilhado, ainda sem levantamento de carrinho idêntico por supermercado/bairro.

## Achado 3 — Trabalho remoto: alternativa de coworking
| Cidade | Espaço pesquisado | Preço publicado e condições | Fonte |
|---|---|---|---|
| Mulhouse | La Jonction / Mulhouse Coworking | €15 HT/dia extra no plano a partir de €30 HT/mês; alguns formatos têm acesso até 22h30 durante a semana. Precisa verificar elegibilidade do plano e acesso real até fim do expediente | https://www.mulhouse-coworking.fr/ |
| Strasbourg | DOKO BÜRO | €175/mês na modalidade mensal publicada no diretório regional; funcionamento em geral até 19h. Não cobre expediente BR até tarde | https://label-tiers-lieux.grandest.fr/tiers-lieux/doko-buro/ |
| Metz | B'CoWorker (diretório secundário) | €15/dia ou €190/mês publicados no comparador; confirmar junto à empresa e horário | https://comparatifcoworking.com/coworking/metz/ |
| Nancy | Charlie Coworking | €90/mês flex sem lugar garantido; também menciona anuidade associativa de €75 e acesso 24h para titulares de chave. Confirmar se plano flex permite o horário e uso por dois meses | https://www.coworking-nancy.org/ |

**NÃO concluir que um coworking substitui o apartamento para trabalho remoto.** Na França, enquanto vigora o horário de verão, o expediente do Brasil poderá alcançar aproximadamente 23h; após a mudança do relógio no fim de outubro, até aproximadamente 22h, dependendo do horário efetivo. Verificar privacidade, espaço para videochamadas, cadeira, internet e horários antes de pagar.

## Achado 4 — Lei do contrato de curta duração
Fonte governamental: https://www.service-public.gouv.fr/particuliers/vosdroits/F1165 e https://www.service-public.gouv.fr/particuliers/vosdroits/F34759. O bail mobilité clássico tem duração de 1–10 meses e perfil de locatário elegível; o depósito de garantia é vedado nessa modalidade. Não presumir que empregado brasileiro em home office preencha o requisito. Uma cláusula de caução divulgada em anúncios pode ser pista de **outra modalidade contratual** ou de anúncio inconsistente; não concluir violação sem apurar o contrato.

## Status da auditoria após esta rodada
| Gate | Avanço | Continua bloqueado por |
|---|---|---|
| Moradia | Índice residencial por m² e anúncios históricos separados | Falta custo integral e 3 ofertas independentes elegíveis para 2027 |
| Custo de vida | Preço do MESMO tipo de refeição para todas as cidades | Falta carrinho e restaurantes reais por bairro, consumo semanal comparável |
| Trabalho remoto / vida diária | Um coworking pesquisado por cidade | Falta validar horas até 22–23h, internet no imóvel, mesa/ergonomia, bairro |
| Elegibilidade | Portal oficial sobre contratos | Falta verificar enquadramento do casal e autorização do empregador |
| Transporte interurbano | Linhas e alguns preços históricos do TER na fase anterior | Falta 5 roteiros reais por cidade, preço total do casal e retorno aos domingos |
| Aéreo / deslocamentos | Lista de aeroportos de interesse já existe no projeto | Falta custo Itália → base → Brasil, datas, bagagens e percurso porta a porta |

**Nenhum gate completo novo é marcado nesta rodada.** Essa decisão evita fazer parecer que obter uma referência pública de aluguel ou de coworking já resolve a adequação contratual da estadia.

## Como foi integrado
- Prompt: `PROMPT_APROFUNDAMENTO_CIDADES_R2.md`
- Evidência versionada: `data/city_research_round2_2026.json`
- Validador: `city_research_round2.py` e `tests/test_city_research_round2.py`
- Streamlit: aba **Comparar cidades → Transporte e custos**, abaixo dos dados já existentes, com tabelas compactas e links diretos.
- Nenhuma planilha do Drive, decisão D-004, credencial, nota editorial histórica ou orçamento global foi alterado.

## Prioridades da próxima coleta
1. Obter datas-alvo reais de entrada e saída após 04/09/2027 e a Itália; executar busca de imóveis para o mesmo período, enviar mensagens padronizadas a anfitriões, registrar disponibilidade e custo integral sem antecipar reserva.
2. Fazer carrinho-padrão de supermercado em uma loja do mesmo tipo por cidade, com produto, peso e unidade; observar alternativas e disponibilidade.
3. Comparar 3 restaurantes, 2 academias e 2 bairros por cidade, sem inventar nota.
4. Criar 5 passeios desejados por cidade, tempos porta a porta e retorno domingo.
5. Confirmar formalmente trabalho remoto internacional e modalidade legal de hospedagem.
