# DATA23 + UX78 — Adaptação dinâmica de cidades-base e novas pesquisas francesas

Revisão de 21/11/2026. Objetivo: estudar Angers, Le Mans, Annecy e Rennes, com fotos Wikimedia Commons de cada atração incluída, tempos históricos de ida e fontes. Plano oficial (Metz), favoritos, roteiro e nuvem privada não devem ser modificados.

## Arquitetura sem contagem fixa de cidades

A antiga base de 30 cidades em `data/base_city_research_expanded_2026_11.json` e as 30 fichas em `data/city_profiles_enriched.json` são **snapshots históricos** e permanecem byte-a-byte intactas. As funções `load_research()` e `load_profiles()` **sem argumentos** preservam os 30 registros históricos, garantindo a reprodutibilidade das auditorias DATA10–DATA22 e dos relatórios antigos. A interface opta explicitamente por `load_research(include_candidates=True)` e por `load_profiles(canonical=research)`, resultando em 34 candidatas atuais e 34 fichas. As telas modernas de exploração e comparação solicitam o catálogo dinâmico; o relatório histórico não deve misturar os dois denominadores.

O baseline `data/research_snapshot_baseline.json` permanece em 30, pois audita os *arquivos de origem congelados*. Nenhum teste deve mudar esse baseline apenas para ocultar o aumento da visualização. O `base_options` compartilhado oferece `include_candidates=True` apenas para telas exploratórias; as auditorias permanecem limitadas às 30 bases antigas.

## Atrações verificadas com fotos e atribuição

| Base | Atração local | Passeio regional |
|---|---|---|
| Angers | Château d'Angers; foto GoginkLobabi CC BY-SA 4.0 ([Commons](https://commons.wikimedia.org/wiki/File:Angers_-_Ch%C3%A2teau_d%27Angers.jpg)) | Château de Saumur; foto Targut CC BY-SA 3.0 ([Commons](https://commons.wikimedia.org/wiki/File:Ch%C3%A2teau_de_Saumur.jpg)) |
| Le Mans | Cathédrale Saint-Julien; foto Chris06 CC BY-SA 4.0 ([Commons](https://commons.wikimedia.org/wiki/File:Cathedrale_de_Le_Mans_(11).jpg)) | Circuit des 24 Heures; foto OldLion CC BY-SA 4.0 ([Commons](https://commons.wikimedia.org/wiki/File:Le_Mans-_Circuit.jpg)) |
| Annecy | Palais de l'Île; foto Châtaigne des Cévennes CC BY-SA 4.0 ([Commons](https://commons.wikimedia.org/wiki/File:Palais_de_l%27Isle_%C3%A0_Annecy.jpg)) | Gorges du Fier; foto Tiia Monto CC BY-SA 3.0 ([Commons](https://commons.wikimedia.org/wiki/File:Gorges_du_Fier.jpg)) |
| Rennes | Parc du Thabor; foto Oldspider CC BY-SA 3.0 ([Commons](https://commons.wikimedia.org/wiki/File:Parc_du_Thabor.jpg)) | Remparts de Saint-Malo; foto Avi1111 CC BY-SA 4.0 ([Commons](https://commons.wikimedia.org/wiki/File:Ramparts_of_Saint-Malo.jpg)) |

Todas as doze atrações têm foto, autor, licença, URL de origem e página turística identificadas. Fotos podem deixar de carregar por indisponibilidade externa; um fallback visual neutro permanece obrigatório. Não substituir por imagens de outro local.

## Quatro fotografias adicionais (3 atrações por base)

| Base | Terceira atração | Fonte turística | Foto Commons (autor/licença) |
|---|---|---|---|
| Angers | Terra Botanica | https://www.destination-angers.com/tourisme/organiser-son-sejour/activites-a-faire-a-angers/sites-visites-angers/ | [Chabe01, CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Terra_Botanica_2017.08.23_Angers_46.jpg) |
| Le Mans | Abbaye Royale de l'Épau | https://lemans-tourisme.com/fr/abbaye-de-lepau.html | [Benchaum, CC BY-SA 3.0](https://commons.wikimedia.org/wiki/File:Abbatiale_de_l%27%C3%A9pau.JPG) |
| Annecy | Château de Menthon-Saint-Bernard | https://www.ville-annecy.fr/que-faire-autour-d-annecy/ | [Hamster hypertonique, CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Ch%C3%A2teau-Menthon-Saint-Bernard.jpg) |
| Rennes | Rua Jerzual, Dinan | https://www.dinan-capfrehel.com/nos-incontournables/dinan-cite-medievale-bretagne/ | [Zairon, CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Dinan_Rue_du_Jerzual_1.jpg) |

## Logística ferroviária — mínimas de ida e fontes

| Base | Destino | Mínimo | URL |
|---|---|---:|---|
| Angers | Saumur | 20 min | https://www.sncf-connect.com/train/horaires/angers/saumur |
| Angers | Nantes | 37 min | https://www.sncf-connect.com/train/trajet/angers/nantes |
| Angers | Tours | 54 min | https://www.sncf-connect.com/train/trajet/angers/tours |
| Le Mans | Chartres | 58 min | https://www.sncf-connect.com/train/horaires/le-mans/chartres |
| Le Mans | Paris | 56 min (amostra de horários) | https://www.sncf-connect.com/en-en/train/timetables/le-mans/paris |
| Annecy | Aix-les-Bains | 26 min | https://www.sncf-connect.com/train/trajet/annecy/aix-les-bains |
| Annecy | Genève | 88 min | https://www.sncf-connect.com/train/trajet/annecy/geneve |
| Annecy | Chamonix | 120 min | https://www.sncf-connect.com/en-en/train/route/annecy/chamonix |
| Rennes | Saint-Malo | 42 min | https://www.sncf-connect.com/train/trajet/rennes/saint-malo |
| Rennes | Dinan | 56 min | https://www.sncf-connect.com/train/horaires/rennes/dinan |

Esses mínimos refletem exemplos ou páginas disponíveis em 2026, não disponibilidade específica para outono de 2027. Não extrapolar rota inversa, ida e volta, média, tarifa, duração porta a porta ou funcionamento sazonal. Não há preços de aluguel, ingressos ou estimativas finais sem evidência.

## Revisão de impacto obrigatória

- Cidades-base: explorador, filtros, favoritos, página detalhada, indicadores, pontuação incompleta, fichas e cenários exploratórios
- Comparação `UX503`: até 5 bases selecionadas, a mesma lista de desejos, fontes preservadas, tempo apenas no sentido consultado
- Roteiro: cidade-base oficial, atrações escolhidas, preferências, revisões e salvamento GCS permanecem inalterados
- Fotos: `photo_markup` com fallback e `photo_credit` atribuído, links seguros
- Histórico: DATA13, DATA22, baseline de 30, 12 finalistas, 35 anúncios observados e listas antigas continuam inalterados
- Dados faltantes: não substituir `None` por `0`; evitar ranqueamento por ausência de documentação
- Regressão e UI: executar `python tools/validate_research_data.py`, `python -m unittest discover -s tests`, checar Streamlit e testar duas inclusões sucessivas de futuras cidades sem precisar trocar um literal de contagem

## Próximos enriquecimentos

O lote não garante que todo passeio nas redondezas esteja catalogado. Próximas investigações: Fontevraud, Cité Plantagenêt completa, Talloires e Mont-Saint-Michel com fotos individualmente licenciadas, retornos e acessos pela última milha. Não anunciar esses passeios como cadastrados até ter os três elementos.

## Revisão de impactos cruzados (UX78)

- **Explorar cidades-base:** carrega 34 fichas quando solicitada a pesquisa atual, sem alterar o plano; painéis de atrações com 3 fotografias por nova base e referências ferroviárias; contador dinâmico.
- **Explorador de cenários:** `base_options(..., include_candidates=True)`, `_nearby` e `expanded_rail_routes` usam IDs válidos e fontes DATA23. Bases não suportadas pelo `TripPlan` continuam sem permissão de aprovação automática.
- **Comparar cidades-base:** UX503 carrega os quatro candidatos e usa DATA23 apenas como camada subsidiária de referências direcionais, sem ranking de logística quando faltam retornos e última milha.
- **Auditorias de dados, cobertura macro, orçamento e indicadores históricos:** usam `load_research()` e `base_options()` sem inclusão de candidatos, preservando o universo de 30 bases e os 12 finalistas enquanto auditam o snapshot histórico.
- **Meu roteiro, escolhas, GCS e favoritos:** esta mudança não escreve nem migra o documento do usuário. Os quatro candidatos aparecem para estudo, não como base oficial.
- **Foto fallback:** créditos e licença são preservados; serviço Commons tem cache na UI e imagens externas podem exibir fallback neutro se indisponíveis.

Testes de regressão checam os dois universos separadamente (30 histórico / 34 pesquisados) e o fluxo Streamlit de abertura de Angers sem mudança do plano oficial.
