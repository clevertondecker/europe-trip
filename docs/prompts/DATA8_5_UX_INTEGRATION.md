# DATA 8.5 — Integração nas telas existentes, sem navegação paralela

**Papel:** Senior UX/Product Engineer + Python/Streamlit Engineer. **Dependências:** DATA 8.1, 8.2, 8.3, 8.4.

## Implementar
1. Reutilizar o catálogo base-free da tela `ux501_destination_discovery_ui.py`: dentro do expander de atrações existente, indicar fichas enriquecidas e propostas que precisam de reconciliação.
2. Reutilizar o expander `Atrações: experiência, ingresso, horários e pendências` do comparador `ux503_destination_base_comparison_ui.py` para mostrar, por atração, motivo para conhecer, faixa editorial de visita, ingresso ou desconhecido, regra de funcionamento com fonte, endereço publicado e caminhada preliminar em cada sentido. Atrações sem ficha mantêm fallback do legado.
3. Permitir uma simulação **opcional** para duas pessoas, com seleção explícita de atrações, custos de trem/local/refeições como faixas digitadas pelo usuário e câmbio manual opcional. Se faltar preço ou faixa, exibir lista de pendências, nunca um valor final fictício.
4. Nunca incluir fotos sem licença/crédito ou inferir fotos de atração a partir das fotos da cidade.
5. Respeitar 2–5 cidades-base e a mesma wishlist, sem ranking automático; não alterar `TripPlan`, orçamento oficial ou prioridades.
6. Testes puros para a apresentação, orçamento e invariantes. Verificar Streamlit via CI/AppTest e inspecionar visualmente antes de merge.

**Aceite:** 18 fichas acessíveis nas telas existentes, ausência de fichas nos destinos de Colônia/Gand explicitamente demonstrada sem cadastro forçado, 7 cenários de caminhada editoriais, simulação incompleta transparente, nenhum dado futuro inventado.

**Regra de governança:** alterações de UX de propriedade compartilhada devem ser realizadas somente pela função integradora do projeto; este PR é o ponto de integração. Entregar aberto para revisão, sem merge/deploy.

## Revisão corretiva — 18/11/2026

- Na comparação, compor campos DATA 8 e legado por proveniência, sem `continue` que oculte documentação histórica.
- Usar entrada geral, visita exclusivamente externa e atividades adicionais como escopos distintos e explícitos.
- Classificar ingresso não pesquisado como desconhecido; não equiparar a custo zero.
- Cada faixa de transporte informada na simulação representa ida e volta de **dois adultos** e é hipótese manual.
- Caso qualquer custo do escopo esteja ausente, exibir total parcial com pendências e bloquear total completo.
- Validar cenários interativos por Streamlit AppTest; não alterar `TripPlan`, wishlist ou orçamento.
