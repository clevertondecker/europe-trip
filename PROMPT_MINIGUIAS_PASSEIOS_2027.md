# Prompt executado — Miniguia dinâmico para cada passeio

## Contexto
Aplicativo Streamlit Nossa Europa 2027, repositório `clevertondecker/europe-trip`.
O casamento será em 04/09/2027; os roteiros França/Itália posteriores ainda são
planejamento, não reservas. O `TripPlan` versionado representa somente escolhas
explicitamente confirmadas; os cenários são sugestões independentes.

## Problema
Cada card mostrava só fotografia, destino, duas atrações e subtotal histórico.
Sem detalhar duração, visita, origem, meios de transporte, dependência da
cidade-base, condições de tarifa, riscos de retorno, gastos pendentes e fontes.
A mesma viagem poderia parecer ter custo zero quando faltavam dados.

## Objetivo
Transformar cada passeio escolhido, sugerido ou incluído em simulação em um
miniguia acionável baseado **unicamente** nos dados verificados da matriz de
rotas e no catálogo de atrações, com transparência de incertezas.

## Requisitos de arquitetura
1. Criar um modelo puro `build_outing_guide(plan,catalog,routes,dest,ids)`
   que use `route_for`, `package_cost` e `approximate_feasibility`.
2. Recalcular para cada origem `plan['base_city']` a tarifa publicada,
   distância documentada, tempo de trem e custo de ida e volta por casal,
   sem atualizar manualmente a tarifa em cada aba.
3. Separar trem estação-a-estação de tempo porta-a-porta. Nunca inventar
   conexões, estações precisas, horários, retorno, caminhada, distância
   rodoviária ou ferroviária sem evidência; exibir pendências.
4. Na falta de distância de rota, permitir apenas distância em linha reta
   derivada de coordenadas catalogadas, devidamente rotulada.
5. Mostrar pontos escolhidos, resumo, tempo sugerido de visita (hipótese
   editorial), preço de ingresso se documentado, fontes e observações.
6. Listar até 3 atrações opcionais cadastradas na mesma cidade. Botão
   explícito `Adicionar` modifica somente `Meus passeios` oficial;
   não afetar roteiros oficiais quando o usuário apenas visualiza sugestões.
7. Mostrar subtotal separado por transportes e ingressos, EUR e CHF,
   além de pendências de alimentação, transporte local, transporte de retorno,
   entradas, deslocamento estação-atrações e eventual hospedagem.
8. Oferecer simulador opcional de alimentação/transporte urbano e extras
   com **valores digitados pelo usuário**, isolado da projeção oficial;
   nenhuma suposição é tratada como cotação.
9. Mapa sob demanda com marcadores apenas das cidades de origem e destino;
   não desenhar rota ferroviária, caminhada entre atrações ou trajetos
   inexistentes no catálogo.
10. Reutilizar o componente em `Meus passeios`, pré-selecionados do perfil,
    `Descobrir`, `Simular roteiros` e `Orçamento`; mostrar resumos
    coerentes na `Visão geral` e alertas de logística no `Calendário`.
11. Atualizar somente os custos reais documentados no motor oficial,
    sem duplicar a verba de excursões. Mudar base, passeios ou câmbio atualiza
    todos os cálculos na sessão, sem escrever arquivos remotos.
12. Garantir interface progressiva: cards legíveis, imagem compacta,
    detalhes expansíveis e carregamento do mapa apenas se solicitado.
13. Testar tempos/tarifas para Mulhouse e Strasbourg rumo a Colmar;
    para Metz, tempo/tarifa desconhecidos; cenário financeiro sem mutação;
    mudança de base no UI, atualização das atrações e navegação.
14. Criar PR, validar GitHub Actions e integrar somente com CI verde.

## Limitações comunicadas
A matriz de rotas e as fontes do catálogo são pesquisas de 2026. Não há
consulta ao vivo a trens, tarifas 2027, retorno noturno nem horário confirmado.
Tempo de visita é editorial, não programação definitiva, e a ordem listada
não é um percurso a pé otimizado. A distância em linha reta não representa
distância de estrada ou ferrovia.
