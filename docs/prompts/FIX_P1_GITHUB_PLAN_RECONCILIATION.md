# Nossa Europa 2027 — FIX P1 · Reconciliação de planos entre sessão e GitHub

**Objetivo:** resolver o conflito de salvamento mostrado após o PR #172, sem remover o bloqueio de concorrência e sem perder alterações locais.

## Evidências do código antes da mudança
- `continuity_ui.apply_pending_restore` e `restore_private_on_start` removem a referência `advisor_github_sha`, deliberadamente separando backup privado de publicação pública.
- `trip_plan_repository.GitHubPlanRepository.save` compara SHA recebido com o remoto e rejeita SHA ausente/stale quando o mesmo `plan_id` já existe.
- A UI orientava baixar backup e comparar, mas não disponibilizava uma comparação efetiva nem confirmação controlada para publicar o rascunho reconciliado.

## Implementação
1. Preservar as cópias locais e jamais adotar automaticamente um SHA remoto após importação.
2. Adicionar comparação explícita de versões com contagem e detalhes por campo de `TripPlan`, incluindo passeios, atrações, datas e preferências; comparação somente leitura.
3. Mostrar revisões local/remota e fornecer download do JSON remoto para segurança. O backup local segue disponível no fluxo existente.
4. Exigir confirmação específica e informada antes de publicar os dados locais no GitHub público. Nenhuma ação automática.
5. Ao confirmar, preparar cópia local com revisão `max(local, remote)+1`, sem alterar o estado da sessão antes da resposta remota.
6. Continuar usando `GitHubPlanRepository.save` para verificar novamente o SHA no momento da gravação, rejeitando corrida e mantendo o rascunho se ocorrer outra alteração remota.
7. Após sucesso confirmado, atualizar snapshot/SHA de sessão e o `TripPlan`; invalidar status do armazenamento privado, pois essa publicação pública não confirma o save privado.
8. Não incorporar automaticamente os campos exclusivos do GitHub: a ação é **publicar meu local** após revisão, não uma mesclagem semântica automática.

## Testes e qualidade
- Planos iguais, destinos/passeios/datas divergentes, revisões diferentes, IDs incompatíveis, preview obsoleto, corrida de SHA antes do PUT e conflito 409 no PUT.
- Garantir que análise e preparação não alterem a cópia original.
- Executar a suíte da pipeline e revisar riscos de UI/Streamlit, autenticação e consentimento.
- Abrir PR separado, sem merge antecipado.

## Fora do escopo
- Alterar o formato persistido, automatizar resolução de conflitos, sincronizar GCS com GitHub, salvar plano privado no repositório público ou modificar outras páginas do produto.

## Critério de aceite
Um backup local de um plano cujo ID já está salvo no GitHub pode ser comparado e publicado **apenas após autorização explícita**. Uma gravação concorrente rejeita a publicação sem alterar a cópia local.

## Revisão de integração após captura de tela
- A tela **Etapa 2 · Temporada europeia / Salvar e recuperar planejamento** é renderizada por `itinerary_flow_ui._save_panel`, não por `travel_advisor_ui.render_advisor`.
- O fluxo de comparação e confirmação foi integrado também ao painel real e fica restrito ao proprietário autenticado.
- Quando mais de 100 campos diferem, o resumo é incompleto e o botão de publicação permanece desabilitado; os arquivos JSON podem ser baixados para revisão completa.
- O PR não deve ser integrado antes de CI verde e revisão de segurança/Streamlit.
