# UX 4.3 — Adaptador conservador de evidências ferroviárias

## Fontes verificadas
- `data/five_base_comparison_evidence_2026_11.json`: 27 trechos pesquisados entre cinco bases e os destinos da cesta.
- `data/base_city_rail_evidence_expanded_2026_11.json`: 11 trechos com amostras de horários; tempos mínimos e médias de um dia.
- `data/base_destination_routes_2027.json`: 44 combinações legadas, muitas ainda sem horários conhecidos e com tarifas condicionadas.

Nenhum arquivo original foi reescrito. `rail_evidence_unified_model.py` normaliza identificadores, metadados e proveniência em memória. Registros duplicados permanecem acessíveis na lista `observations` e não se escolhe o menor tempo entre fontes.

## Contrato
- `canonical_place(id)`: aliases explícitos, sem equivalência aproximada.
- `load_rail_evidence()`: carrega observações com nomes canônicos e índice de pares.
- `route_evidence(data, origem, destino)`: devolve observações, tempo mínimo histórico, tempo médio da amostra quando documentado, modalidade, fonte, tarifa "desde" e `status` (`local`, `not_researched`, `partial`, `historical_time`). `comparable` e `return_2027_verified` permanecem falsos na ausência de evidência completa.

O comparador da UX 4.1 usa a mesma cesta para todas as favoritas e agora recupera fontes existentes fora do dataset original. **Freiburg continua com rota desconhecida na cesta quando não existe evidência de origem Freiburg** — isso é uma lacuna real do dataset, não uma falha de carregamento. Rotas como Karlsruhe–Strasbourg comprovam que a camada ampliada é consultada.

## Restrições
- Nenhum horário de ida prova retorno de fim de semana.
- Tarifa promocional não representa custo médio, total ou em 2027.
- Observações de períodos e modalidades diferentes não geram ranking.
- A seleção é exploratória; plano oficial, persistência e orçamento ficam inalterados.
- Desktop/mobile precisam de inspeção visual real; AppTest não equivale a teste visual.

## Próxima etapa
UX 4.4 implementada em PR separado, sem modificar esses arquivos da UX 4.3.
