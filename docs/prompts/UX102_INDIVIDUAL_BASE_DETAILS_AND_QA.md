# UX102 — Detalhes da cidade-base: navegação, fontes, responsividade e QA

> **STATUS: PROPOSTA DOCUMENTAL, SEM CÓDIGO IMPLEMENTADO.** Revisar este prompt juntamente com UX101. Este PR só cria documentação. Implementar após o aceite do UX101, sem duplicar cabeçalho, estados ou serviços.

## Contexto e dependência

Repositório: `clevertondecker/europe-trip`.

**Dependência de UX:** UX101 organiza o contexto, ações e síntese da ficha individual. UX102 organiza **o corpo detalhado abaixo dessa síntese**, para transformar relatórios técnicos em uma experiência de consulta fácil.

O fluxo atual de `render_profile_context()` invoca:
- `base_research_expanded_ui.render_expanded_research(..., compact=True, fixed_city=base)`;
- `rec05_priority_research_ui.render_research_from_session(key="rec05_profile", base_ids=[base])`.

A pesquisa usa `_explore_city` com `_city_profile`, `_candidate_media_and_logistics`, `_city_housing`, `_city_routes`, indicadores e `decision_readiness`, seguidos por metodologia. Hoje as seções **“Vida cotidiana, bairros e clima”, “Fontes públicas e limitações”, “Moradia · anúncios históricos”, “Trens e passeios · tempos e fontes”, “Pesquisa técnica”, “O que ainda não podemos confirmar”, “Pesquisa opcional”** parecem todas equivalentes e perdem prioridade.

## Objetivo

Dar ao usuário uma sequência lógica de leitura sem perder nenhuma fonte ou dado existente:

1. **Essencial para decidir**: moradia, deslocamentos, passeios;
2. **Conhecer a cidade**: vida cotidiana, bairros, clima e atrações locais;
3. **Fontes e metodologia**: evidências verificáveis, lacunas e estudo técnico;
4. **Pesquisa opcional**: investigação aprofundada, sem se sobrepor ao básico.

Trata-se de **divulgação progressiva** no mesmo perfil, não de criar novo wizard, navegação paralela, etapas obrigatórias ou formulário.

## UX proposta

### 1. “Explore os detalhes”

Imediatamente após os painéis UX101, apresentar blocos/títulos de seção claros.

**Bloco Moradia e custo observado**
- Nº de anúncios históricos já exibido no resumo, mas não repetir o mesmo KPI várias vezes;
- Exemplos de anúncios com preço e tamanho reais e fonte clicável, quando houver;
- Indicar “amostra de 2026”, fonte e ausência de cotação de aluguel mobiliado por 56–60 noites para 2027;
- Quando zero anúncios: estado vazio explicativo, nunca `€ 0` nem preço interpolado.

**Bloco Trens, passeios e conexões**
- Tempos de ida/documentos ferroviários existentes, distinguindo cesta histórica do DATA23;
- Rota sem tempo: “Não pesquisado”, jamais “0 min” ou rota impossível;
- Para trajetos: categoria, origem/destino, tempo, eventual ressalva de estação e link real;
- Retorno, última milha, bilhetes de 2027 e custo final sempre identificados como pendentes;
- Fotografias/licenças das atrações já verificadas continuam acessíveis, sem requisições desnecessárias em cada rerun.

**Bloco Vida cotidiana, bairros e clima**
- Reusar `city_research_packs_model`, `city_profiles_model`, `_city_profile`;
- Para clima, quando disponíveis, as normais 1991–2020 para setembro–novembro são contexto histórico, **não previsão de 2027**;
- Restaurantes, bairros e custos têm data/fonte; dados ausentes ficam claros e neutros.

### 2. “Fontes e pesquisa avançada”

Agrupar sem esconder informações críticas:
- `Fontes públicas e limitações`;
- `Metodologia da pesquisa` (substitui o título técnico excessivo “critérios, pesos e pontuação indisponível”, sem alterar o cálculo);
- `O que ainda não podemos confirmar`;
- `Pesquisa opcional · lacunas prioritárias` de REC05.

As ressalvas mais importantes aparecem já na síntese UX101; documentação detalhada fica aqui. **Uma fonte não pode exigir abrir vários expanders aninhados**, principalmente links de moradia e rotas. O status “pesquisa pendente” permanece visível no contexto adequado.

Não apagar `render_research_from_session(key="rec05_profile", base_ids=[base])`, pesquisas auxiliares, filtros de cinco bases ou relatórios acessados por outros fluxos; apenas reorganizar o modo de exibição no perfil `fixed_city`.

### 3. Controles e comportamento

- Preferir `st.expander` nativo ou blocos com `st.container`; evitar cartões HTML que imitem botões.
- Não exigir uma tab adicional apenas para mostrar conteúdo que já está na página.
- Evitar submenus e múltiplas áreas expansíveis aninhadas; conservar acesso direto a fontes.
- Se usar tabs nativas, documentar como estado/teclado funcionam e não perder conteúdo ao navegar.
- Evitar widgets duplicados com a mesma `key`, especialmente `expanded_bases_rank_preset`, `rec05_profile` e controles legados.
- Não gerar novos KPIs a partir de dados incompletos; documentação técnica não deve criar ranking.

### 4. Responsividade, CSS e acessibilidade

Usar classes `ux102-*` e integrar com o design system atual de `assets/styles.css`; não sobrescrever estilos globais de `stExpander`, `stCheckbox`, `stButton` ou `stDataFrame`.

- **1440 px:** hero + resumo acima, detalhes em largura confortável, agrupamentos fáceis de escanear;
- **768 px:** seções e cartões adaptados sem cortes, ações refluem;
- **390 px:** uma coluna, botões com área de toque suficiente, sem rolagem horizontal da página; tabelas de trem com scroll local se necessário;
- Indicadores nunca dependem apenas de cor; rótulos, ícones e textos acessíveis;
- Foco visível por teclado, `aria-label`/alt em imagens reais, fontes com texto de link compreensível;
- Sem modais invasivos, JS injetado nem CSS preso a hashes de classe;
- Não tratar AppTest como prova de layout; screenshots devem ser do Streamlit realmente executado.

### 5. Reuso e migração sem regressões

- Modificar em escopo mínimo `base_research_expanded_ui.py` e componentes de apresentação, respeitando o modo `compact=True,fixed_city=...`;
- A exploração independente `fixed_city=None`, comparação de favoritas, relatório de cinco bases e mapa devem continuar oferecendo as mesmas fontes;
- Preservar `rec03b_handoff_ui.render_profile_context`, ações UX101, `CHOICE`, `CONTEXT`, `TripPlan`, filtros da wishlist e favoritos;
- Não introduzir salvamento paralelo da investigação nem alterar o status de base oficial;
- Reusar `ux100_base_card_photos` e as imagens existentes quando aplicável, sem scraping ou substituições inventadas.

## Testes de aceite

### Fluxo

- Comparar 2–5 bases → investigar Mulhouse → abrir moradia, tempos, cotidiano e fontes → retornar à comparação com as mesmas bases;
- Alternar para candidata fora do fluxo oficial (ex. uma cidade apenas exploratória) sem erro e sem CTA de oficialização indevida;
- Perfil com 0 anúncios, sem tempos ou sem clima documentado;
- Mudar de atividade / retornar a outra cidade sem duplicar keys e sem abandonar o contexto de pesquisa;
- Conferir `advisor_plan`, wishlist, `CHOICE`, filtros e favoritos antes/depois; nenhum render muda dados;
- Todos os links de fonte já existentes permanecem presentes em pelo menos um caminho nativo de abertura; nenhuma foto perde crédito/licença.

### Tests e ferramentas

- Testes puros para a projeção das seções e estados vazios;
- AppTest do perfil (incluindo abrir cada detalhe, filtros e navegação), sem exigir nova interação artificial;
- Regressão `tests/test_rec03b_handoffs.py`, `tests/test_cross_page_base_exploration.py`, `tests/test_base_explorer.py` e demais testes existentes;
- `python -m compileall -q .`;
- `python tools/validate_research_data.py`;
- `python -m unittest discover -s tests -v`;
- Capturas reais, com navegador, nas larguras **1440/768/390 px**, revisando overflow, contraste, foco, leitura das fontes e responsividade.

## Critério final

A página continua sendo **uma ficha de investigação**, não uma tela de relatório técnico e nem uma nova etapa de roteirização. O usuário encontra moradia, trajetos e contexto cotidiano com rótulos claros; documentação aprofundada está acessível sem exigir vários cliques aninhados. Não se perde detalhe técnico, nem se inventam benefícios ou preços.

## Entrega e dependência

- PR atual: **somente este prompt para review**; não implementar código nem fazer merge automático.
- Implementação futura: iniciar somente depois da aprovação da proposta UX101, mantendo os PRs funcionais separados e testáveis.
- Se a divisão técnica não justificar dois PRs funcionais depois da revisão, pode-se agrupar a implementação em **um único PR funcional** preservando os dois critérios de aceite, desde que continue revisável e sem duplicação de código.
