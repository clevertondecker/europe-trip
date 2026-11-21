# DATA23 + UX78 — Adaptação dinâmica de cidades-base e novas pesquisas francesas

Revisão de 21/11/2026. Objetivo: estudar Angers, Le Mans, Annecy e Rennes, com fotos Wikimedia Commons de cada atração incluída, tempos históricos de ida e fontes. Plano oficial (Metz), favoritos, roteiro e nuvem privada não devem ser modificados.

## Arquitetura sem contagem fixa de cidades

A antiga base de 30 cidades em `data/base_city_research_expanded_2026_11.json` e as 30 fichas em `data/city_profiles_enriched.json` são **snapshots históricos** e permanecem byte-a-byte intactas. A função `load_research()` agrega o lote DATA23, totalizando 34 cidades. `load_profiles()` agrega 4 fichas mínimas e validadas. Métricas, filtros e rótulos da interface usam o tamanho real da coleção, não valores literais de 30.

O baseline `data/research_snapshot_baseline.json` permanece em 30, pois audita os *arquivos de origem congelados*. Nenhum teste deve mudar esse baseline apenas para ocultar o aumento da visualização.

## Atrações verificadas com fotos e atribuição

| Base | Atração local | Passeio regional |
|---|---|---|
| Angers | Château d'Angers; foto GoginkLobabi CC BY-SA 4.0 ([Commons](https://commons.wikimedia.org/wiki/File:Angers_-_Ch%C3%A2teau_d%27Angers.jpg)) | Château de Saumur; foto Targut CC BY-SA 3.0 ([Commons](https://commons.wikimedia.org/wiki/File:Ch%C3%A2teau_de_Saumur.jpg)) |
| Le Mans | Cathédrale Saint-Julien; foto Chris06 CC BY-SA 4.0 ([Commons](https://commons.wikimedia.org/wiki/File:Cathedrale_de_Le_Mans_(11).jpg)) | Circuit des 24 Heures; foto OldLion CC BY-SA 4.0 ([Commons](https://commons.wikimedia.org/wiki/File:Le_Mans-_Circuit.jpg)) |
| Annecy | Palais de l'Île; foto Châtaigne des Cévennes CC BY-SA 4.0 ([Commons](https://commons.wikimedia.org/wiki/File:Palais_de_l%27Isle_%C3%A0_Annecy.jpg)) | Gorges du Fier; foto Tiia Monto CC BY-SA 3.0 ([Commons](https://commons.wikimedia.org/wiki/File:Gorges_du_Fier.jpg)) |
| Rennes | Parc du Thabor; foto Oldspider CC BY-SA 3.0 ([Commons](https://commons.wikimedia.org/wiki/File:Parc_du_Thabor.jpg)) | Remparts de Saint-Malo; foto Avi1111 CC BY-SA 4.0 ([Commons](https://commons.wikimedia.org/wiki/File:Ramparts_of_Saint-Malo.jpg)) |

Todas as oito atrações têm foto, autor, licença, URL de origem e página turística identificadas. Fotos podem deixar de carregar por indisponibilidade externa; um fallback visual neutro permanece obrigatório. Não substituir por imagens de outro local.

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

O lote não garante que todo passeio nas redondezas esteja catalogado. Próximas investigações: Terra Botanica, Fontevraud, Cité Plantagenêt completa, Abbaye de l'Épau, Talloires, Menthon-Saint-Bernard, Mont-Saint-Michel e Dinan com fotos individualmente licenciadas, retornos e acessos pela última milha. Não anunciar esses passeios como cadastrados até ter os três elementos.
