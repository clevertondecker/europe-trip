# UX124B — implementação e inventário

Base: main `6984517` (CI pós-merge aprovada, run 45499049257). A captura enviada mostra os problemas de Visão geral; as demais seções foram auditadas pelo código. Não houve acesso a uma instância de navegador da branch durante esta alteração; nenhuma captura ou resultado visual é inventado.

## Alterações
- Cabeçalho contextual: retorno, nome/país/corredor, foto/atribuição existente, dois CTAs nativos de decisão, popover nativo de favorita, mapa e descoberta. Capabilities, limites e callbacks existentes preservados. Detalhes de simulação separados.
- Ficha única: seletor com label acessível mas oculto, um assunto renderizado por vez. Shadow de assunto/filtro no namespace rec03a (já invalidado na troca de identidade); sem persistência ou novo router. Acesso de Visão geral a Logística usa mesmo seletor.
- Overview: moeda compacta, cobertura dos desejos sem zeros supérfluos; lista compacta dos primeiros desejos na ordem canônica (inclusive locais/sem tempo), divergências preservadas; resumo sem prefixo administrativo, fatos deduplicados, trabalho remoto e pendências concisas; um único expansor de contexto.
- Moradia: mediana e faixa, anúncios/documentação em detalhes; colunas de internet, taxas, estação e duração com estado a verificar; bairros e fontes existentes.
- Logística: filtro com shadow, datas/estações/unidades legíveis; tarifas por destino no detalhe correspondente, referências adicionais claramente separadas; matriz e fontes intactas.
- Vida cotidiana: custos em blocos compactos, passe urbano resumido e normais climáticas existentes; um único conjunto de evidências da seção.
- Trabalho remoto: cartão com status, horário, preço/modalidade, internet e fonte. Não inferir compatibilidade.
- Atrações: cards e fotos atuais, ingressos/modalidades e dados ausentes explícitos; lista regional compacta e fontes sob demanda. Sem novos dados.

## Integridade
Nenhuma mudança em modelos de domínio, datasets, TripPlan, wishlist ou cálculo de orçamento. Reutiliza UX124, UX503/REC01, ROUTES7, UX113, REC03A/B, REC04, UX41 e fotos existentes. CSS escopado, HTML somente lista estática escapada. Nenhum ranking ou score. A cobertura não implica viabilidade. As três entradas compartilham o renderer; CTAs de recomendação permanecem apenas no contexto válido REC03B.

## Validação
Testes adicionados para todos os perfis (texto/fatos), valores e ingressos, preview de prioridades, navegação de assunto, retorno de descoberta com filtro, quatro cidades nas seis seções. Testes antigos de layout atualizados sem desativar contratos. CI e revisão de falhas do novo HEAD pendentes. QA real em 1440/1280/768/390px, contraste, teclado, fallback e screenshots antes/depois continuam pendentes; AppTest não comprova responsividade. Não mergear antes da revisão visual.

Review estático complementar: detalhes de simulação movidos ao popover existente; callbacks de assunto recebem somente a key, não toda a projeção privada; observações originais mostram minutos sem arredondamento ou conversão de tipo; disponibilidade 2027 explícita nos anúncios; teste de deduplicação diferencia resumo visível e evidência dentro do expansor. A remoção de código de UI antigo é restrita aos componentes substituídos; modelos mantidos.
