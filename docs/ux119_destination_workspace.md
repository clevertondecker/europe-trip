# UX119 — Roteiro de navegação e responsabilidades

- Planejar → Meus destinos: cards de visitas existentes, indicadores da projeção compartilhada, filtro e paginação. Editar passeio abre o editor canônico de atrações/período e confirmação de remoção. Organizar encaminha o ID e a etapa ao organizador existente.
- Incluir destinos: elegibilidade da wishlist existente, seleção visual e multiselect refletem a mesma lista temporária; confirmação via commit_undated_destinations. Nenhuma inclusão automática, alteração de base ou reserva.
- Proposta italiana: acesso ao renderer italiano existente; não adota proposta sem confirmação.
- Logística e custos: leitura opcional do adapter UX47; lacunas permanecem explícitas.
- Wishlist e destinos somente pesquisa: continuam em Explorar → Minha lista.
- Salvar e recuperação: renderers privados existentes, sem novo writer. Consolidação de continuidade pertence a UX122.
- Calendário e viagens agrupadas: organizador existente; redesign pertence a UX120.
- Ações e ferramentas legadas ainda acessíveis até inventário de UX122.
- Testes automatizados da fundação e AppTest de edição, cancelamento, encaminhamento e inclusão visual. QA visual real e revisão transversal ainda exigidos antes de concluir o PR.
