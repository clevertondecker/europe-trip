# UX81 — Design System compartilhado | Prompt de implementação

## Papel e objetivo
Atue como Staff Python/Streamlit Engineer, Design System Architect, Principal Product Designer e Accessibility Reviewer no repositório clevertondecker/europe-trip. Implementar uma linguagem visual única para todas as áreas públicas, partindo do resultado aprovado do PR #196 (Meu roteiro), mas SEM criar um novo tema paralelo, uma nova navegação ou uma reescrita.

## Estado real do produto
A navegação canônica de apresentação é definida em ux64_navigation_model.py:
- Explorar: Descobrir, Minha lista, Comparar bases, Mapa.
- Planejar: Visão geral, Meus destinos, Organizar.
- Orçamento: Visão financeira, Simulações.
Os TARGETS legados e a persistência continuam como estão. O CSS ativo já está em assets/styles.css, com tokens únicos auditados em docs/CSS10_DESIGN_SYSTEM_AUDIT.md. O PR #196 adicionou ux_planning_journey_presentation.py e a identidade de Meu roteiro.

## Contrato visual obrigatório entre todas as telas
1. Cabeçalho de página consistente: eyebrow contextual, título editorial, descrição curta e status factual quando existir. Não duplicar o título já fornecido pelo app.py.
2. KPIs em cards do mesmo sistema: tipografia, tamanhos, bordas, espaçamento, ícones, unidades, dicas de evidência e hierarquia. Apenas métricas derivadas de projeções existentes; nenhuma porcentagem fictícia.
3. Uma única ação visualmente primária por contexto; demais ações de navegação secundárias. O banner deve ter variante forte, compacta e ausente. Em Mapa e comparações densas, privilegiar área útil e usar próximo passo compacto.
4. Seções operacionais com hierarquia consistente (eyebrow, heading, descrição, toolbar, conteúdo). Status textuais sempre distinguidos de navegação/em foco.
5. Componentes de informação neutra, atenção, risco e sucesso preservando significado sem depender somente de cor.
6. Mesmo sistema responsivo de cards, gaps e largura nas três áreas: 1440 px, 768 px e 390 px; leitura vertical no mobile e nenhum botão comprimido.
7. Paleta e tipografia do CSS existente: DM Sans / Playfair Display e tokens --ui-heading, --ui-selected, --ui-page-bg, --ui-link, --ui-focus e paleta compatível. Não acrescentar um segundo :root nem fontes novas.
8. Imagens somente onde úteis; fotos reais/licenciadas com autoria/fallback, sem impor banners de imagem ao orçamento.

## Execução técnica
- Auditar assets/styles.css, ux_planning_journey_presentation.py, ux_planning_journey_ui.py, app.py e docs/CSS10_DESIGN_SYSTEM_AUDIT.md antes de editar.
- Extrair componentes reutilizáveis de apresentação (ex.: ui_shared_presentation.py e ui_shared_streamlit.py, ou nomes coerentes com o repositório), separados de estado de negócio. API proposta: page_header, kpi_cards, next_action, section_heading, status + variantes opcionais. Preservar suporte a HTML escaping e aos botões nativos Streamlit.
- Especializar por classes CSS sem seletores globais frágeis; limitar seletores st-key-* a containers nomeados. Não substituir controles nativos por botões HTML sem callbacks.
- Refatorar Meu roteiro para consumir estes componentes, mantendo aparência e semântica do PR #196. Preserve summary_only=True e todos os IDs flow_journey_*.
- Documentar uma matriz de padrões: elemento, variante, quando usar, não usar, estados, responsividade e acessibilidade. Registrar os desvios permitidos (Mapa, tabela de comparação, simulação).
- Garantir que renderização comum NÃO dependa de TripPlan, storage ou APIs externas: dados chegam por props/projeções já existentes.
- Não introduzir nova persistência, rotas públicas, scores ou dados inventados.

## Testes obrigatórios
- Testes unitários de HTML escape, estados, variantes e validação AA >= 4,5:1 inclusive gradientes.
- AppTest de navegação Meus destinos e resumo compacto, callbacks, edição, salvamento e retorno.
- Contrato CSS10: um único :root, foco visível, media queries, sem override destrutivo.
- Matriz visual manual real (não substituir por AppTest): 1440/768/390 px, light/dark se suportado, teclado, hover, disabled e zero-state. Documentar pontos não validados.

## Execução e entrega
Implementar código e testes NESTA branch. Rodar python -m compileall -q . e python -m unittest discover -s tests -v, conferir o GitHub Actions no HEAD do PR, anexar screenshots antes/depois quando possível e manter alterações estritamente ligadas ao sistema visual. Não fazer merge automático.

## Critérios de aceite / dependência
Meus destinos continua funcional e visualmente equivalente, com componentes documentados e testados para reutilização. UX82, UX83 e UX84 devem CONSUMIR estes componentes, não replicar sua marcação/CSS. PR de especificação inicialmente draft; só marcar pronto para revisão após implementação e testes.

---

## Contratos públicos do componente compartilhado (revisão arquitetural)

A fundação será **apresentação pura**, sem importar Streamlit, \`TripPlan\`, \`planning_store\`, \`continuity_ui\` ou serviços. O módulo compartilhado deve ter uma API estável e documentada, com dados vindos exclusivamente de projeções existentes. Nomes podem seguir convenção do projeto, mas os cinco contratos precisam existir:

| Componente | Entrada mínima | Saída/variante | Responsabilidade |
|---|---|---|---|
| \`page_header\` | \`title: str\`, \`eyebrow: str\`, \`description: str = ""\`, \`status_label: str = ""\`, \`status_hint: str = ""\`, \`saved: bool = False\`, \`tag: str = ""\` | HTML escapado; \`standard/compact\` | Só apresenta contexto e persistência **já comprovada**; não deduz salvamento |
| \`kpi_cards\` | \`metrics: Sequence[Mapping]\` contendo \`name\`, \`value\`, \`hint\`, \`icon\`, \`highlight\` | Sequência de cards HTML para \`st.columns\` responsivas | Não calcula nem inventa métricas; destaca somente conforme projeção |
| \`next_action\` | \`headline: str\`, \`explanation: str\` | \`strong/compact\` ou ausente na página | Só conteúdo informativo: **CTA nativa é responsabilidade do chamador** |
| \`section_heading\` | \`eyebrow: str\`, \`title: str\`, \`description: str = ""\` | \`standard/compact\` | Hierarquia editorial sem duplicar título de página |
| \`status_indicator\` | \`status: str\`, \`active: bool = False\`, \`kind: str = "neutral"\` | Estado e marcação de foco **independentes** | Sem confundir dados salvos, alterações locais e navegação |

### Responsabilidades e acessibilidade
- HTML de saída deve escapar **todos** os campos dinâmicos, inclusive nomes, hints, valores e status; sem \`onclick\` HTML nem botão decorativo.
- States de foco e persistência vêm de dados explícitos; não inferir sucesso privado por cor ou por presença de revisão.
- Classes CSS escopadas a esses componentes, reutilizando os tokens e a paleta existentes de \`assets/styles.css\`; não criar \`:root\` novo ou um segundo CSS concorrente.
- Fundir implementação de markup de \`ux_planning_journey_presentation.py\` aos contratos novos, deixando wrappers compatíveis somente quando protegidos por testes. **Não manter duas bibliotecas equivalentes.**
- Preservar \`flow_journey_*\`, \`summary_only=True\`, \`render_build\`, \`render_review\`, \`_render_organize\`, mapeamentos UX64 e callbacks nativas.
- \`strong\` só para a ação contextual principal; usar \`compact\` em mapa, comparação, orçamento denso. Cards mantêm hierarquia visual uniforme; estado não depende apenas de cor.
- Testes: presença de classes/estados, escaping, contraste WCAG AA >= 4.5, contrato CSS10, AppTest de Meus destinos e resumo, largura 1440/768/390; se não houver navegador, anotar não validado.

**Dependência da série:** só depois de implementação e integração deste PR em \`main\` realizar as integrações UX82/UX83/UX84. Sem merge automático e manter draft até os gates de aceite.

---

## UX81 P2 — Como usar `next_action` fora de Meu roteiro

**Causa:** anteriormente, `strong` emitia texto branco, mas seu fundo dependia da key `flow_journey_next`. Agora a variante tem fundo, borda, padding, tipografia e responsividade próprios.

**Uso autônomo:** chamar `st.markdown(next_action(title, explanation, variant="strong"), unsafe_allow_html=True)` em qualquer página. A classe `.ui-next-action--strong` define toda a superfície mesmo sem `st.container` nomeado.

**Uso com CTA nativa e fundo único (recomendado):**

```python
with st.container(key="ui_action_shell_strong_explorar"):
    st.markdown(next_action(title, explanation), unsafe_allow_html=True)
    st.button("Continuar", key="explorar_cta", type="primary", on_click=callback)
```

O prefixo de key compartilhada `ui_action_shell_strong_` é um opt-in para agrupar a CTA nativa. Streamlit coloca Markdown e botões em elementos irmãos do DOM, portanto o CSS pinta somente o contêiner exterior e neutraliza fundo e padding do filho `.ui-next-action--strong`. **Não existe card duplo.** A key histórica `flow_journey_next` continua como shell compatível sem mudanças de callbacks.

**Uso compacto:** `st.markdown(next_action(title, explanation, variant="compact"), unsafe_allow_html=True)` — estilo claro autocontido para Mapa, Comparar bases, Visão financeira e Simulações. Não introduz botão HTML fictício.

**Testes e limites:** novos testes cobrem variante autônoma e compacta, neutralização do card interno, contraste >= 4,5:1 e botões nativos em AppTest; o controle de keyboard/focus/disabled é escopado a shells opt-in. **Navegador real (1440/768/390 px) não validado nesta execução**, portanto comparação visual com PR #196 permanece pendente. AppTest não mede layout CSS.

**Dependentes:** #198, #199 e #200 podem reutilizar o mesmo contrato. O problema `summary_only=True` de Meus destinos (#199) continua pendente e fora do escopo deste PR.
