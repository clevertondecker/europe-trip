# Prompt — UX 5.2: conta Google acessível na sidebar

## Papel
Atue como Senior Python/Streamlit Engineer, UX Designer e Security Reviewer no
repositório `clevertondecker/europe-trip`.

## Objetivo
Tornar o login/logout do Google descobrível em qualquer área do Nossa Europa
2027, sem mexer na autoridade do TripPlan nem nos mecanismos de persistência.

## Escopo
1. Na sidebar existente, abaixo da navegação e da sincronização, incluir
   seção **Conta Google** visível independentemente da página.
2. Desconectado: botão nativo **Entrar com Google** acionando `st.login("google")`.
3. Identidade proprietária validada: mostrar e-mail autorizado, status fiel do
   salvamento e botão **Sair do Google** chamando `st.logout()`.
4. Conta distinta, não verificada ou expirada: negar privilégios; mostrar aviso
   discreto e ação de sair. Não exibir dados privados.
5. OAuth não configurado: mostrar explicação segura, sem ação inoperante,
   sem expor `st.secrets`, tokens, cookie secrets ou detalhes internos.
6. Remover botões duplicados de login/logout das ferramentas avançadas.
   Manter o consentimento do repositório GitHub público, os botões de salvar,
   o controle `_owner_signed_in` e o acesso restrito.
7. Distinguir **autenticado**, **nuvem privada salva** e
   **Google Drive apenas leitura**. Não escrever "sincronizado" por mera sessão.
8. Preservar a navegação por quatro botões, o painel de sincronização existente
   e a seção `Fontes e ferramentas`.

## Critérios de aceite
- Sem Secrets: AppTest não falha e explica login indisponível.
- Usuário desconectado com OAuth configurado: uma ação `Entrar com Google`.
- Usuário proprietário verificado: e-mail e ação de sair; não repetir botões
  no restante da aplicação.
- Conta não autorizada/expirada: não aparece como proprietário e não pode
  salvar, recuperar ou gravar dados por conta própria.
- Login/logout não altera diretamente `advisor_plan`, `ux502_interests`,
  `main_navigation` nem estruturas de rotas/orçamento.
- Nenhum segundo login, token ou estado de autenticação.
- CI: `python -m compileall -q .`,
  `python tools/validate_research_data.py`,
  `python -m unittest discover -s tests -v`.
- Inspeção visual desktop/mobile em 1440×900 e 390×844. AppTest não prova layout.

## Não fazer
- Não implementar gravação no Google Drive. O serviço `drive_sync.py`
  permanece somente leitura.
- Não colocar informações pessoais no GitHub público.
- Não mudar orçamentos, TripPlan, decisões, datasets ferroviários,
  contratos de arquivos ou persistência privada.
- Não incluir chaves ou credenciais no repositório.

## Saída esperada
PR isolado na branch `feature/ux52-sidebar-google-account`, resumo de
arquivos, testes/CI e limitações. Somente merge após CI aprovado e revisão.
