# UX89 — Simplificar navegação e hierarquia sem novo redesign

> **Status: proposta para review — NÃO IMPLEMENTAR neste PR.**
> Repositório: `clevertondecker/europe-trip`. Dependência visual e funcional: UX64, UX81–UX88, UX83 e REC03. PR #206 trata separadamente do JSON redundante em Minha lista; não sobrepor mudanças.

## Papel e objetivo
Atue como Principal Product Designer, Staff Python/Streamlit Engineer e Senior Code Reviewer.

O problema observado em **Explorar → Minha lista** é a concorrência entre muitos controles e títulos de contextos distintos antes do conteúdo principal: botões `Configurar minha viagem` / `Comparar alternativa`, expander `Ajustes avançados da simulação`, seletor público de atividade, expander `Atividades anteriores · avançado`, descrição de Explorar e título `Meu roteiro`. Não confundir presença de título genérico com prova de roteamento errado: rastrear a origem de cada componente antes de editar.

**Resultado esperado:** entrar em uma atividade e saber (a) onde está, (b) o que pode fazer aqui e (c) qual a próxima ação útil. Percurso de referência: **Descobrir → Minha lista → Montar roteiro → Organizar/Revisar e salvar**. **Comparar bases, mapa e orçamento são opcionais**, não bloqueantes.

## Auditoria obrigatória do HEAD antes da implementação
1. Rebasear/atualizar a branch de implementação a partir da `main` atual; revisar #206 e demais PRs abertos, garantindo que não se sobrescrevam mudanças.
2. Inspecionar visualmente ou em código a sequência de renderização em `app.py`, particularmente `render_context()` (antes dos tabs), `render_public_task_tabs()`, renderização condicional dos painéis legados, `render_wishlist()` e o ramo `page == "Roteiro"`. Inspecionar `planning_context_ui.py`, `ux64_navigation_model.py`, `ux64_navigation_ui.py`, `ux_navigation.py`, `ux502_destination_interests_ui.py`, `ux_planning_journey_ui.py` e `ux_shared_ui_presentation.py`.
3. Identificar o ponto concreto que produz o título `Meu roteiro` na atividade `Minha lista`. Confirmar se é cabeçalho genérico ou conteúdo de outra atividade antes de corrigir.
4. Inventariar cada controle público e legado, callback, key, URL/deep link, origem, ação de retorno e dependências. Não remover funcionalidades que ainda são a única forma de acessar pesquisa, backup ou simulação.
5. Capturar a experiência ANTES em 1440/768/390 px quando navegador real estiver disponível, documentando ordem, duplicações, rolagem e foco; caso contrário declarar pendente.

## Decisões propostas (submetidas a review)
### A. Manter a navegação pública UX64 exatamente em três áreas
- `Explorar`: Descobrir, Minha lista, Comparar bases, Mapa.
- `Planejar`: Visão geral, Meus destinos, Organizar.
- `Orçamento`: Visão financeira, Simulações.
- Não criar uma quarta área, wizard, outro router ou segundo conjunto público de tabs.

### B. Uma hierarquia clara por atividade
- Mostrar primeiro **breadcrumb/identificação da atividade, um único título e descrição curta**, depois conteúdo e CTA contextual.
- `Explorar → Minha lista`: desejos e prioridades, estado de salvamento privado e CTA **Montar roteiro com meus destinos** (se elegível); alternativa **Comparar bases** de menor destaque. Sem título concorrente `Meu roteiro` nem simulação financeira no topo.
- `Explorar → Descobrir`: busca, descoberta e adicionar à lista; evitar reexibir um cabeçalho de roteiro.
- `Explorar → Comparar bases`: seleção única CHOICE, síntese e matriz UX87/UX88; não interferir com a comparação inline.
- `Planejar → Meus destinos`: destinos incluídos/revisão/salvamento; datas opcionais.
- `Orçamento → Simulações`: editar hipóteses e comparar alternativas; **não** introduzir dados hipotéticos como custo oficial.
- Preservar o contexto e os atalhos de retorno em handoffs.

### C. Tirar controles técnicos do caminho principal, sem quebrar comportamento
- Reavaliar `render_context()`: `Configurar minha viagem` deve estar disponível em local de configuração contextual; `Comparar alternativa` deve fazer sentido somente onde sua ação é pertinente. Não esconder confirmação indispensável de configuração.
- Mover **`Ajustes avançados da simulação`** atualmente no topo de Explorar para o contexto adequado de **Orçamento → Simulações**, ou preservar acesso legado em seção técnica existente, desde que não crie instâncias duplicadas dos mesmos widget keys.
- **`Atividades anteriores · avançado`**: retirar da jornada principal e manter um único caminho de compatibilidade avançada quando necessário (por exemplo, `Fontes e ferramentas` já existente), sem expor um segundo navegador junto aos tabs públicos. Auditar o ramo de Comparar que o renderiza outra vez.
- Evitar texto explicativo repetido e blocos vazios acima do primeiro conteúdo útil. Não remover automaticamente `render_return_to_summary()` nem links de retorno antes de verificar seus contratos.

### D. Streamlit e identidade — invariantes
- Preservar `TripPlan`, prioridades e persistência da wishlist, `rec03a_scope`, `CHOICE`, `PREVIOUS`, `MANUAL_KEYS`, REC04 e orçamento, fontes REC05, configuração UX81 e roteamento UX64.
- Manter alias/deep links legados em `ux_navigation`; esconder interface **não equivale a apagar rota ou callback**. Preservar entrada por links, restauração da nuvem privada, conta e rascunho.
- Não atualizar chave de widget após sua instanciação, especialmente `ux64_public_task`, `ux_section`, `ux_mode`, `scenario_sidebar` e `flow_journey_view`. Garantir que a navegação solicitada seja aplicada antes de renderizar os tabs.
- Não criar cópias locais do plano, pontuações, simulações ou estados paralelos.
- Se a hierarquia puder ser corrigida com poucas condições de renderização, preferir isso a refatoração global em `app.py`.

## Plano de implementação proposto (somente após review)
1. **P1 — origem dos conteúdos cruzados:** ajustar renderização condicional para cada atividade ter um único cabeçalho e conteúdo coerente. Verificar `Minha lista` → `Meu roteiro` e acessos de login/retorno.
2. **P1 — reduzir duplicações acima da dobra:** ocultar/relocalizar simulação e navegação legada, mantendo pontos de acesso explícitos sem duplicar widgets.
3. **P2 — ação contextual e copy:** destacar uma CTA primária por estado (ex.: descobrir, montar, revisar), consolidar descrições, manter orçamento/mapa/comparação opcionais.
4. **P2 — acessibilidade:** hierarquia de headings, teclado/foco, labels, feedback sem rolagem forçada, responsividade 1440/768/390.
5. **Verificação:** registrar antes/depois e revisão adversarial. Não alargar escopo para redesenhar cards, gráficos, funcionalidades ou sistema visual.

## Matriz de aceite
| Cenário | Aceite |
|---|---|
| Explorar → Minha lista com desejos | Um título `Minha lista`, prioridades e CTA relevante; nenhum título `Meu roteiro` de outro fluxo nem simulador financeiro acima |
| Explorar → Descobrir | Filtros e adição à wishlist sem um editor de planejamento concorrente |
| Explorar → Comparar bases | UX87/UX88 continuam inline; CHOICE e escopo REC02 não se perdem |
| Explorar → Mapa | Mapa e controles pertinentes, sem configurações de orçamento duplicadas |
| Planejar → Visão geral/Meus destinos/Organizar | Editor e salvamento canônicos; pode salvar sem datas; sem título/controles de Explorar |
| Orçamento → Visão financeira/Simulações | Apenas dados e controles financeiros pertinentes; simulação nunca oficializa gastos automaticamente |
| Handoffs | Perfil, mapa, orçamento, revisão, retorno e navegação com filtro/seleção preservados |
| Legado | Deep links, snapshots privados, chaves compatíveis e ferramentas avançadas acessíveis de maneira discreta |
| Estado | Mudança de aba, login/logout, restore e rerun não instanciam widget duplicado nem perdem seleções |
| Viewports | Desktop 1440, tablet 768 e mobile 390 sem overflow, cabeçalhos duplicados ou CTA inacessível |

## Testes e gates
- Atualizar AppTests para percorrer **todas as 9 atividades públicas** e garantir presença de seu cabeçalho/conteúdo e ausência de elementos fora do contexto.
- Testar `Minha lista` com 0/1/vários destinos, `Planejar` com plano vazio/incluído/organizado; navegação e retorno depois de login e restauração.
- Testar que simulações mudam apenas cenário e não `TripPlan`, que REC03 mantém CHOICE/escopo, e que #206 não sofre regressão.
- Testes específicos de widgets instanciados: não registrar dois elementos com mesmo key nem alterar sessão após a renderização.
- Executar `python -m compileall -q .`, `python -m unittest discover -s tests -v`, validações de pesquisa e CI verde no HEAD final.
- Validar **navegador real** em 1440/768/390; AppTest não comprova foco, contraste, legibilidade ou ausência de overflow. Se não houver navegador, informar explicitamente.
- **Não fazer merge automático** na futura implementação até revisão e gates acordados.

## Fora de escopo
Sem alteração em algoritmos ferroviários, cálculos financeiros, importadores/exportadores de backups, modelos persistidos, UX81, wishlist, regras REC02, identidade ou novos fluxos públicos. Mudanças do PR #206 ficam em seu próprio PR.

## Entrega da futura implementação
Relatar: raiz de cada fricção, arquivos modificados, comportamento antes/depois, elementos removidos da visão cotidiana versus recursos preservados, cobertura de testes, CI, pendências visuais, regressões potenciais e recomendação de merge.

**Pergunta de aprovação:** A jornada fica compreensível em três áreas e uma atividade por vez, sem perder nenhum recurso e sem um segundo conjunto de opções técnicas competindo com a ação principal?
