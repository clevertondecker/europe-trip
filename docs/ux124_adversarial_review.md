# UX124 — Review adversarial: decisão antes de documentação

Findings confirmados no HEAD e83df63:
- Dois indicadores documentais eram exibidos antes de qualquer assunto; aluguel e desejos eram secundários.
- Logística mostrava contagem do catálogo mesmo com filtro da wishlist; ordenação misturava interested/maybe.
- Observações originais, estações e divergências não eram integralmente consultáveis.
- Perfil contextual carregava pesquisa pública novamente e duplicava a fila REC05; cache público preservado.
- Ações de favorita, mapa e simulação já existiam; faltava transição explícita para descoberta e para comparação com a cidade selecionada.
- Fontes antigas de tarifa podem representar outros destinos; manter escopo explicitamente separado, sem inferir correspondência.

Correções: visão geral com aluguel histórico, referências nos desejos, trabalho remoto, limites e imperdíveis sem tempo; seis assuntos; projeção pura de filtros e prioridades canônicas; detalhes por destino com observações originais; handoffs REC03A/B e CHOICE, seleção pública UX64; retorno contextual de descoberta; remove REC05 duplicado da ficha (continua Pesquisas & decisões). Sem novos datasets, ranking ou alterações de TripPlan/persistência. A ficha não conclui que um bate-volta é viável nem que a cidade é adequada sem evidências.

Testes: adaptação de contratos de UX107–110 e REC03B; novos testes de contagem, prioridade, local, filtro e imutabilidade; suíte de todas as bases/paridade já existente. CI e QA visual real devem ser verificados antes de aprovação. Não realizar merge automático.

CI e83df63: 1332 testes, 2 falhas, 2 ignorados. Falhas confirmadas: contrato antigo do seletor de pesos e regressão de importação a frio em worker com UX503 anterior. Reutilizado o resolver lazy REC01 existente (falha fechada quando a ficha é aberta), ajustado o teste de navegação para a seção Moradia, e preservado o retorno do mapa à ficha pelo handoff existente. Teste integrado percorre Descobrir, mapa, comparação e planejamento. Nova CI ainda pendente. Não há merge autorizado nesta revisão.
