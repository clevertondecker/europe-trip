# Redesign de Planejar — jornada primeiro
Referência: wireframe e critérios fornecidos pelo usuário. Não reproduzir pixel-perfect.
- Título Meu roteiro/status → 3 indicadores → ação contextual → 4 etapas → ferramentas secundárias.
- Fonte única: TripPlan, wishlist UX502, board UX61, canonical commit_undated_destinations e save privado UX75. Nenhum novo schema.
- A montagem separa as etapas com o catálogo itinerary_flow_model, não por país. Confirmação em lote por etapa, até 50 por operação; sem datas obrigatórias.
- A revisão mostra todos os destinos confirmados em ambas etapas, datas e períodos opcionais, pendências e salvamento privado ou backup JSON explícito.
- Sem exigir comparação de bases ou orçamento. Destinos exploration_only não são promovidos; permanecem na lista.
- Preservar Organizar existente, navegação legada, restauração e editor de atrações.
- Gate: AppTest fluxo lista preenchida → lote → revisão → salvar com mock autorizado, sem navegar Explorar; caso privado indisponível, backup; desktop/mobile visual real se disponível; CI inteiro verde. Não mergear sem revisão do HEAD.
