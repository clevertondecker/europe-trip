# UX 4.7 — Cartão único por destino

## Objetivo visual
Aplicar o exemplo de referência: foto integrada ao lado esquerdo, nome/país, período, atrações, status ferroviário e custo total não confirmado à direita; editor **existente** dentro do mesmo cartão. Um destino produz somente um cartão na etapa França. No Streamlit as colunas nativas são responsivas e empilham no celular; imagem limitada a 260px para não dominar a tela.

## Escopo
- `ux47_destination_card_model.destination_card_view(plan,catalog,routes,row)`: adaptador puro e de leitura. Usa o catálogo oficial, `outing_guide_model.build_outing_guide` e `selected_rows`; não altera `TripPlan`, orçamento ou componentes de domínio.
- `itinerary_flow_ui._render_integrated_destination`: cartão com duas colunas, foto com crédito/licença, fatos e `_edit_destination` no mesmo bloco. Etapa Itália preservada.
- Retira da tela o segundo bloco `render_chosen_places_cards` após a lista. A função histórica permanece no módulo de dashboard para compatibilidade, mas não cria uma nova renderização no planejamento.
- Custos conhecidos são descritos como **parciais**; total 2027 e viagem de volta não são comprovados. Nenhum preço nulo passa a zero.
- `tests/test_ux47_integrated_cards.py` verifica modelo, cards reais, múltiplos destinos e ausência da galeria duplicada; atualizados dois testes que esperavam o título antigo.

## Fora de escopo
Não altera CSS global, tipografia, tokens, mapas, catálogo, perfis, Itália, aprovação financeira, mecanismo de salvamento, backups ou a navegação principal. Não cria abas adicionais nem segunda fonte de verdade.

## Verificação
CI: compilação e suíte completa `unittest discover` com AppTest do editor. AppTest não tira screenshots: ainda é necessário conferir no navegador larguras 375, 768 e 1280 px, especialmente alturas diferentes de fotos Wikimedia e empilhamento mobile.
