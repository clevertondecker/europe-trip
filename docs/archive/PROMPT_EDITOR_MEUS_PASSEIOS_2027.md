# Prompt executado — simplificar Meus passeios

## Problema
O workspace Roteiro mistura "Destinos da simulação" com passeios realmente aprovados,
dificultando localizar, adicionar, editar e remover escolhas do usuário.

## Objetivo e comportamento
- A aba **Meus passeios** exibe SOMENTE destinos existentes em TripPlan.packages.
- Cada card mostra nome, país, fotografia licenciada, atrações e datas efetivamente atribuídas.
- Botões diretos **Editar** e **Remover**, com confirmação explícita de remoção.
- Exclusão usa planning_session.delete_package, inclusive limpando assignments do destino.
- Adição usa catálogo de destinos real, seleção validada de 1 a 5 atrações e
  planning_session.select_package; exclusões e escolhas de preferência respeitadas.
- Alterações são refletidas na mesma sessão, através de fonte única TripPlan,
  e não são gravadas remotamente sem autenticação e procedimento já existente.
- Estado vazio orienta "Adicionar passeio".
- Propostas de estilos de viagem e quadros de simulação ficam na aba separada
  **Simular roteiros**, mantendo revisão/aprovação, histórico de rascunhos e orçamento.
- **Descobrir**, **Orçamento**, **Calendário**, guias anteriores, pesquisa,
  persistência Google/GitHub, formatos JSON e motor financeiro seguem existentes.
- Nenhum preço de 2027, reserva ou rota é presumido.
- Criar testes que comprovem a diferença entre seleção canônica e proposta,
  adição, edição, cancelamento, confirmação de exclusão e sincronização legada.
- Validar GitHub Actions antes de integrar à main.
