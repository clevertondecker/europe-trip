# Habilitar salvamento de planos no GitHub (Google OAuth + Streamlit Secrets)

Status: **código preparado, credenciais de produção ainda precisam ser criadas pelo proprietário diretamente nas contas Google, GitHub e Streamlit Cloud**. Não habilitar gravação sem autorização validada. Em 15/11/2026, o repositório `clevertondecker/europe-trip` era **público**, portanto um JSON salvo em `data/user_plans/` será publicamente acessível.

## O que mudou

- A autenticação com senha e SHA-256 foi **descontinuada** por não ser adequada para proteger escrita num aplicativo web público.
- A nova interface exige login Google pelo mecanismo OIDC do Streamlit, identidade emitida pelo Google, e-mail verificado, sessão não expirada e e-mail idêntico a `advisor_github.owner_email`.
- Mesmo após login, salvar exige clique explícito e confirmação de que o repositório é público. Ausência de configuração desativa a escrita, preservando exportação/importação JSON.
- `trip_plan_repository.py` exige revisão por SHA para não sobrescrever conflitos de gravação.
- **A conta de serviço do Google Drive existente não é uma credencial de login OIDC.** Não a reutilize como OAuth Client.

## 1. No GitHub: criar token restrito

Abra https://github.com/settings/personal-access-tokens/new e crie um **fine-grained personal access token**:
1. Resource owner: a conta que possui o repositório.
2. Repository access: **Only select repositories**, selecionando exclusivamente `clevertondecker/europe-trip`.
3. Repository permissions: **Contents — Read and write**; Metadata Read pode ser automático. Não conceda Actions, Administration, Secrets etc.
4. Expiração curta, por exemplo 30–90 dias. Planeje rotação periódica.
5. Copie o token diretamente para o Streamlit Secrets, **nunca** para GitHub, chat, prints, logs ou o navegador da aplicação.

**Atenção:** o GitHub limita esse token ao **repositório**, não à pasta `data/user_plans/`. O código valida caminhos, mas não é uma restrição do token. Se quiser privacidade do itinerário, faça o repositório privado ou utilize um repositório privado separado para os planos (isso exigirá adaptar o código). Não coloque dados pessoais no JSON versionado de um repositório público.

## 2. Google Cloud: criar credencial de login OAuth

Abra https://console.cloud.google.com/auth/clients e selecione um projeto Google Cloud.
1. Configure a tela de consentimento / Audience, com tipo compatível com sua conta Google. Se usar modo Testing, adicione a própria conta Google como usuário de teste.
2. Crie um **OAuth client ID** para **Web application**.
3. Authorized redirect URI: `https://nossa-europa-2027.streamlit.app/oauth2callback`.
4. Guarde Client ID e Client secret diretamente no Streamlit Secrets.

A URI precisa corresponder exatamente à URL final hospedada. Para desenvolvimento local, configure `http://localhost:8501/oauth2callback` como URI adicional, caso seja necessário.

## 3. Streamlit Cloud: inserir os Secrets

Abra https://share.streamlit.io/ > encontre `nossa-europa-2027` > menu `...` > **Settings** > **Secrets**.

**Não substitua os Secrets que já existem, especialmente `[gcp_service_account]`. Acrescente as seções a seguir ao conteúdo atual.** Todos os exemplos são placeholders:

```toml
[auth]
redirect_uri = "https://nossa-europa-2027.streamlit.app/oauth2callback"
cookie_secret = "GERAR_ALEATORIAMENTE_COM_PYTHON"

[auth.google]
client_id = "SEU_GOOGLE_OAUTH_CLIENT_ID"
client_secret = "SEU_GOOGLE_OAUTH_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[advisor_github]
owner_email = "SUA_CONTA_GOOGLE_AUTORIZADA@example.com"
token = "SEU_FINE_GRAINED_GITHUB_TOKEN"
```

Gere um cookie secret aleatório no seu computador com:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Use uma conta Google com e-mail verificado, exatamente igual a `owner_email`. Não compartilhe client secret, GitHub token ou cookie secret com terceiros, incluindo assistentes em chat.

Após salvar, reinicie a aplicação se necessário. O app usa `streamlit[auth]>=1.66,<2` como dependência.

## 4. Teste de funcionamento

1. Abra https://nossa-europa-2027.streamlit.app/ e navegue até **Roteiro → Consultor inteligente**.
2. Crie ou importe um plano e entre com Google usando **Entrar com Google (proprietário)**.
3. Confira que somente a conta autorizada vê as opções de leitura/gravação.
4. Reconheça o aviso de que o repositório atual é público.
5. Clique **Gravar versão aprovada no GitHub**.
6. Confirme o novo arquivo JSON em https://github.com/clevertondecker/europe-trip/tree/main/data/user_plans .
7. Teste novamente com outro usuário: a gravação deve ficar indisponível.
8. Teste duas revisões, leitura, histórico e restauração local. Conflitos de SHA devem exigir recarregar.

## 5. Como desativar ou revogar acesso

- Remova `[advisor_github]` do Streamlit Secrets, ou remova `token` e `owner_email`: a UI volta ao modo exportação JSON.
- Revogue o token no GitHub imediatamente em caso de vazamento.
- Rotacione os segredos do Google OAuth/cookie quando necessário.
- Revise quem pode acessar/alterar o app no Streamlit Cloud e a visibilidade do repositório.

## Segurança e limitações

- O fluxo implementado não sincroniza decisões oficiais do Drive; D-004 continua separada.
- O login Google verifica identidade; não outorga acesso GitHub ao usuário final. O token armazenado server-side realiza a escrita como credencial do proprietário.
- A autenticação do Streamlit depende de OIDC e da configuração Google Cloud. Sem a configuração final do proprietário, esta documentação não é uma ativação efetiva.
- O deploy e os testes do CI não podem provar que os Secrets de produção foram salvos; confirme isso na interface Streamlit.
