# Roadmap UX 3.6–3.10 — auditoria e revisão cruzada

**Status:** PROPOSTAS PRELIMINARES · pendentes de revisão UX independente e revalidação após UX 3.5 real  
**Controle:** [issue #40](https://github.com/clevertondecker/europe-trip/issues/40) · [coordenação de agentes](../AGENTS_COORDINATION.md)  
**Base de pesquisa:** `main` commit `4653e62213b39fc472fa3a712fcc083a45abc34d` (UX 3.4), 15/11/2026.

> A UX 3.5 não estava implementada na `main` na auditoria inicial. O calendário inteligente é uma **hipótese de base** retirada de `docs/UX_3_5_IMPLEMENTATION_PROMPT.md`. Não considerar as telas da UX 3.5 como existentes sem confirmar em código/testes.

## Problemas identificados no código atual

| Evidência | Efeito na experiência | Candidato |
|---|---|---|
| `city_decision_ui.py` documenta rascunhos apenas em `st.session_state` e JSON; issue #30 | Perda do estudo ao mudar de sessão/dispositivo, mesmo após longas pesquisas | UX 3.6 |
| `planning_status.py` distingue alteração local/remota; `trip_plan_repository.py` é acoplado ao GitHub | Usuário precisa compreender persistência e consentimento público para continuar | UX 3.6 |
| `base_coverage_model.py`, `base_weight_coverage_ui.py` e `outing_cost_evidence.py` expõem numerosas lacunas documentais; `ux_navigation.py` preserva páginas de pesquisas e decisões separadas | Informação correta, mas dificuldade de saber o próximo passo que move a viagem adiante | UX 3.7 |
| `advisor_finance.py`, `unified_budget.py` e `finance_margin_metrics.py` modelam provisões e custos conhecidos; `city_decision_ui.py` isola aluguel hipotético | Difícil comparar custo planejado, orçamento, cotação recente e pagamento efetivo | UX 3.8 |
| `app.py` contém 1800+ linhas e mapeamentos de navegação; `ux_navigation.py` tem adaptador legado; `README.md` ainda descreve layout antigo | Risco de excesso de rolagem, navegação inconsistente e fluxos que funcionam apenas no AppTest | UX 3.9 |
| `calendar_model.py`, `travel_optimizer.py` e a especificação da UX 3.5 ainda requerem harmonização | Evitar refazer o calendário sob outro nome depois da 3.5 | **Exclusão transversal** |

A auditoria da **interface visual real** permanece pendente: não foi possível acessar o site Streamlit pelo navegador disponível. Nenhum resultado descrito aqui equivale a sessão de usabilidade observada.

## Propostas e gates

| Versão | Hipótese | Estado | Dependência | Stop rule |
|---|---|---|---|---|
| **3.6** | Retomar estudos com segurança entre sessões e dispositivos | Rascunho A | UX 3.5 validada; arquitetura privada + custo aprovados | Não lançar se depender de salvar dados pessoais no repositório público |
| **3.7** | Pendências acionáveis no contexto da decisão | Rascunho A | 3.5 + inventário de fontes | Descartar se 3.5 entregar fluxo equivalente e medido |
| **3.8** | Do orçamento estimado às cotações e compromissos | Rascunho A | Modelo financeiro e regras de fonte | Descartar dashboards paralelos ou preço sem evidência |
| **3.9** | Consistência, acessibilidade e usabilidade mobile | Rascunho A | fluxos 3.5–3.8 para teste | Não criar área funcional nova só para "melhorar UX" |
| **3.10** | **Não proposto** | Aguardar evidência | pós-3.9 | Se não houver problema de usuário mensurável, encerrar no 3.9 |

## Processo de dupla revisão

- **A — Engenharia/produto:** cria a hipótese a partir do diff atual, documentação e testes. Cada prompt tem contexto, implementação, contratos, métricas e alternativa mais simples.
- **B — Revisor especializado em UX:** lê o documento, avalia jornada sem conhecimento técnico, custo de interação, linguagem, consistência, falhas, prevenção de erro, privacidade, responsividade e acessibilidade. Registra aprovação ou devolução na issue #40 com referência ao **SHA do arquivo**.
- **Conciliação:** A corrige os pontos, B relê a nova versão; somente com `ACEITE_A` e `REVISÃO_B: APROVADO` do **mesmo SHA** uma proposta passa a `FINALIZADA`. Antes disso, status é `EM REVISÃO`.
- **Auditoria da 3.5 real:** ao detectar merge, rever todos os prompts para evitar duplicação. Um escopo pode ser diminuído, reordenado ou cancelado.
- **Implantação:** essa rotina cria **propostas de implementação**, não código de implementação. PRs de funcionalidades continuam separados, com testes/CI/autorizações.

## Heurísticas de aceite de UX

- Leigo consegue explicar o efeito de cada ação antes de clicar.
- No máximo 4 áreas principais; não aumentar 3 tarefas de `Meu roteiro`. Usar estado/contexto existente.
- Nenhuma alteração em `TripPlan` sem revisão e confirmação. Cotas, fontes e reservas não são confundidas.
- A mesma tarefa deve ser executável no celular e no desktop, com teclado e leitor de tela.
- Retornar de pesquisa/orçamento ao mesmo contexto em **uma ação** quando a origem ainda existir.
- Para novas jornadas, medir número de cliques, mudanças de área, recuperação de erro e compreensão da consequência da ação; definir baseline observável (AppTest + teste manual) em vez de inventar porcentagens de melhoria.
- Preferir **simplificação** ou exclusão de ferramentas duplicadas a mais cards, abas ou painéis.

## Arquivos que não devem ser alterados por essas propostas

Sem edição de `app.py`, `planning_session.py`, `TripPlan`, `OAuth/Secrets`, `unified_budget.py` ou arquivos de agentes. O integrador realiza futuramente qualquer alteração compartilhada, somente após autorização e testes. Sem escrita em arquivos oficiais do Drive.

**Observação:** duas rotinas automatizadas podem atuar como auditor e revisor em execuções distintas; isso não corresponde a revisão humana nem comprova acesso a um navegador real. Registrar resultados somente após execução bem-sucedida.
