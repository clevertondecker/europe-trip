# UX 3.6 — Resiliência do salvamento privado

**Problema:** o código de autosave consumia `ux36_cloud_dirty` via `pop` antes de uma confirmação da geração GCS. Em falhas temporárias isso apagava o sinal de alterações pendentes.

**Correção:** mantém dirty até resposta remota confirmada; armazena a impressão digital da tentativa falha apenas em sessão para impedir repetição a cada rerun; uma edição diferente libera nova tentativa. Clique manual **Salvar cópia privada agora** força nova tentativa. Conflito não sobrescreve outra sessão; generation/ifGenerationMatch existente permanece. Sem novos Secrets, bucket ou serviço.

**Aceite:** teste simulado de rede, conflito, opt-out, mudança posterior e sucesso. Testar em navegador com duas sessões autenticadas antes de considerar concorrência E2E verificada. Exportação JSON mantém fallback.

**Sem merge/deploy.**
