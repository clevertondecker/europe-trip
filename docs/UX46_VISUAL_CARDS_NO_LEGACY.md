# UX 4.6 — Cartões visuais no planejamento; painel legado removido

## Decisão de produto
O usuário aprovou o visual das fotos de destinos na seção **Lugares que escolhemos**, mas pediu para retirar o controle **Mostrar painel detalhado e mapas antigos**, que duplicava navegação, mapas, métricas e orçamento e gerava confusão.

## Implementação
- `app.py`: remove o toggle `flow_show_legacy_dashboard` e seu corpo, incluindo a segunda visão completa de dashboard e a linha do tempo/mapas antigos. Não altera outras visualizações de mapas em páginas dedicadas.
- `travel_dashboard_ui.py`: extrai `render_chosen_places_cards(plan,catalog,routes)`, somente leitura, a partir do bloco fotográfico existente. Mantém imagem do catálogo, créditos, licença, nome/local, quantidade de atrações, data, exemplos de atrações, tempo histórico e custo parcial por casal. O `render_trip_dashboard` existente também chama a função extraída (compatibilidade), mas não é mais duplicado na tela principal.
- `itinerary_flow_ui.py`: apresenta esses cartões diretamente após a lista de lugares escolhidos na etapa França de **Meu roteiro → Meu planejamento**, sem toggle e sem mudar seleções ou agenda. Para Itália continua a apresentação específica do editor da lua de mel.

## Preservações e limitações
- Fonte de verdade: `TripPlan.packages` e `TripPlan.assignments`. Não se cria estado paralelo, não se aplica nenhum custo extra ao orçamento, não se adiciona destino fictício.
- Valores de transporte e custo permanecem **referências históricas incompletas**, não ofertas ou reservas para 2027. Fotografias e créditos são os dados do catálogo existente.
- Esse componente apresenta os lugares franceses que já estão em `packages`, como no painel anterior; as escolhas italianas continuam na etapa Itália.
- A versão antiga de `render_trip_dashboard` permanece no módulo para compatibilidade de chamadas externas; a aplicação principal deixa de exibi-la como opção.
- Regra de propriedade: alterações em `app.py` são do integrador; não mexer em CSS, `TripPlan`, orçamento, catálogo, backups, autenticação ou mapas dedicados.

## Verificações
- Compilação completa e suíte de testes via CI.
- Teste de interface em `tests/test_travel_dashboard.py` verifica ausência do toggle e presença dos cartões na etapa França.
- Revisão visual mobile/desktop permanece necessária: AppTest não executa screenshots de navegador.
