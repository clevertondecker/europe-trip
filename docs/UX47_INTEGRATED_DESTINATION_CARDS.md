# UX 4.7 — Cartão único por destino

## Objetivo visual
Aplicar o exemplo de referência: foto integrada ao lado esquerdo, nome/país, período, atrações, status ferroviário e custo total não confirmado à direita; editor **existente abaixo das duas colunas, em largura total** no mesmo cartão. Um destino produz somente um cartão na etapa França. Colunas nativas do Streamlit empilham no celular; o bloco fotográfico usa proporção 4:5, largura máxima de 310px e altura máxima de 365px, sem CSS global.

## Escopo
- `ux47_destination_card_model.destination_card_view(plan,catalog,routes,row)`: adaptador puro e de leitura. Usa o catálogo oficial, `outing_guide_model.build_outing_guide` e `selected_rows`; não altera `TripPlan`, orçamento ou componentes de domínio.
- `itinerary_flow_ui._render_integrated_destination`: cartão com foto e fatos em duas colunas; o `_edit_destination` original fica **fora das colunas**, depois de divisor, ocupando a largura total. Etapa Itália preservada.
- `ux47_photo_ui.photo_markup/photo_credit`: imagem renderizada como camada CSS de fundo com enquadramento `cover`, sobre placeholder neutro. Se a URL falhar no navegador, não há ícone de foto quebrada e o placeholder aparece; sem conexão HTTP por rerun e sem dependência nova. Somente URLs HTTPS Wikimedia são aceitas e os créditos/licenças originais são linkados. **O sucesso do carregamento remoto não é detectado no Python:** o texto do crédito qualifica como *foto cadastrada*.
- Conferidas as páginas oficiais Wikimedia de Basel, Metz e Colmar em 16/11/2026. Fonte de Metz e autoria/licença CC BY-SA 4.0 existem no Commons; isso não garante que o redirecionamento de imagem sempre carregará em cada navegador.
- Retira da tela o segundo bloco `render_chosen_places_cards` após a lista. A função histórica permanece no módulo de dashboard para compatibilidade, mas não cria uma nova renderização no planejamento.
- Custos conhecidos são descritos como **parciais**; total 2027 e viagem de volta não são comprovados. Nenhum preço nulo passa a zero.
- `tests/test_ux47_integrated_cards.py` verifica modelo, Basel/Metz/Colmar juntos, alterações canônicas independentes, remoção individual, fallback de imagem ausente/URL não confiável, créditos, custos desconhecidos, ausência da galeria duplicada e AppTest de editores distintos. Atualizados dois testes que esperavam o título antigo.

## Fora de escopo
Não altera CSS global, tipografia, tokens, mapas, catálogo, perfis, Itália, aprovação financeira, mecanismo de salvamento, backups ou a navegação principal. Não cria abas adicionais nem segunda fonte de verdade.

## Verificação
CI: compilação e suíte completa `unittest discover` com AppTest do editor e testes do fallback. AppTest **não** tira screenshots nem carrega as fotografias remotamente. Navegador real 375, 768 e 1280 px continua pendente; testar foto em portrait/landscape, expansão do editor e falha de rede. Não declarar validação responsiva visual concluída apenas por testes estruturais.
