# UX132C1 — Cobertura documental de destinos e atrações

Atue como Staff Software Engineer e Principal Product Designer especializado em Python, Streamlit, qualidade de dados e UX no Nossa Europa 2027.

## Contexto e dependência
- UX132A (#269, integrado) introduziu Explorar → Comparar bases → Cobertura dos dados.
- UX132B (#270, ainda em validação) acrescenta filtros, detalhe e rastreabilidade ferroviária. Este PR é dependente e parte do HEAD 2b8d60f do #270. Antes de implementar, verificar alterações posteriores; após integração de #270, atualizar a branch e retarget para main, garantindo diff exclusivo. Não integrar antes da dependência.
- DATA24A já define inventário de atrações reconciliado e indicadores em data24_audit_model.attraction_inventory(), consumidos por tools/data24_research_coverage.py. Não reintroduzir o painel legado nem duplicar a auditoria.

## Objetivo
Ampliar a tela existente para responder: quantos destinos têm atrações catalogadas? Quais informações faltam nas atrações de cada destino? Quais fontes sustentam os dados? Sem misturar cobertura documental, qualidade da experiência, completude turística e viabilidade de 2027.

## Experiência e navegação
1. Manter entrada e navegação existentes, acesso independente da wishlist, do escopo e da seleção de base. Não criar nova página pública.
2. Adicionar seletor compacto de domínio dentro de Cobertura dos dados: Transporte ferroviário | Atrações turísticas. Manter Transporte como padrão para preservar UX132A/B. Visão geral deve apresentar os dois domínios com denominadores explícitos e permitir acessar o detalhe sem replicar navegação; decidir posicionamento final após verificar a tela real. Não adicionar domínios vazios como se estivessem implementados.
3. Atrações: usar Visão geral e Destinos (não aplicar a perspectiva ferroviária de cidades-base às atrações). Evitar dois seletores concorrentes de cidade. Reutilizar padrões de busca, filtro, estado e seleção por ID do UX132B quando úteis, sem abstrações especulativas.
4. Visão geral: exibir contagem de destinos e atrações únicas; indicadores documentais por campo e respectivas unidades, com numerador/denominador e pendências, sem média global de qualidade.
5. Destinos: tabela compacta com nome, número de atrações, foto contextual atribuída e contagens por campo; permitir busca sem acentos, filtro de lacuna selecionada, ordenação relevante e detalhe de um destino. Exibir atrações e respectivas pendências em uma tabela legível, com fontes e ressalvas por divulgação progressiva. Não criar ranking turístico. Não duplicar os cards de Descobrir ou a ficha Conhecer cidade.
6. Tratar ausência de atrações: zero atrações catalogadas não prova inexistência de atrações; campos por atração com denominador zero são N/A. Estado vazio, erros e filtros sem resultados devem ter mensagem clara.

## Contratos dos dados (obrigatórios)
Usar exatamente a projeção reconciliada do catálogo de descoberta (build_exploration_discovery) e data24_audit_model.attraction_inventory, com load_attractions, load_data23, load_macro_tourism e load_walking_access. Se necessário, extrair pequeno helper canônico compartilhado com a auditoria, sem criar outra fonte de verdade, sem alterar precedências e sem duplicar o inventário completo no disco. Não executar build_audit inteiro a cada interação. Não usar Markdown/JSON gerado como fonte se a projeção canônica já está disponível.

Indicadores suportados hoje pela auditoria:
- Destinos com ao menos uma atração catalogada / destinos do catálogo; foto contextual atribuída / destinos do catálogo.
- Atrações com descrição / atrações únicas reconciliadas.
- Duração editorial documentada / atrações únicas (explicitamente estimativa editorial, não duração verificada).
- Ingresso com preço, moeda e modalidade publicados; ingresso não aplicável; ingresso desconhecido. Preservar os três estados e suas contagens separadas sobre o total de atrações; não aplicável não é ingresso grátis, não contar como falta nem como preço conhecido.
- Foto própria atribuída / atrações únicas. Foto contextual de cidade não conta como foto da atração; atribuição exige URL, página de fonte, autor, licença e URL de licença conforme attributed_photo(). Não afirmar disponibilidade online sem teste.
- Acesso a partir de estação documentado / atrações únicas, apenas quando cumpre o contrato DATA24 (origem estação, duração e fonte, status aceito). Não equivale a porta a porta ou itinerário.
- Horários de abertura não fazem parte dos indicadores do inventário atual; mostrar como não medido se necessário, nunca inferir a partir da descrição nem atribuir 0% por ausência de contrato. Avaliar contrato de dados em entrega futura.
- Respeitar aliases reconciliados; não somar duplicatas. Não confundir total de atrações existentes no mundo com total do catálogo.
- URLs, datas, valores, atribuições e observações devem permanecer ligados ao registro que os sustenta. Separar fonte geral da atração, fonte do ingresso, licença da foto e fonte de acesso; não atribuir a data genérica a todos os campos. Ausência documental permanece desconhecida. Sem pesquisa online durante reruns, sem inventar valores, fotos ou horários.

## Integração, desempenho e manutenção
- Preservar todo UX132B, inclusive precedência de referências, filtros por eixo, estado shadow, DRAFT, SCOPE, CHOICE, wishlist, TripPlan, orçamento, persistência e handoffs.
- Estado de apresentação por domínio e eixo; validar seleção antes de montar o widget. Retornar a Transporte preservando filtros e seleção. Não salvar esse estado no roteiro.
- Medir execução do inventário de atrações e do detalhe com catálogo real; evitar construir inventário completo da auditoria em cada rerun e não criar cache preventivo. Não regredir custo ferroviário. Nenhum novo dataset de pesquisa, alteração de preços ou nova política de estimativa nesta entrega.
- Preparar a composição para UX132C2 (moradia, vida cotidiana, clima, trabalho remoto) sem antecipar implementação ou criar framework de domínios.

## Aceite e validação
- Testes puros de paridade com attraction_inventory e auditoria DATA24, contagens por destino somando globais, denominador zero, aliases, foto contextual versus própria, estados de ingresso, duração editorial, acesso de estação, ausência de fonte e proveniência.
- Testar atualização de cobertura ao acrescentar informação válida via fixture/entrada controlada sem alterar datasets oficiais.
- AppTest: acesso sem wishlist, alternância de domínios/áreas, pesquisa sem acentos, filtros, seleção inválida, retorno e preservação de DRAFT/SCOPE/CHOICE e TripPlan; manter testes ferroviários existentes. Diagnóstico de performance com tempos reais e sem limiar frágil.
- QA visual desktop/mobile quando disponível; checar ausência de controles redundantes e clareza dos denominadores. Registrar findings, decisões, resultados e limitações. CI do HEAD final obrigatória.
- Manter draft; não realizar merge sem autorização. UX132C2/C3 e DATA26 ficam fora do escopo.

## Resultado esperado
Uma evolução incremental da tela existente, orientada a lacunas acionáveis de destinos e atrações, baseada em dados reais e sem novo motor de pesquisa.


## Registro da implementação
- #270 integrado; PR retargetado para main e diff inicial exclusivo.
- Reutilizado attraction_inventory; extraído apenas attraction_counts para que os totais por destino e globais compartilhem o mesmo contrato. Nenhuma alteração em datasets, cobertura ferroviária ou artefatos gerados da auditoria.
- Seletor de domínio acima da navegação existente. Transporte continua padrão, com resumo de atrações na visão geral; domínio Atrações oferece visão geral e destinos. Inventário é carregado somente quando necessário, sem cache novo ou build_audit completo.
- Filtros de destino por texto, campo e pendências; ordenação por nome ou quantidade de campos pendentes. Não representa ranking turístico. Seleção por ID e estado shadow independentes do ferroviário.
- Ingressos: fonte específica exibida apenas se registrada no ticket; a fonte geral não foi reclassificada como fonte de ingresso. Data genérica identificada como data do registro geral. Atribuição fotográfica e acesso de estação mantêm suas fontes próprias.
- Horários de abertura permanecem não medidos; valores/condições documentados não confirmam 2027.
- Testes acrescentados: paridade global/por destino, reconciliação, N/A, preço zero versus não aplicável, foto contextual versus própria, acesso válido, atualização controlada, busca sem acentos, seleção e persistência por domínio, navegação real e preservação do escopo. Diagnóstico UX132C1_ATTRACTION_TIMING mede projeção e filtros/detalhe no catálogo real. Execução e QA visual ainda pendentes no momento deste registro; validar CI do HEAD final antes de merge.


## Review adversarial — 27/11/2026 (substitui decisões de composição iniciais)
### Dados e proveniência
- TRIP01: inspecionados os seis registros (três Obernai e três Lucerna). O JSON original só contém ID, nome, categoria e URL; não contém descrição, duração, preço, fotografia própria ou acesso por atração. Não há base para aumentar percentuais desses campos. A projeção de descoberta descartava metadados do registro suplementar e DATA24 só buscava três inventários. Agora o registro exato é preservado, com data do catálogo explicitamente geral, sem inferir evidência específica.
- DQ32: inspecionados 30 registros e o único alias reconciliado (dq32_luxembourg_city_22 → lux_bock). A fonte complementar existente não documenta preço/duração/foto/acesso. O ingresso histórico canônico permanece. A projeção usa somente ID exato e aliases já resolvidos, preserva campos canônicos conhecidos, complementa ausências por campo e mantém proveniência de cada registro. Ingresso é indivisível; não aplicável não é substituído por outra tarifa. Trechos de estação documentados para alias explícito preservam seus IDs e fontes. Não há correspondência por nome nem soma de atrações duplicadas.
- DATA23: as fotos próprias já eram consideradas pelo ID exato; não usar a foto contextual para completar lacunas. Horários não medidos. Não alterados os datasets oficiais; os indicadores atuais não devem aumentar apenas por esta correção.
### Arquitetura e UX
- A composição passou a ux132_coverage_page.py, com Visão geral como entrada padrão e áreas Transporte ferroviário / Atrações turísticas. Visão geral tem cartões, indicadores por domínio e botões diretos. Transporte mantém apenas eixos Cidades-base e Destinos; Atrações abre diretamente o detalhe por destino. Removida a visão geral aninhada. O retorno aos domínios mantém estado shadow independente.
- Extraídos os helpers pequenos search_key e widget_state; remember/restore_widget existentes movidos sem mudança semântica e reexportados por rec03a_suggestions_ui para compatibilidade. Domínios não importam um ao outro. Nenhum registry/framework.
- Mantida a entrada atual em Explorar → Comparar bases: transferência para área independente melhora semântica quando crescerem os domínios, mas hoje adicionaria navegação e exigiria revalidar fluxos/handoffs. Composição isolada permite decidir em UX132C3 sem reescrever os domínios. Mantido selectbox por ID: seleção de linha é posicional e seu estado é somente leitura, exigindo sincronização adicional após filtros e navegação; não adicionar dois mecanismos.
- Quantidade/total substitui Documentado/total. Visão geral mostra denominadores e lacunas; tabela de destinos reduz colunas e distingue pendências de destino de campos de atrações. Sem pontuação turística; N/A para campos sem denominador, sem duplicação de indicadores no mesmo resumo.
### Performance e validação
- Baseline aprovado #270 (run 45993772387): mediana 47,3 ms projeção ferroviária e 0,3 ms detalhe. O resumo executa somente as projeções canônicas necessárias (rail_coverage e attraction_inventory), sem agrupar detalhe por destino; reaproveita descoberta. Domínios especializados executam apenas a projeção respectiva. Sem cache novo ou indexação. O diagnóstico UX132C1_ATTRACTION_TIMING permanece; a execução do HEAD revisado e sua medição ainda pendentes.
- Testes adicionados/ajustados: TRIP01 real, alias real e complementar controlado, precedência atômica, foto/acesso por alias com proveniência, paridade global e por destino, links de resumo, isolamento de carregamento por domínio, filtros/seleções e navegação, incluindo DRAFT/SCOPE/CHOICE e handoffs. Testes existentes adaptados à entrada independente (sem remover regressões). A validação de execução do CI no HEAD final é obrigatória. QA visual desktop/mobile ainda não disponível nesta sessão. Manter draft; não mergear sem autorização.
