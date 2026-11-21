# UX 7.5 — Uma experiência de salvamento, nuvem privada primeiro

## Objetivo
O planejamento de viagem não deve exigir que o usuário administre SHA, commits, versões ou arquivos JSON no cotidiano. A fonte principal de persistência deve ser o arquivo completo de continuidade em **Google Cloud Storage privado**, com o GitHub público como publicação avançada separada.

## Descobertas verificadas no código
- `continuity_ui._private_archive` combina TripPlan, favoritos, interesses/wishlist, grupos, estudos, propostas e contexto.
- `PrivateArchiveStore.save` usa `ifGenerationMatch` com geração do objeto GCS, impedindo sobrescrita concorrente.
- `save_private_now` só confirma status após resposta do GCS com geração válida e atualiza fingerprint das decisões persistidas.
- `restore_private_on_start` recupera o GCS em sessões autenticadas antes da criação dos widgets; `_recover_saved_plan` ainda carrega um plano legado do GitHub se houver.
- Antes da mudança, a tela `itinerary_flow_ui._save_panel` promovia o GitHub público e mostrava controles de SHA/conflito para todos os usuários.

## UX implementada
1. Principal: **Salvar minha viagem**, status simples de nuvem privada e opção explícita de salvamento automático privado. Não é possível confundir login Google com nuvem privada configurada.
2. Avançado: JSON para exportação/importação manual e GitHub público para publicação opcional separada, mantendo autorização por operação.
3. Estado de planejamento passa a priorizar a confirmação da nuvem privada, não o snapshot do GitHub público.
4. Falhas ou conflitos preservam a versão local e não geram declaração falsa de sucesso.
5. Nenhuma gravação pública é ativada pela opção de autosave privado. O autosave GitHub legado foi desativado, inclusive para flags antigas ainda presentes na sessão; publicação pública permanece somente manual.

## Caminho de migração seguro
- Quando o owner possui um plano legado vindo do GitHub e GCS configurado, o primeiro **Salvar minha viagem** cria o arquivo privado completo no GCS; não apaga o arquivo público nem seu histórico.
- Se uma cópia GCS já existe e outra sessão alterou sua geração, o save é bloqueado por concorrência: nunca forçar overwrite.
- Sem `ux36_private_storage.bucket` e `gcp_service_account` nos Streamlit Secrets, a interface informa que o armazenamento privado está indisponível e não afirma que salvou.
- Verificar e configurar IAM, conta proprietária e bucket no ambiente da aplicação **separadamente**, antes de considerar a migração operacional concluída.
- Somente após validar recuperação privada numa nova sessão é seguro discutir desativar publicação legada; não retirar backups ou histórico nesta etapa.

## Testes e revisão obrigatórios
- Configuração indisponível; plano igual já confirmado; alteração local; escrita bem-sucedida; falha de API; 409/412 GCS; opt-in/autosave desativado por padrão.
- Confirmar ausência de chamadas `_secure_save` no botão primário e ausência de credenciais nos logs.
- Teste visual/Streamlit de áreas Itália e temporada europeia, login/logout e retorno à sessão.
- Suíte completa CI, lint/sintaxe e contratos de dados antes de merge.

## Critérios de aceite
- O usuário sabe se a viagem foi realmente salva na nuvem privada.
- A opção principal não solicita aprovação para publicar em repositório público.
- O controle de versão GCS não permite sobrescritas silenciosas.
- O JSON é apenas ferramenta de recuperação e permanece recolhido.
- O GitHub público não recebe gravações automáticas como resultado deste fluxo.
- O PR não altera segredos, infraestrutura ou dados de produção sem autorização e validação.
