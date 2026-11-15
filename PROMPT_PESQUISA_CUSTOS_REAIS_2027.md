# Prompt executado — pesquisar preços reais e melhorar estimativas por passeio

## Contexto
Projeto Streamlit `clevertondecker/europe-trip`, viagem de duas pessoas após
04/09/2027, França e Itália, com cidade-base francesa variável: Mulhouse,
Strasbourg, Metz ou Nancy. O `TripPlan` continua sendo a única fonte de
verdade dos passeios escolhidos; os cenários são sugestões.

## Pesquisa e auditoria (obrigatórios)
1. Auditar `advisor_finance`, `package_cost`, `outing_cost_evidence`,
   `outing_guide_model`, a matriz das 44 rotas e o orçamento da França.
2. Identificar descontos ferroviários condicionais, refeições incluídas
   na verba existente, itens sem cotação e inconsistências de fonte.
3. Pesquisar em 15/11/2026 fontes oficiais de trens SNCF TER, tarifas
   Fluo, ônibus e transportes urbanos Soléa, CTS e TNW.
4. Pesquisar **cardápios de restaurantes reais** por cidade, armazenando
   preço por pessoa, moeda, item incluído, oferta semanal, data e URL.
5. Priorizar Mulhouse, Strasbourg, Colmar e Basel; manter Metz, Nancy e
   destinos sem dados como **pendentes**, jamais preço zero.
6. Ler relatos atuais de viajantes para destacar riscos, mas **não usá-los**
   como preços absolutos, amostras representativas nem cotações.
7. Persistir dados pesquisados em JSON, análises em Markdown, links e
   datas explícitos. Preservar versões históricas existentes.
8. Validar a Carte Fluo: €30/ano, benefício do titular, condição do
   acompanhante no fim de semana; não somar cartão várias vezes
   e não assumir desconto para dia útil.
9. Quando a tarifa normal não for publicada, não obtê-la
   automaticamente multiplicando a promocional. Separar os dois campos.
10. Declarar "ainda não cotado" quando faltar transporte, refeição ou
    última conexão. Não alegar retorno confirmado para 2027.

## Modelagem e produto
11. Criar `research_cost_model.py`, com validação dos registros,
    preços de almoço observados, custos de transporte documentados,
    alternativas condicionais e subtotais parciais.
12. Câmbio usado é o da tela, sempre identificado como hipótese.
    Distinguir moeda CHF de EUR; jamais somar sem conversão.
13. Criar `research_cost_ui.py`: mostrar menus observados e suas
    fontes, comparação com/sem cartão, custos urbanos opcionais,
    subtotais de casal e reservas gerenciais opcionais (não estatísticas).
14. Integrar a todos os miniguias já usados em Meus passeios, Descobrir,
    Orçamento e Simular roteiros; exibir comparação da cobertura
    por estilo sem sugerir que incompletude é economia.
15. O orçamento existente já inclui rubricas para alimentação e
    excursões. **Não duplicar valores automaticamente** na projeção.
    Apresentar pesquisa como simulação separada até ser possível
    identificar a refeição cotidiana substituída e outros componentes
    incrementais efetivos.
16. Permitir mudança de cidade-base e recalcular origem, tempo ferroviário
    e opções de preço com a matriz apropriada.
17. Testar Colmar saindo de Mulhouse (18 minutos, €5,40 com Fluo,
    €10,80 regular documentado), Strasbourg (32 minutos, €7,90 com Fluo,
    preço regular ainda desconhecido), Basel sem tarifa regular
    e Metz/Nancy sem trajetos verificados.
18. Validar que interações e comparações não alterem `TripPlan`,
    não escrevam em GitHub/Drive e não criem reservas.
19. Criar PR e executar GitHub Actions antes de qualquer merge.
20. Relatar limitações, amostragem, dados ausentes, itens que dependem
    de condições tarifárias e oportunidades de pesquisa futura.

## Critérios de aceite e limites
- A UI mostra custos e fontes pesquisados, com tipo, data, moeda,
  unidade e possibilidade de verificar o cardápio original.
- Para Colmar/Mulhouse, um exemplo parcial sem Carte Fluo compara
  trem regular documentado com **um único almoço observado** para duas
  pessoas; não é total final da viagem.
- Para bases sem tarifa normal, o subtotal não pode parecer completo
  nem considerar trem gratuito.
- Os três perfis mostram custos de refeições pesquisados apenas onde
  existem evidências, com número de passeios sem total.
- Despesas extras, compra de cartão e reserva de imprevistos permanecem
  destacadas como hipóteses e **não se tornam cotações para 2027**.
- A execução é **primeira fase priorizada**: não afirmar ter coletado
  todas as 44 rotas, toda a comida da temporada ou média da Europa.
