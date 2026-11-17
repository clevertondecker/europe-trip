# Refinamento visual — fotografias dos destinos (UX 5.0)

## Problema
Em Explorar → Passeios → Descobrir lugares, os destinos originados das pesquisas ampliadas não possuem `photo` no catálogo original. O card ficava sem conteúdo visual, dificultando a escolha. As fotos já cadastradas (ex.: Freiburg) possuíam créditos e devem continuar como fonte prioritária.

## Solução
- Manter o catálogo, as identidades, atrações, prioridades e `TripPlan` exatamente como estão.
- A cada página de até 12 destinos, consultar **apenas os destinos sem foto** via `ux501_destination_photo_service.lookup_destination_photos()`. O artigo da **cidade** é identificado por ID/título explícito (não por similaridade ou localização geográfica). Reaproveitar sua imagem principal e obter autor, licença e miniatura pela API do Wikimedia Commons. Não escolher fotos por distância ou por pesquisa de palavras não relacionadas.
- Exibir somente arquivos de licença aberta reconhecida e autor documentado, com link para o arquivo original. Se a API não fornecer evidência suficiente, **não mostrar uma foto substituta de outra cidade**.
- Cache do Streamlit por seis horas para consultas da página visível (sem downloads de arquivos originais, sem novo banco, sem gravação remota). O conteúdo editorial estático do catálogo permanece prioritário.
- Cards passam a reservar sempre uma área 16:9 para a foto. Quando não há imagem comprovada, mostrar um placeholder neutro com a mensagem “Foto a pesquisar”.
- Nenhuma foto desta consulta implica viabilidade ferroviária, tempo, preço ou recomendação turística.

## Limitações
- **Dependência externa:** Wiki APIs e os thumbnails precisam ser acessíveis a partir do ambiente do Streamlit Cloud; bloqueios HTTP, timeout, falta de licença ou indisponibilidade podem deixar placeholders. Não inventar foto para encobrir falha.
- **Cobertura variável:** a imagem editorial principal da Wikipédia pode representar um monumento ou vista panorâmica, não necessariamente todas as atrações. O link de fonte explica a escolha.
- Metadados e atribuição são extraídos do Commons; não persistimos licenças ou imagens em um segundo catálogo.
- A inspeção visual real em desktop/mobile só pode ser declarada após visita efetiva ao aplicativo. Os AppTests verificam a estrutura do cartão e a origem da imagem com mocks.

## Escopo de arquivos
`ux501_destination_photo_service.py`, `ux501_destination_discovery_ui.py`, `tests/test_destination_photos_ux501.py`. Este documento. Sem mudanças de `TripPlan`, persistência, navegação, ranking ou pesquisas ferroviárias.

## Correção após validação na interface (17/11/2026)
A captura do Streamlit em produção mostrou fotografias para destinos do catálogo editorial (ex.: Freiburg), mas placeholders para Aachen, Baden-Baden, Colônia, Karlsruhe e Kehl. A primeira solução consultava as APIs Wikipédia + Commons no tempo da renderização e retornava um dicionário vazio em caso de falha HTTP ou metadados ausentes. Os mocks de CI não provavam conectividade do ambiente hospedado.

Agora as cinco cidades da captura possuem uma **seleção estática individualmente verificada** de arquivos públicos do Wikimedia Commons, com nome real do arquivo, autor, licença e URL da página de origem. Cada imagem usa `Special:FilePath` (redirecionamento direto para o arquivo), sem dependência de chamadas à Action API. A consulta dinâmica permanece apenas para destinos não cobertos e suas falhas não apagam as cinco imagens verificadas.

| Destino | Foto identificada / crédito | Licença |
| --- | --- | --- |
| Aachen | Cathedral in Aachen.jpg — Vitold Muratov | CC BY-SA 4.0 |
| Baden-Baden | Baden Baden - Lichtentaler Allee - View SE.jpg — Txllxt TxllxT | CC BY-SA 4.0 |
| Colônia | Köln Cathedral, Germany.jpg — AtmikaPaul | CC BY-SA 4.0 |
| Karlsruhe | MKa 0553 Schloss Karlsruhe.jpg — Martin Kraft | CC BY-SA 3.0 |
| Kehl | Passerelle des Deux Rives Kehl.jpg — H.Helmlechner | CC BY-SA 4.0 |

As páginas do Commons foram consultadas para confirmar autoria e licença antes de cadastrar. Não foi feita inspeção visual no Streamlit Cloud após a correção; bloqueios de imagens pelo navegador ainda podem ser investigados separadamente.
