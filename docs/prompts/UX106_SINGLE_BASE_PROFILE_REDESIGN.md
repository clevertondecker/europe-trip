# UX106 — Redesign consolidado da investigação individual de cidade-base

> **STATUS: PROMPT PARA REVIEW.** Este PR apenas documenta a implementação proposta. **Nenhuma mudança funcional foi aplicada**. A execução depende de aprovação explícita; não tratar este PR documental como entrega visual concluída.

**Repositório:** https://github.com/clevertondecker/europe-trip

**Referências:** PRs documentais #226 (UX101: cabeçalho, síntese, ações) e #227 (UX102: organização de detalhes), e esboço visual aprovado para **Strasbourg, França**. Este prompt **consolida** as propostas numa única jornada e é a referência preferencial para implementação. Evitar implementar duas versões concorrentes; não criar um segundo perfil.

**Fluxo real:** `Explorar → Comparar bases → Cidade para investigar individualmente → Conhecer cidade`. `rec03b_handoff_ui.render_profile_context(plan)` obtém `CONTEXT` e a cidade fixa, mostra retorno/favorito/simulação/mapa e delega ao `base_research_expanded_ui.render_expanded_research(activity_override="Explorar uma cidade", compact=True, fixed_city=base)`. A página atual repete “Explorar cidades”, “Explore uma cidade” e o nome da cidade, deixa ações em coluna e organiza informação como uma longa pilha de expanders.

## Resultado visual aprovado — estrutura, não imagem fictícia

Implementar uma única **ficha editorial de cidade-base**, com visual profissional e responsivo, inspirada em aplicativos de viagem. A referência é *Strasbourg, França*. Números **3 anúncios históricos de 2026** e **10/15 tempos da cesta histórica** vieram da captura específica e **não devem ser hardcoded**. A mesma ficha deve atender Mulhouse e outras cidades, com dados reais, estados vazios e status corretos.

Ordem da tela:

1. **Breadcrumb + voltar:** “Comparar bases / Investigar cidade” e controle nativo **Voltar à comparação**, preservando escopo e seleções.
2. **Hero da cidade:** fotografia **real e licenciada**, quando disponível, opcional e com crédito; título principal único “Strasbourg, França”; subtítulo “Cidade-base em investigação”; corredor documentado e chip de status (“Finalista da pesquisa”, “Candidata” ou “Base oficial atual”) segundo dados reais; texto curto orientado à decisão. Não equiparar `shortlist=True` a recomendação final.
3. **Barra compacta de ações nativas:** **Simular esta cidade** em evidência *apenas quando elegível*; **Ver no mapa**; **Adicionar/Remover favorita**; retorno em posição secundária. Desktop horizontal, mobile empilhado. Para cidade inelegível, explicar o motivo, sem CTA falso. Nenhuma ação muda a base oficial silenciosamente.
4. **“[Cidade] em resumo”:** três cartões concisos, não indicadores soltos: **Moradia pesquisada** (contagem e ano históricos); **Tempos pesquisados** (X/Y na cesta histórica comparável, não avaliação nem contagem do escopo personalizado); **Contexto/corredor documentado** ou status de pesquisa pendente. Quarto cartão apenas se houver benefício de leitura concreto, sem duplicar “Finalista”.
5. **“O que sabemos sobre a cidade?”**: dois painéis lado a lado no desktop, empilhados no mobile: **Já documentado** (semântica neutra/favorável, evidências respaldadas) e **Ainda precisa confirmar** (pendências verificáveis). No máximo três achados curtos por lado como resumo, demais informações disponíveis nos detalhes. Não confundir cobertura de evidências com benefício logístico; evitar recomendar uma “melhor base”.
6. **“Explore os detalhes”:** três entradas/agrupamentos principais de consulta: **Moradia e bairros**, **Trens, logística e passeios**, **Como é viver em [cidade]?**; em seguida **Fontes e metodologia** como seção avançada. Os títulos são orientação de leitura, não botões HTML decorativos. Implementar com widgets nativos/expanders acessíveis, abrindo o conteúdo existente sem duplicá-lo. Pesquisa opcional REC05 deve permanecer acessível após as seções principais.
7. **Fechamento contextual:** nota “Investigar/simular não altera automaticamente sua base oficial”, e retorno à comparação claramente disponível.

A ficha **não** é um novo comparador, wizard, editor de roteiro ou sistema de decisões.

## Dados e reuso: antes de codificar

Inspecionar no HEAD atual da `main`:

- `rec03b_handoff_ui.py`: `render_profile_context`, `_favorite`, `return_to_suggestions`, `queue_handoff`, `CONTEXT`;
- `rec03b_handoffs.py`: `CHOICE`, `PENDING`, filtros/escopo da investigação;
- `base_research_expanded_ui.py`: `render_expanded_research`, `_explore_city`, `_city_profile`, `_city_housing`, `_city_routes`, `_candidate_media_and_logistics`;
- `base_research_expanded_model.py`: `load_research(include_candidates=True)`, `find_city`, `observed_housing`, `decision_readiness`;
- `base_coverage_model.py`: `coverage_matrix("general", study=study)`;
- `city_profiles_model.py` / `city_research_packs_model.py`: fatos, bairros, clima, mobilidade e fontes;
- `data23_france_candidates_model.py`: referências regionais adicionais **fora da cobertura histórica**;
- `ux105_base_city_context.py`: pesquisa local apenas onde disponível (não criar um segundo catálogo);
- `ux100_base_card_photos.py`, `destination_photo_assets.py`, `ux501_destination_photo_service.py`: prioridade de fotos, licença, autor e fallback;
- `rec04_candidate_capabilities.py`, `rec04_simulation_handoff.py`: capacidade de simulação;
- `ux41_favorites_model.py`: limite de favoritos, mudanças/salvamento;
- `rec05_priority_research_ui.py`: pesquisa opcional que deve continuar acessível;
- `ux_shared_ui_presentation.py` e `assets/styles.css`: tokens e apresentação existente;
- testes de `tests/test_rec03b_handoffs.py`, exploração independente, pesquisa expandida e viagens.

A solução deve reduzir as camadas de apresentação, não criar `ux106_data.json`, um novo catálogo de informações nem um segundo motor de recomendação.

## Responsabilidades de implementação

### A. Ficha resumida, sem duplicações

Preferir uma projeção **pura, pequena e testável** dos campos já existentes para título/corredor/status/KPIs/achados. Exibir sempre com rótulos, unidade, período e limite real. Caso o dado não exista, usar “Não pesquisado”, não `0`, aproximação ou score artificial. Separar:
- 10/15 tempos da cesta histórica;
- o subconjunto de destinos que o usuário escolheu para sua viagem;
- referências DATA23 adicionais sem retorno confirmado.

Não inferir aluguel disponível de anúncios de 2026 nem disponibilidade/horários para setembro–novembro de 2027.

### B. Um único nível de título

No fluxo `fixed_city`, evitar renderizar “Explorar cidades”, “Explore uma cidade” e a cidade novamente em sequência. Garantir que `fixed_city=None` **continue exibindo os títulos do explorador independente**.

Não duplicar a foto, métricas e blocos de documentação em outras seções abaixo.

### C. Ações e estados existentes

Usar `st.button`/callbacks já existentes; manter as chaves estáveis quando possível, incluindo `rec03a_handoff_back_profile`, `rec03a_handoff_favorite`, `rec04_simulate_profile`, `rec03a_handoff_profile_map`.

- Retorno preserva `CHOICE`, escopo, filtros e wishlist.
- Favoritar respeita `MAX_FAVORITES` e não declara salvamento persistente antes de confirmado.
- Simulação valida elegibilidade por cidade, sem promover bases exploratórias a oficiais.
- Mapa utiliza o handoff atual com a cidade correta.
- Apenas renderizar a ficha não altera `TripPlan`, `scenario_base_selected` ou dados de sessão além de widgets previstos.

### D. Fotografia

Hero somente para foto com ID exato da cidade, fonte, licença e autor presentes no catálogo já validado. Priorizar WebP local; se externa, fallback robusto para indisponibilidade de rede. **Não** fazer pesquisa livre, scraping, geração de imagem ou substituição por fotografia de cidade vizinha. Texto alternativo útil e crédito visível/acessível. Sem imagem válida, manter cabeçalho tipográfico elegante — não deixar um retângulo gigante vazio.

### E. Detalhes com hierarquia, sem perder dados

Dentro do modo `fixed_city`, reorganizar o conteúdo já existente em **três assuntos e uma seção documental**:

- **Moradia e bairros:** amostras históricas, preços observados, localizações, referências; esclarecer contratos e disponibilidade de 2027 pendentes.
- **Trens, logística e passeios:** tempos/documentos com origem e destino, categorização histórico/indicativo/local, referências DATA23 diferenciadas; fontes e ressalvas de retorno, frequência e última milha.
- **Como é viver na cidade?:** bairros, clima histórico (não previsão), mobilidade e contexto municipal; atrações licenciadas disponíveis, sem publicidade genérica.
- **Fontes e metodologia:** documentos, limitações, pesos/documentação técnica e lacunas. Pesquisa opcional REC05 continua disponível, mas não precisa dominar a primeira dobra.

Não transformar três cartões de seção em páginas novas; não criar cliques falsos, múltiplos expanders aninhados nem tabelas repetidas. Fontes relevantes acessíveis em no máximo um nível de abertura quando viável.

### F. Visual real implementável em Streamlit

- Card/hero com espaçamento, bordas leves e tipografia do design system existente; CSS `ux106-*` escopado;
- Verde discreto para fatos documentados e âmbar para lacunas, sem depender só da cor;
- Botões agrupados com prioridades claras, incluindo estados disabled;
- Até três indicadores lado a lado no desktop; se ficar apertado, reduzir a duas colunas ou uma, nunca forçar cards minúsculos;
- **1440 px:** hero/ações/resumo legíveis e detalhes bem hierarquizados;
- **768 px:** reflow sem truncar texto/ações;
- **390 px:** uma coluna, sem overflow horizontal da página, botões tocáveis e texto acessível.
- Não usar hacks globais de CSS, classes internas aleatórias do Streamlit, JS para navegação ou HTML de botões inertes.

## Estratégia de entrega

**Preferência: um único PR funcional** para a experiência completa, pois UX101 e UX102 são duas partes da **mesma tela**, mas permitir separar em no máximo dois PRs funcionais (hero/resumo e detalhes) se testes, conflitos ou revisão justificarem. Não quebrar a jornada entre PRs nem criar mais uma abstração sem benefício concreto. Fazer uma auditoria rápida das branches existentes antes de iniciar.

No PR funcional, registrar decisões de produto (o que aparece acima da dobra e o que fica em detalhe) e mapear arquivos alterados. Nada de persistência paralela ou migração de dados.

## Plano de testes e aceite

1. Testes puros para projeção dinâmica: Strasbourg (3 anúncios e 10/15 na captura, verificar dados no HEAD), Mulhouse, cidades com 0 anúncios, 0 tempos, dados parciais e base exploratória.
2. AppTest do fluxo: comparar → escolher cidade individual → conhecer cidade → favorito → simulação elegível/inelegível → mapa → retorno, sem perder `CHOICE`, wishlist, escopo, filtros, `TripPlan` e contexto.
3. Garantir que UI `fixed_city` tenha **um título principal** e não tenha os títulos duplicados; `fixed_city=None` permanece íntegro.
4. Abrir moradia, logística, cotidiano e fontes e confirmar que **todas as informações e URLs pré-existentes** seguem acessíveis e pertencem à cidade escolhida.
5. Fotos: com WebP local, Commons curado, fonte inválida, indisponibilidade externa e ausência de foto; validar autor/licença/alt/fallback.
6. Testar foto e conteúdo de Aachen, Angers, Annecy, Arlon, Strasbourg e Mulhouse, quando há dados; não extrapolar onde não houver.
7. Validar fluxo do roteiro: investigar/simular nunca altera silenciosamente a base oficial; verificar caminho de volta e salvamento independente.
8. Rodar `python -m compileall -q .`, `python tools/validate_research_data.py` e `python -m unittest discover -s tests -v` **sem enfraquecer a suíte**.
9. Executar **navegador real Streamlit** e capturar telas em 1440/768/390 px, conferindo layout, overflow, contraste, foco e leitura assistiva. AppTest não prova fidelidade visual.
10. Code review adversarial: identificar regressões em páginas reutilizadoras de `render_expanded_research`, widgets duplicados e nova lógica de pontuação.

## Critério de aceite

Um usuário que abre Strasbourg identifica **em poucos segundos**: qual cidade, país, corredor e status; principais referências documentadas; limites de moradia/transporte de 2027; e ações reais de simular, mapa, favorito ou voltar. Os detalhes ficam agrupados em 3 áreas + documentação, sem repetir os sete accordions originais, com dados e fontes preservados.

**Este PR é somente um prompt de implementação para aprovação. Não executar código nem mergear automaticamente.**
