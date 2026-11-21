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
