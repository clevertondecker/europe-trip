# UX124C — Acabamento da ficha de cidade-base

Base: UX124B mergeado no commit 796458e. Capturas reais do usuário de Visão geral, Vida cotidiana e Logística: foto com crédito muito próximo, ações dispersas, preview com largura excessiva, ausência de bandeiras, falta de distinção visual entre preço e ausência de amostra, coluna de tempo típico inteiramente desconhecida e links isolados.

## Escopo implementado
- Reutilizar o país canônico de Descobrir na projeção somente leitura e COUNTRY_FLAGS do comparador; bandeiras ao lado dos destinos no resumo, na tabela, no seletor de detalhes e em atrações regionais. País desconhecido não recebe bandeira inventada.
- Cabeçalho: agrupar ações nativas junto à identidade e dimensionar foto/crédito no escopo do perfil; manter callbacks, capacidades, navegação e acessibilidade. Limitar largura da lista de conexões.
- Parafrasear as descrições documentadas e riscos editoriais conhecidos sem novos fatos; manter originais no expansor. Não afirmar segurança, comércio ou vida cotidiana sem pesquisa.
- Logística: mostrar coluna típica quando houver qualquer valor, inclusive divergência; quando todos forem desconhecidos, informar isso uma vez. Detalhes e valores canônicos mantidos.
- Vida cotidiana: estado ausente discreto, distinguir custo local e premissa compartilhada, fontes de custo em detalhe, passe com unidade/condições e tabela climática com uma casa decimal e fonte junto à estação.
- Não alterar datasets, arquitetura, cálculo, planejamento, wishlist, handoffs ou outros consumidores.

## Critérios de aceite
Preservar o comportamento das seis abas, flags por ID/country, nenhuma mutação de planos, tempos e divergências intactos, ausência de custo não é zero, atribuição/licença visíveis, ações próximas e layout adaptativo sem overflow. Testes de projeção em todas as cidades e AppTest específico. CI deve passar no HEAD exato. A captura do usuário é evidência do antes; navegador real pós-alteração não validado. Revisão visual e merge separados, sem autorização automática para este novo PR.
