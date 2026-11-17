# Nossa Europa 2027 — DQ 3.2 / cobertura turística e conectividade macro

**Data:** 17/11/2026  
**Escopo:** expansão exploratória baseada em fontes, **não** planejamento de caminhadas ou avaliação de viagens completas.

## Diagnóstico antes da implementação

- **30 cidades-base** no seletor de pesquisa ampliada (`base_city_research_expanded_2026_11.json`).
- **14 destinos / 65 atrações** no catálogo operacional canônico (`attractions_2027.json`).
- **21 destinos** catalogados independentemente no estudo de `exploration_bases_2027.json`, vários não presentes nas 14 fichas com atrações.
- Os conjuntos ferroviários têm referências históricas de alguns pares de cidades. Ausência de um par **não** significa que não exista trem ou que não se possa visitar a cidade.
- DQ 3.1 já permite comparar a mesma cesta de destinos. Exigir caminhadas completas no DQ 3.2 criaria um bloqueio desnecessário à descoberta.

## Nova entrega

1. `data/dq32_macro_tourism_2026_11.json` — **30 registros de atrações locais pesquisadas em 23 cidades**, com nome, categoria, cidade canônica, data e URL da página oficial de turismo/município. Preços, durações, ingressos, acessos e datas de 2027 ficam **null**.
2. `dq32_macro_opportunities_model.py` — combina, sem editar os originais, as 30 cidades-base, o catálogo de 14 destinos, a descoberta histórica de 21 destinos e as novas atrações locais. Usa o adaptador ferroviário existente para **tempos mínimos históricos de ida, com fonte**, e o estudo exploratório como complemento. Reconcilia aliases como `luxembourg`/`luxembourg_city`.
3. `attractions_ui.py` — nova seção **Descoberta ampliada · DQ 3.2** para qualquer cidade-base. Três modos de consulta: atrações da própria cidade, destinos com evidência ferroviária histórica e destinos ainda sem duração pesquisada. Os blocos originais de passeios permanecem no lugar.
4. `base_weight_coverage_ui.py` — tabela adicional em **Explorar → Comparar → Pesos das 30 cidades** apresentando atrações locais identificadas e números de destinos com/sem tempo ferroviário observado, sem transformar quantidade de pesquisa em nota de qualidade.
5. `tests/test_dq32_macro_opportunities.py` — integridade de fontes, cobertura das 30 bases, read-only, aliases, distinção de tempo mínimo, custos ausentes, AppTest de navegação e comparação.

## Antes/depois — métricas de dados e apresentação

| Métrica | Antes | DQ 3.2 |
|---|---|---|
| Cidades-base consultáveis | 30 | 30 |
| Destinos operacionais com atrações, preservados | 14 | 14 |
| Atrações canônicas inalteradas | 65 | 65 |
| Complemento de atrações locais verificadas | 0 nesta camada | 30 em 23 cidades |
| Universo de destinos do estudo exploratório | 21 (separado) | Integrado à leitura com catálogo e cidades-base; deduplicado |
| Caminhadas exigidas para inclusão | Não era requisito técnico | **Não é requisito** |
| Viabilidade de bate-volta inferida | Não | Não |
| Nota artificial por quantidade de pontos turísticos | Não | Não |

**Importante:** os 30 registros ampliam a descoberta, não substituem as 65 atrações canônicas; uma localidade pode ter outras atrações ainda não pesquisadas. As 7 cidades-base sem novos POIs documentados nesta onda **não são excluídas** e permanecem selecionáveis na análise macro. Não se alega que os 30 centros sejam todos turísticos nem que 30x30 conexões estejam pesquisadas.

## Evidências de turismo utilizadas

Todas as 30 linhas incluem uma página de origem individual, com exemplos:

- Lille — Ville de Lille e Lille Tourism (Grand'Place / Palais des Beaux-Arts).
- Dijon — Dijon Métropole (Palais des Ducs / Parcours de la Chouette).
- Trier — Trier Tourism (Porta Nigra / Catedral).
- Aachen — Aachen Tourist Service (Catedral / Elisenbrunnen).
- Liège — Maison du Tourisme du Pays de Liège (Montagne de Bueren / Coteaux).
- Offenburg — Stadt Offenburg (Museum im Ritterhaus).
- Karlsruhe — Karlsruhe Interaktiv (Schloss / ZKM).
- Reims — Ville de Reims (Catedral); Arras — Explore Arras (Grand'Place / Belfroi).
- Besançon — Office de Tourisme (Citadelle); Sélestat — Mairie (Bibliothèque Humaniste).
- Saverne — Visit Alsace (Château des Rohan); Haguenau — Visit Alsace (Floresta).
- Namur — Visit Namur (Citadelle); Luxembourg City / Esch — Visit Luxembourg (Casemates / Belval).
- Saint-Louis — Visit Alsace (Petite Camargue); Belfort — Belfort Tourisme (Citadelle / Lion).
- Thionville — Pays Thionvillois (Beffroi); Baden-Baden — Baden-Baden Tourism (Lichtentaler Allee).
- Saarbrücken — Saarbrücken Tourismus (Ludwigskirche); Lörrach — Stadt Lörrach (Burg Rötteln); Kehl — Stadt Kehl (Jardin des Deux Rives).

URLs e data de pesquisa ficam junto de cada registro; não reutilizar apenas uma URL genérica para inventar atrações ou horários.

## Três dimensões distintas, sem falso ranking

- **Inventário local**: atrações descritas e rastreáveis na própria base. Não comprova acesso da moradia nem horário de abertura.
- **Conectividade histórica**: menor tempo de trem publicado entre duas estações, com referência e data, quando existente. Não comprova retorno nem tempo típico se este não for fornecido na mesma fonte.
- **Universo de pesquisa**: outros destinos que já aparecem nos estudos, mas ainda não têm rota registrada desde aquela base. Não contar como inacessíveis, nem como bate-volta possível.

Nunca calcular `reachable_destinations` a partir da união de nomes. O valor de `feasible_destinations_count` e custos totais permanecem `null`, e `comparison_score` também.

## Próximos pacotes recomendados

**DQ 3.3 — pesquisa macro de transporte por corredores:**
- Priorizar os pares origem/destino mais úteis para diferenças entre bases, não um produto cartesiano 30×todos.
- Pesquisar ferrovias regionais, conexões e tempos típicos em amostras de sábado e domingo.
- Ampliar atração local para as 14 bases restantes, com páginas oficiais, sobretudo quando estiverem na shortlist.
- Explicitar quais ofertas são excursionáveis (somente após evidência de ida e retorno).

**DQ 3.4 — detalhamento de finalistas:**
- Entradas, caminhadas entre atrações, última milha, retorno tardio e custos específicos para os destinos que se tornarem prioritários.

## Limites de segurança da pesquisa

Não altera: `TripPlan`, reservas, `app.py`, orçamento oficial, `attractions_2027.json`, adaptador ferroviário, CSS, dados históricos ou decisões de cidade-base. Não adiciona motor de roteamento pedestre, Haversine, tarifas ou tempos de retorno fabricados. Toda a nova pesquisa fica numa camada consultiva versionada.

Testes obrigatórios: `python -m unittest discover -s tests`, incluindo `AppTest`; conferir CI antes do merge. Não fazer merge/deploy sem autorização.


## Pós-revisão — identidade, métricas e fontes

A identidade das atrações é resolvida por `reconcile_attractions()`: o conjunto canônico mantém seus IDs; títulos idênticos normalizados dentro da mesma cidade convergem automaticamente e sinônimos sem coincidência literal requerem `canonical_attraction_id` explícito na evidência DQ3.2. Uma equivalência de outra cidade, ambígua ou contraditória gera erro. O registro `dq32_luxembourg_city_22` (Casemates do Bock) referencia `lux_bock` (Casamatas do Bock), preservando a URL e o ID original como evidência alternativa, sem dobrar a contagem da atração.

A resposta retorna `canonical_local_attractions`, `new_local_attractions`, `known_local_attractions` (soma deduplicada), `reconciled_duplicate_count` e `semantic_equivalences`. O total de 30 é **número de registros de pesquisa**, não número garantido de 30 atrações novas e únicas. A interface mostra canônicas e novas em colunas distintas.

### Precedência ferroviária pré-ARCH 1.0

A seleção primeiro consulta `rail_evidence_unified_model.route_evidence()` sobre os registros históricos, cuja prioridade de apresentação é `five_base_operator_2026` → `expanded_rail_sample_2026` → `four_base_routes_2026` → `dq30_dated_operator_2026` → `dq30_operator_overview_2026`. Quando não há tempo publicado, a camada DQ3.2 usa `exploration_bases_2027` com data/fonte, sem completar retorno ou custo. `outing_base_coverage_model` e `dq31_logistics_evaluation_model` repetem parte desse fallback. Sua centralização é tratada **no ARCH 1.0, PR separado**, e não nesta correção de identidade.
