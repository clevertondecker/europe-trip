# UX 6.5 — Salvamento como responsabilidade transversal da viagem

**Status:** PROMPT REVISADO; sem implementação. **Prioridade P0 (integridade/confiabilidade)**.
**Veredito adversarial:** REDESENHAR. Um painel de salvamento é útil como detalhe/recuperação, mas não deve virar aba obrigatória nem nova etapa de viagem.
**Dependências:** pode iniciar auditoria técnica já; integrar projeção UX 6.1 e evolução de contrato UX 6.2 após ambas serem revisadas. Não misturar atualização do schema do TripPlan com uma refatoração do armazenamento sem migração e rollback separados.

## Papel
Atue como Principal Product Designer, Staff Security/Backend Engineer, Senior Streamlit Engineer e Data Persistence Reviewer.

## Experiência recomendada
Um **indicador global discreto** sempre visível nas três áreas **Explorar, Planejar e Orçamento**, ligado ao estado efetivo da cópia privada, com ação `Salvar minha viagem` quando necessário. Estados compreensíveis:
- `Alterações somente nesta sessão` — ainda não confirmadas remotamente.
- `Salvo no espaço privado` — GCS confirmou gravação da **mesma versão/fingerprint** atual.
- `Salvando…` somente durante ação de gravação em curso.
- `Falha ao salvar — exporte backup` — preserva rascunho, nunca afirma sucesso.
- `Outra sessão alterou a viagem` — conflito, oferecer opções seguras de comparar/restaurar.
- `Espaço privado não configurado` — login Google pode estar ativo, mas bucket/credencial não disponível.
- `Não autenticado` — apresentar login/backup sem alegar persistência.

**Não** exigir que o usuário atravesse uma página de `Salvamento` para prosseguir. Ao clicar no status, abrir painel contextual com data da última confirmação, tipo de backup, `Salvar agora`, `Baixar backup JSON`, `Ver/restaurar versão` se houver versão verificável, e explicação dos serviços. Never show "salvo" only because Google OIDC is authorized.

## Arquitetura e regras
1. **Três camadas distintas:** (i) login/OIDC Streamlit Google para identificar owner, (ii) GCS privado com service account e bucket configurado e isolamento por usuário, (iii) GitHub público com consentimento específico de publicação. Não chamar GCS de `Google Drive`. Não publicar dados privados por engano em GitHub.
2. Único arquivo de continuidade versionado deve incluir TripPlan, wishlist, estudos, calendário, agrupamentos, contexto e valores aplicáveis. Reutilizar `continuity_archive_model.make_archive`, `validate_archive`, `continuity_ui.save_private_now`; não criar `wishlist_save.json` paralelo nem cópias silenciosas.
3. **Default: salvar manualmente**, com um botão claro `Salvar minha viagem`. Autosave privado só após opt-in explícito, com limitação de frequência, escrita idempotente, controle de versão e possibilidade de desativar; sem escrita automática no GitHub público. Não habilitar via mera navegação.
4. Confirmar sucesso **somente** depois da resposta de `PrivateArchiveStore.save` e generation validada; recalcular fingerprint a partir do arquivo efetivamente gravado e refletir alterações posteriores. Se a escrita falhar após preparar JSON, preservar `advisor_plan`, `ux502_interests`, calendário e geração conhecida.
5. Continuar usando `ifGenerationMatch` do GCS e optimistic concurrency: 409/412 → não sobrescrever, não perder alteração, oferecer `Recarregar e comparar` e `Exportar minha versão`, com revisão antes de substituir.
6. **Recuperação**: preview de diferenças (plano, destinos, prioridades, datas, grupos) antes de restaurar; ação explícita de confirmação. Não substituir planos diferentes/versões sem comparação. Tratar arquivo legado que não possui wishlist; validar arquivo com novos destinos e, após UX 6.2, novas visitas de zero atrações sem aceitar IDs arbitrários.
7. Tamanho e schema: preservar o limite atual de 450k bytes (ou justificar aumento com teste de custo e segurança), `ARCHIVE_SCHEMA=1` atual quando não houver necessidade de versão; qualquer mudança deve ter parser retrocompatível + migração explicitada, fixture e rollback.
8. **Diagnóstico sem vazamento**: categorizar (a) validação local de cidade/arquivo, (b) indisponibilidade de bucket/credencial, (c) falha de sessão/owner, (d) HTTP 403/404/timeout no endpoint **storage.googleapis.com** de metadados/upload, (e) conflito 409/412, (f) resposta de sucesso divergente. Mostrar mensagem prática e um identificador local opcional, sem expor tokens, e-mails, IDs do bucket, segredo, conteúdo do arquivo, contatos ou payload de viagem em log público.
9. O `404 /api/v2/subdomain/user/details` apresentado anteriormente não é prova de falha GCS: o caminho do storage é `storage.googleapis.com/storage/v1` e `/upload/storage/v1`. Checar **origem** da solicitação antes de atribuir causa. Não adicionar workaround de permissão baseado nesse 404 externo.
10. Ação `Publicar no GitHub público` deve ficar em **Ferramentas avançadas**, com consentimento inequívoco por operação e explicação do que ficará acessível. **Nunca** confluir `Salvei minha viagem` com `Publiquei o planejamento`.
11. Status por objeto/escopo: o arquivo privado inclui múltiplos tipos de dado. Se salvou somente uma exportação JSON no navegador, status é `Backup baixado`, não `Nuvem confirmada`. Se plano mudou desde a última geração, status volta a `Alterações somente nesta sessão`.
12. Após login/logout e novas sessões, restaurar em momento seguro do Streamlit (antes da criação de widgets), sem sobrescrever um draft local modificado durante render. Confirmar GCS independente da UI.

## Comparação das opções
**A — incremental:** novo painel com botões separados para wishlist e roteiro em cada aba. Pouca mudança, mas perpetua incerteza e duplicação.
**B — recomendada:** indicador transversal + controle contextual de `Salvar minha viagem` + recuperação/backup em painel secundário, reutilizando o arquivo versionado. Não criar uma tela obrigatória.

## Gate P1 — Estado de salvamento baseado em decisões, não na aba atual

### Problema reproduzível por inspeção do código
- `continuity_ui._private_archive()` inclui `continuation` com `area`, `section`, `search`, `stage`, semana e destino ativo.
- `continuity_ui._archive_fingerprint()` ignora somente `exported_at`. Logo, um contexto de navegação diferente pode alterar o hash integral **sem mudar decisões da viagem**.
- `render_private_controls()` compara o fingerprint do arquivo completo, enquanto `private_status_label()` verifica o hash do TripPlan e `ux36_cloud_dirty`. Essa diferença permite indicadores conflitantes, sem demonstrar que houve erro GCS.

### Contrato do novo indicador
1. Definir função pura `decisions_fingerprint(archive)` (nome sugerido) que englobe **todos os dados persistíveis de usuário**, incluindo `plan`, `destination_interests`, `city_favorites`, `weekend_groups`, estudos e propostas incluídos efetivamente no arquivo. Excluir exclusivamente o contexto de navegação transitório (`continuation`) e metadados voláteis (`exported_at`); não excluir itens só porque não estão no TripPlan.
2. **Separar identidades:** `saved_decisions_fingerprint` alimenta `Salvo` / `Alterações nesta sessão`; `saved_archive_fingerprint` identifica os bytes/snapshot completos efetivamente enviados e auxilia restauração/conflitos; `GCS generation` é prova do servidor, nunca calculada localmente.
3. Unificar `render_private_controls()`, `private_status_label()` e indicador global sob a **mesma projeção pura** de status, incluindo falha/conflict e disponibilidade do backend. Evitar que flag residual `ux36_cloud_dirty` crie falsa divergência quando os dados atuais equivalem à versão confirmada; também não declarar sucesso só porque a flag está falsa.
4. Navegar, filtrar, buscar, trocar aba, visualizar mapa/comparação ou mudar destino ativo **sem editar decisões** não marca a viagem como alterada, não ativa autosave e não provoca POST GCS. Quando o usuário salvar por uma alteração real, registrar contexto da sessão naquele snapshot. Se desejar retomada da *última aba vista* mesmo sem edições, tratá-la explicitamente como conveniência opcional separada, não como dado de roteiro não salvo.
5. Salvar uma lista de interesses via botão existente usa o mesmo arquivo completo. Se algum conteúdo efetivamente incluído no arquivo mudar (como estudos persistíveis), o status deve refletir alteração. Backup baixado continua distinto de geração GCS confirmada.
6. Em nova sessão, validar que o indicador aparece salvo somente após recuperar GCS + hash válido. Recalcular após qualquer importação manual, decisão de atualização, alteração de grupo/estudo, e reconciliação de plano.

### Testes de regressão
- **GIVEN** arquivo completo confirmado em GCS **WHEN** navego por Explorar, Planejar, Orçamento, mudo busca, filtros, semana ou vista de mapa **THEN** status permanece `Salvo no espaço privado`, não há dirty e POST GCS = 0.
- **GIVEN** alterações em destinos/prioridades, visitas, datas, grupos, favoritos ou estudo realmente persistido **WHEN** comparo **THEN** status muda para `Alterações nesta sessão` e permanece até novo GCS acknowledgement.
- **GIVEN** dois widgets de status legados e o indicador global **WHEN** altero somente contexto ou dados **THEN** exibem a mesma classificação derivada.
- **GIVEN** resposta GCS falha ou retorna conflito **WHEN** salvo **THEN** dados locais persistem na sessão; hash não é marcado como confirmado.

## Gate P1 — Prévia fiel de restauração do arquivo completo

`continuity_archive_model.preview_restore()` atualmente compara principalmente campos de `plan`; o arquivo inclui também `destination_interests`, `city_favorites`, `weekend_groups`, `city_studies` e `calendar_drafts`. Uma wishlist pode mudar sem alterar o `TripPlan`, e a prévia não deve anunciar `Nenhuma diferença` nesse caso.

1. Calcular diff **estruturado e inteligível** para plano, destinos desejados (adicionados, removidos, prioridades alteradas), grupos de fim de semana (incluindo datas), favoritos, estudos e propostas persistíveis; preservar IDs e limitar o detalhamento da UI, com expansão e contagens para muitos itens.
2. Prévia é somente leitura; ação `Confirmar substituição` é explícita, mantendo verificações de `plan_id`, revision, geração remota e fingerprints de arquivo corrente/entrante. Para evitar *TOCTOU*, comparar **dados persistíveis atuais**, não apenas `plan_fingerprint(current)`, imediatamente antes de substituir, pois wishlist/grupos podem ter mudado após abrir a prévia.
3. Não usar o contexto de aba como alteração relevante de decisão na prévia; contexto restaurado poderá voltar à última tela somente se a rota antiga for normalizada pelo #168. Reabrir destinação inexistente não pode invalidar todo o backup se os dados forem válidos: preferir fallback seguro de contexto, preservando diagnóstico.
4. Backups legados sem wishlist ou grupo usam valor padrão conforme contrato; apresentar isso como potencial diferença, não omitir alterações.

### Testes de restauração
- **GIVEN** TripPlan idêntico e wishlist distinta **WHEN** pré-visualizo a recuperação **THEN** a UI destaca entradas/prioridades que serão substituídas; não afirma `sem diferenças`.
- **GIVEN** a prévia foi aprovada e uma prioridade foi editada antes da confirmação **WHEN** confirmo **THEN** a aplicação rejeita preview obsoleto e pede revisão, sem modificar plano/lista atuais.
- **GIVEN** grupos diferem por data e o TripPlan é idêntico **WHEN** reviso **THEN** diferenças de grupos aparecem e a confirmação preserva geração/propriedade.
- **GIVEN** backup antigo de quatro áreas **WHEN** restauro no futuro UX 6.4 **THEN** o contexto é normalizado antes de validar sem fazer alterações no conteúdo do roteiro.

## Cenários Given / When / Then
- **GIVEN** owner logado + bucket configurado, wishlist de 6 incluindo Obernai, nenhum passeio **WHEN** salvo **THEN** GCS confirma geração e o indicador mostra `Salvo no espaço privado`, sem publicações GitHub; nova sessão restaura lista.
- **GIVEN** existe visita sem atrações no TripPlan (UX 6.2) **WHEN** salvo e restauro **THEN** IDs, zero atrações, datas e estado permanecem válidos; sem se converter em seleção fictícia.
- **GIVEN** altero prioridade ou crio passeio depois do último save **WHEN** volto ao painel **THEN** status regressa para `Alterações somente nesta sessão` até confirmação de nova geração.
- **GIVEN** apenas realizei login Google **WHEN** não há bucket/credencial **THEN** não aparece `Salvo`, há instrução de backup local.
- **GIVEN** outra sessão incrementou a geração GCS **WHEN** tento salvar **THEN** recebo conflito legível, não há overwrite/retry cego e posso exportar meu rascunho.
- **GIVEN** falha por 403/404/timeout na API GCS **WHEN** clico `Salvar` **THEN** o rascunho fica intacto e o status indica falha; não confundir com 404 externo do Streamlit.
- **GIVEN** não estou logado **WHEN** baixo JSON **THEN** backup local funciona, sem fingir gravação em nuvem.
- **GIVEN** arquivo remoto é de outro `plan_id` ou mais antigo **WHEN** peço restauração **THEN** vejo diffs e confirmo separadamente, sem perder a versão atual.
- **GIVEN** escolho publicar no GitHub público **WHEN** não marco ciência explícita dos riscos **THEN** operação de publicação fica indisponível.
- **GIVEN** opt-in de autosave privado **WHEN** edito repetidamente **THEN** existe debounce/limitação com confirmação real e recuperação de conflitos; desativar não apaga dados.

## Arquivos e testes
`continuity_ui.py`, `continuity_archive_model.py`, `private_continuity_store.py`, `ux502_destination_interests_ui.py`, `ux502_destination_interests_model.py`, `sidebar_account_ui.py`, `travel_advisor_ui.py`, `app.py`, `planning_session.py`, `ux_navigation.py`.

Teste unitário do status derivado de fingerprint+GCS generation; GCS mock owner+nonowner, 200/201, 403/404, 409/412, timeout, invalidez de JSON, limites de tamanho, login expirado, tentativas de acesso a objetos de outros owners, redaction de logs; AppTest do indicador global nas 3 áreas e ações de recuperação, retorno após logout/login. Export/import/roundtrip de arquivo completo, com/sem wishlist, visitas futuras de zero atrações e legado de schema. Testes negativos garantindo nenhuma chamada pública no fluxo privado e nenhuma afirmação de sucesso antes de confirmação. Validar mobile/acessibilidade.

## Direção transversal UX 6.0
Arquitetura-alvo **Explorar · Planejar · Orçamento**, jornada não linear, status progressivos de destino e visita, sem etapas obrigatórias de save ou seleção de atrações. Manter snapshots, preços/rotas não verificados como desconhecidos. Esta branch permanece prompt de especificação; implementar somente após revisão e rodar CI antes de qualquer merge.
