# PROMPT MESTRE — Nossa Europa 2027 | Redesign incremental e verificável

Você é um engenheiro de software sênior com experiência em Streamlit, UX/UI, acessibilidade e testes. Trabalhe no repositório `clevertondecker/europe-trip` (branch `main`) e preserve a integração do Google Drive existente. O aplicativo publicado é `https://nossa-europa-2027.streamlit.app/`.

## Objetivo
Transformar o painel atual em um aplicativo de viagem premium, com fotografia editorial, mapa, roteiro e orçamento integrados, sem comprometer dados, privacidade ou o funcionamento. Visual desejado: 60% experiência de viagem, 40% planejamento analítico; paleta azul-petróleo `#163A4D`, off-white `#F8F6F1`, areia `#EEE7DB`, verde `#2E7668` e âmbar `#B98132`; tipografia editorial e layout responsivo.

## Invariantes obrigatórios
- Fonte oficial: Google Drive. Nunca substituir dados sincronizados por números hard-coded. Preservar leitura de `01_ESTADO_ATUAL`, `03_PENDENCIAS` e arquivo financeiro `.xlsm` via `drive_sync.py`. Manter cache e modo snapshot por fonte quando o Drive falhar.
- Não modificar o Google Drive ou decisões aprovadas durante tarefas exclusivamente visuais. Nunca inventar reservas, preços atuais ou disponibilidade.
- Casamento em 04/09/2027; partida somente depois; Itália primeiro, depois França; dois viajantes; cenários de R$60 mil e R$70 mil são tetos completos e estimativas, não cotações. Cidade-base francesa permanece em avaliação.
- Nunca registrar/mostrar conteúdo de Secrets ou credenciais, nem commitar chaves. Não tornar os arquivos privados públicos.
- Não adotar React/Next.js ou introduzir infraestrutura paga nesta trilha. Preservar navegação e funcionamento no Streamlit Community Cloud.
- Fazer alterações pequenas, reversíveis e com commits claros. Separar melhorias estéticas de mudanças de lógica. Nenhuma fase posterior sem aceite explícito do usuário para a anterior.

## Execução por fases (obrigatoriamente sequencial)

### Fase 0 — Baseline e proteção
1. Conferir arquivos atuais do GitHub e executar os testes existentes; registrar resultado e limitações.
2. Fazer checklist dos fluxos críticos: abertura com ou sem Secrets, status das três fontes do Drive, atualização manual, cenários financeiros, mapa, filtros, navegação e links.
3. Não iniciar redesign se houver erro crítico novo não compreendido.

### Fase 1 — Home, design system e navegação
1. Ajustar identidade visual com hero editorial responsivo, hierarquia de títulos, 4 KPIs claros, resumo das etapas e melhor espaçamento.
2. Melhorar navegação lateral sem remover páginas, mostrar status da sincronização e a hipótese de partida como provisória.
3. Respeitar leitores de tela (contraste e labels), evitar títulos cortados e conteúdo que transborde em desktop ou mobile.
4. Não alterar mapas, cálculos, origem das fontes nem dados financeiros.
5. Entregar commit, resultados de testes e URL. Pedir ao usuário confirmação visual e funcional antes da Fase 2.

### Fase 2 — Mapa e destinos
1. Resolver sobreposição de etiquetas; exibir cidades por categoria/estado, filtros que realmente funcionam, seleção com foto e ficha do destino.
2. Separar explicitamente `proposto`, `em avaliação`, `opcional`, sem sugerir visita confirmada.
3. Testar filtros vazios e layout mobile. Gate: aceite do usuário.

### Fase 3 — Roteiro e cronograma
1. Criar timeline visual com destinos, trechos e blocos de férias vs. trabalho remoto.
2. Consumir o cronograma sincronizado, distinguir datas fixas, hipóteses e pendências; não simular horários de viagem.
3. Testar atualização por Drive, fallback e ordem Itália → França. Gate: aceite.

### Fase 4 — Orçamento
1. Criar visão gerencial: custo por categoria, orçamento por casal, margem, alertas, cenários 60/70 mil e sensibilidade de câmbio/aluguel.
2. Partir das premissas do `.xlsm`; manter reserva emergencial incluída, evitar dupla contagem e sinalizar divergências e números não cotados.
3. Testar consistência com Excel e casos de extrapolação de teto. Gate: aceite.

### Fase 5 — Comparador das cidades francesas
1. Cartões para Mulhouse, Strasbourg, Metz e Nancy; ranking ajustável com pesos claros, evidências e data de preço.
2. Nunca tratar ranking histórico como cotação atual; não escolher cidade automaticamente.
3. Testar ausência de dados, pesos e atualização de decisão aprovada. Gate: aceite.

### Fase 6 — Pesquisas, acompanhamento e acabamento
1. Exibir decisões, evidências, tarefas P0–P3, alterações recentes e links de origem com estados.
2. Revisar responsividade, acessibilidade, performance, cache e mensagens de erro sem vazamento de secrets.
3. Gate final: validação visual desktop/mobile, testes automatizados e smoke test de sincronização.

## Protocolo de validação de CADA fase
- Executar `python -m compileall` e `python -m unittest discover -s tests -v` com resultado documentado.
- Se houver ferramentas e ambiente adequados, realizar teste visual desktop/mobile; senão declarar explicitamente que a verificação visual depende do usuário.
- Conferir que status `live` das três fontes continua disponível, que o snapshot continua possível e que os valores do Excel são preservados; quando não houver credencial de teste, não alegar que a integração foi exercitada ao vivo.
- Publicar somente arquivos alterados, sem credenciais, criar commit descritivo, conferir SHA e mostrar link do commit.
- Após cada fase, resumir: o que mudou, o que não mudou, testes aprovados, limitações e a checklist manual de 2–4 passos para o usuário.
- **PARAR** depois de cada fase; continuar apenas depois que o usuário declarar que aprovou ou pedir ajustes.

## Início imediato
Executar **somente a Fase 0 e a Fase 1**. Não iniciar as Fases 2–6 neste ciclo.