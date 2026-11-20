# PROMPT DE IMPLEMENTAÇÃO — UX 6.5

**Situação:** apenas especificação para revisão; **não implementado**.
**Prioridade:** P0
**Dependência:** Pode ser implementado em paralelo após alinhar projeção de UX 6.1; rebase antes de implementação.

## Papel do agente
Atue como Staff Software Engineer, Senior Python/Streamlit Engineer, UX/Product Engineer e Data Integrity Reviewer.

## Objetivo
Criar uma experiência de salvamento e recuperação fácil de entender para wishlist e roteiro, sem confundir login Google, armazenamento privado GCS e publicação pública no GitHub.

## O que implementar
1. Auditar e documentar operações existentes de UX502 lista, continuity_ui, continuity_archive_model, private_continuity_store.py, sidebar_account_ui.py, _secure_save() e fluxo público GitHub. Distinguir claramente três coisas: **login OIDC Google**, **cópia privada em GCS**, **publicação deliberada no GitHub público**. Login ≠ autorização adicional do bucket ≠ salvamento confirmado.
2. Criar um painel único de status de armazenamento, calculado de confirmação efetiva do servidor e fingerprints de arquivo/lista/plano. Exibir estado por tipo: 'Alterações nesta sessão', 'Salvo no espaço privado', 'Falhou — exporte backup', 'Conflito de versões', 'Nuvem não configurada'.
3. Priorizar botão 'Salvar minha viagem em espaço privado', preservando o arquivo versionado que contém TripPlan, wishlist, estudos, calendário e agrupamentos; não criar novo esquema independente sem justificação e plano de migração. Salvar apenas interesses também deve continuar seguro e explícito.
4. Manter a exportação JSON local e restauração com preview/consentimento antes de substituir a sessão. Em caso de falha, conservar a sessão e oferecer backup sem alegar persistência.
5. A gravação em GitHub público deve permanecer avançada, identificada como PUBLICAÇÃO PÚBLICA, sempre com consentimento explícito e sem mudar por acidente a versão privada ou o TripPlan.
6. Diagnóstico: manter os detalhes técnicos seguros no log interno (classe de erro, estágio, status HTTP, identificador de correlação, sem tokens, e-mails, JSON privado, credenciais), mas mensagem prática para usuário; diferenciar erro de validação de destino, falha GCS, 403/404, 409/412 conflito, autenticação e timeouts.
7. Revisar falhas anteriores: destino suplementar (Obernai) rejeitado na serialização; fluxo 404 '/api/v2/subdomain/user/details' NÃO deve ser atribuído ao save sem evidência de origem; relatar como hipótese externa não comprovada. Não desabilitar validações para 'fazer funcionar'.
8. Preservar mecanismo de gerações GCS (optimistic concurrency) e isolamento por proprietário; nunca sobrescrever arquivo remoto com versão diferente, nem fazer retry silencioso que destrua mudanças.
9. Mensagens de Google conectado/conta autorizada não devem induzir a achar que o arquivo foi salvo no Drive; o projeto utiliza GCS privado.

## Pontos atuais
- continuity_ui.py (save_private_now, restore_private_on_start, autosave_private_if_requested)
- continuity_archive_model.py
- private_continuity_store.py, sidebar_account_ui.py
- ux502_destination_interests_ui.py / ux502_destination_interests_model.py
- travel_advisor_ui.py (autenticação e operações de GitHub)
- app.py / st.secrets

## Critérios de aceite e testes
- Sessão autenticada com lista de 6 (incluindo Obernai) + zero passeios; salvar GCS mock confirmado → sessão nova restaura lista e os metadados corretos.
- Alterar prioridades e incluir passeio → salvar → restaurar respeita revisões, não duplica, não perde preferências.
- Falha de bucket, credencial, token, HTTP 403/404, timeout, archive inválido, excesso de tamanho, conflitos 409/412 → mensagem clara; sem sucesso falso ou perda de dados.
- 404 externo não relacionado não é erroneamente atribuído a GCS; instrução de diagnóstico por URL e origem.
- GitHub público nunca recebe dados da lista/roteiro sem confirmação expressa. Testes de segurança e regressão da autenticação.
- Auditoria explícita de UX para desktop/mobile e acessibilidade, backups locais, rotas e renovação de sessão.

## Contexto e regras obrigatórias
Repositório: https://github.com/clevertondecker/europe-trip
Produto: Nossa Europa 2027 (Streamlit/Python), lua de mel na Itália + temporada europeia.
Este PR foi aberto **somente com este prompt**, para review do escopo. Ainda não há implementação funcional. Após aprovação explícita, implementar **nesta branch** e executar testes/CI. Não fazer merge de PR apenas documental.
- TripPlan continua a única fonte autoritativa de passeios confirmados no plano; preferências e pesquisas não são reservas.
- Preservar IDs existentes, compatibilidade de dados/arquivos, isolamento de fontes, fluxos de autenticação, regressões e segurança.
- Sem inventar custos, trens, horários, disponibilidade de 2027, fotos/licenças ou estado de decisão.
- Evitar novos editores paralelos, duplicação de estado de Streamlit e alterações não solicitadas no planejamento oficial.
- Verificar os contratos e os testes existentes antes de editar; adicionar testes de domínio + AppTest; testar troca de etapa Itália/França, restauração, navegação e histórico onde aplicável.
- Rever a branch contra main antes de implementar, pois estes cinco PRs são independentes e poderão ser executados sequencialmente.
- Entregar implementação + explicação da UX + testes + riscos e limitações. Não fazer merge até revisão e autorização posteriores.
