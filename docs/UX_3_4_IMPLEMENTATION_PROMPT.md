# Prompt de execução — Nossa Europa 2027 · UX 3.4

Você é o integrador responsável pelo repositório `clevertondecker/europe-trip`. Execute a implementação da **UX 3.4 — Comparar cidades-base para tomar decisões reais**, após o PR #38 (evidências documentais das 30 cidades) estar integrado à `main`.

## Objetivo do produto

Transformar **Explorar → Comparar → Impacto da troca** em uma ferramenta de decisão que compare a cidade-base oficial com **uma ou duas cidades hipotéticas** usando **os mesmos passeios, casal, duração, cenário de orçamento, câmbio e critérios de pesquisa**.

A ferramenta deve responder:
1. O que muda no tempo de deslocamento para os passeios **que já quero fazer**?
2. Quais destinos ficam potencialmente mais rápidos, lentos ou semelhantes?
3. Onde falta pesquisar trajetos, frequência, última milha, retorno e eventual pernoite?
4. Qual a **diferença financeira estritamente calculável**, separando moradia hipotética, tarifas de ida históricas, despesas orçadas e despesas efetivamente conhecidas?
5. O que mantém o meu plano inalterado?
6. Posso salvar uma comparação para retomar posteriormente sem alterar decisões oficiais?

## Regras não negociáveis

- Ler `AGENTS_COORDINATION.md`, a `main`, PR #38, a estrutura real do Streamlit e as decisões do Drive Living Europe.
- Preservar `TripPlan` canônico, `planning_session`, autenticidade/autorização, decisões oficiais do Drive, roteiros italianos e saldos do orçamento.
- **Comparar não é aplicar**: nunca modificar a base oficial durante seleções ou cálculo. Só permitir aplicação de `mulhouse`, `strasbourg`, `metz`, `nancy` após revisão de uma mudança e confirmação explícita com revisão de versão. As outras cidades permanecem exploratórias.
- Nem ausência de preço ou rota é igual a zero. Uma rota não pesquisada **não** significa destino perdido, inviável ou que exige pernoite.
- Não inferir tarifa regular ida/volta a partir de tarifa `desde` por pessoa/trecho. Não dobrar duração e anunciar viagem garantida. Não inventar cotações, imóveis, internet, horários ou passagens de 2027.
- Se fornecer previsão financeira de moradia, ela será estritamente **hipotética**, com dois aluguéis mensais informados pelo usuário, mesma duração e câmbio, usando `comparable_rent_whatif` e `scenario_total`; mostrar a **diferença de moradia** e, se aplicável, projeções condicionais existentes, jamais “economia total confirmada”.
- Não somar bilhetes por atração de um mesmo destino nem adicionar por cima do orçamento já reservado para passeios. Custos de retorno, ingressos e hospedagem não pesquisados permanecem pendentes.
- Não duplicar controles de cidade, duração e orçamento entre o consultor e o roteiro.

## UX esperada

Na atividade **Explorar → Comparar**, a seção principal deve ter:
1. **Meu plano** — referência visual com a base oficial atual, duração e cenário financeiro.
2. **Comparar uma ou duas alternativas** — seleção de cidades, sem exigir novo cadastro.
3. **Manter os mesmos passeios** — preferência pelos destinos já escolhidos no `TripPlan.packages`; se não houver, oferecer destinos de exemplo claramente rotulados.
4. **Comparação em condições iguais** — grade enxuta de bases e cobertura, com tabela de tempos históricos (ida) e links individuais das fontes.
5. **O que melhora/piora?** — contagens apenas para pares de tempos conhecidos; limiar de referência, desconhecidos explicitamente.
6. **Orçamento** — custos isolados e comparáveis; campos hipotéticos recolhidos; sem total falso.
7. **Guardar/recuperar estudo** — memória de sessão + JSON portátil validado. O GitHub público não é repositório de dados privados.
8. **Aplicar ao meu plano** — somente quatro bases oficiais; revisão e confirmação separadas, com segurança contra estado obsoleto.

Manter `Pesos das 30 cidades`, `Comparar mesmas viagens`, `Uma ou duas bases` e `Estudo histórico` acessíveis como recursos secundários, sem criar abas principais novas.

## Contratos e arquivos sugeridos

- `city_decision_model.py`: `compare_city_decisions(plan,alternatives,destinations,rents,trip_data,finance_live,french_days,eur_fx)->dict`, `review_base_application(plan,comparison,candidate)->dict`.
- `city_decision_store.py`: `make_city_draft`, `validate_city_draft`, `export_city_draft`, `import_city_draft`; limitadores de tamanho, schema e valores.
- `city_decision_ui.py`: `render_city_decision(plan,trip_data,finance_live,french_days)`.
- Ajustes mínimos em `base_change_model.py` (resolução de rotas com fonte), `app.py` (roteamento) e `planning_context_ui.py` (CTA).
- `tests/test_ux34_city_decision.py`, testes existentes e suíte total.

Reutilizar `base_options`, `destination_catalog`, `planned_destinations`, `destination_impact`, `impact_summary`, `comparable_rent_whatif`, `base_coverage_model`, `data_model`, `unified_budget` e os dados documentais do GitHub. Não criar um novo motor financeiro nem migrar os dados antigos para critérios incompatíveis.

## Aceite e verificação

- Comparar oficialmente uma base atual com duas candidatas, sem mudar qualquer campo do plano.
- Quando há 1 destino com rota em ambas bases e 1 sem pesquisa, mostrar **1 comparável e 1 desconhecido**; nunca declarar o segundo perdido.
- Com dois aluguéis simulados, mostrar apenas o delta dessas provisões; quando falta um, exibir “não calculável”.
- Comparar sobre o mesmo conjunto de destinos/dias/moeda; mostrar cobertura assimétrica sem ranking falso.
- Salvar e recuperar JSON de estudo sem misturar com `TripPlan`, alteração remota ou decisão oficial.
- Base fora das quatro suportadas não pode ser aplicada.
- Mudança oficial requer botão de revisão, confirmação, versão ainda válida e `planning_session.update_fields` com somente `base_city`.
- CI completo e `streamlit.testing.v1.AppTest` sem regressões nas páginas de Itália, orçamento e roteiro.
- Anotar CI, limitações e validação visual no PR.
- **Não declarar o aplicativo publicado** até verificar merge e deploy. Não mascarar falta de cotação como preço de 2027.
