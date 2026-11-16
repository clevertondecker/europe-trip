# UX 3.6 — Prompt final de implementação e configuração

## Objetivo
Permitir que o proprietário autenticado retome o planejamento do Nossa Europa 2027 no Streamlit, em outro dia ou dispositivo, sem baixar e importar JSON a cada visita. Preservar o backup JSON manual, a revisão de diferenças e o plano oficial `TripPlan`, sem publicar estudos privados no GitHub.

## Implementação
- Partir de `feature/ux36-safe-continuity-foundation`, preservando a exportação/importação segura e revisão antes da restauração.
- Armazenar o mesmo arquivo de continuidade validado em um **bucket privado GCS dedicado**, com chave derivada de SHA-256 do e-mail do proprietário autenticado.
- Exigir `_owner_signed_in()` e credencial de serviço do Streamlit antes de qualquer leitura ou escrita privada. Não aceitar identidade ou caminho do browser.
- Recuperar somente no início de uma sessão autenticada, antes da renderização dos widgets. Recuperação manual de JSON tem prioridade quando já ocorreu.
- Rascunhos de cidades/calendário nunca se tornam aprovações do plano oficial, nem são gravados no GitHub público.
- Aplicar `ifGenerationMatch` em toda gravação GCS; criar somente se o objeto não existe (`0`). Em conflito, **não** sobrescrever e exigir comparação/backup.
- Disponibilizar botão de salvar e opt-in para salvar **após mudanças confirmadas no `TripPlan`**. Nenhum write por tecla digitada. Se falhar, informar que os dados só estão na sessão; JSON permanece acessível.
- Desabilitar a sincronização quando login, bucket ou credencial não estiverem configurados, sem impedir o uso offline/local.
- Verificar testes unitários, regressão AppTest e comportamento em dispositivo novo antes de mesclar.

## Configuração obrigatória no Streamlit Cloud
1. Criar bucket GCS **privado** dedicado, com *Public Access Prevention* enforced e *Uniform bucket-level access* ativo. Evitar ACLs e exposição pública. Recomendado ativar **Object Versioning** para recuperação administrativa.
2. Conceder à conta de serviço existente em `[gcp_service_account]` acesso de leitura/gravação **somente nesse bucket**, com privilégio mínimo; não compartilhar a chave em código ou PR.
3. Acrescentar apenas o identificador do bucket nos Streamlit Secrets:

```toml
[ux36_private_storage]
bucket = "SEU_BUCKET_PRIVADO"
```

4. Manter `[auth]`, `[auth.google]`, `[advisor_github].owner_email` e `[gcp_service_account]` configurados na interface de Secrets (nunca no GitHub). O e-mail do proprietário deve ser o mesmo autenticado pelo login Google.
5. Reiniciar a aplicação, autenticar, salvar uma cópia privada e reabrir **em nova sessão**. Testar duas abas/dispositivos; uma atualização concorrente deve informar conflito e preservar os dados.

## Limitações e condições de aceite
- O autosave é **opt-in** e se aplica a **commits confirmados do plano**, não a cada filtro ou rascunho transitório. O botão de salvar inclui rascunhos compatíveis e contexto atual.
- Não há armazenamento privado ativo **até o administrador configurar bucket/IAM/Secrets**. Não indicar “Salvo” em caso de falha.
- O histórico de versões do bucket, se habilitado, é administrativo: esta UX não implementa um navegador de versões na nuvem.
- Nenhuma reserva, pagamento ou cotação é executada pela recuperação.
- Com bucket desconfigurado, a UX 3.6 permanece como portabilidade JSON local.
- Não mesclar antes de CI verde e teste manual de identidade/restore/concorrência em Streamlit Cloud.
