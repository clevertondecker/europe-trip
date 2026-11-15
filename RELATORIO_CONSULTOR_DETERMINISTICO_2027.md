# Consultor inteligente sem LLM — implementação (15/11/2026)

## Como acessar
**Roteiro → Consultor inteligente** no Streamlit [Nossa Europa 2027](https://nossa-europa-2027.streamlit.app/).

Esta função adiciona regras e otimização determinísticas aos componentes já existentes, **sem integração com OpenAI/Gemini**.

## Funcionalidades
- Perfil padrão **Equilibrado**; alternativos **Economizar** e **Aproveitar ao máximo**. Pesos transparentes por interesse, custo, conforto e calendário.
- Importa a seleção de atrações em `st.session_state["explore_packages"]`, permite escolher outra base e gera diagnósticos com fontes e sugestões.
- Diferencia preços historicamente publicados, tarifas condicionais e custos desconhecidos; EUR e CHF só são agregados em BRL após câmbio hipotético informado.
- Analisa logística: retorno não verificado, Carte Fluo, trechos longos, Alpes/pernoite e falta de preços.
- Otimizador heurístico de até três propostas de calendário, com classificação relativa por perfil e justificativa das informações faltantes. **Não planeja trajetos com duração desconhecida, pernoites sem logística completa nem combinações impossíveis**. Só agenda na França em férias/finais de semana e não substitui atividades já agendadas. Tempo de visita é estimativa editorial.
- Propostas são **simulações**. Para alterar a agenda da versão em sessão é obrigatório clicar **Aprovar esta proposta**. Rejeitar mantém o plano intacto; versões obsoletas são bloqueadas.
- Exporta e importa JSON versionado. A lista de passeios existente é importada por ação explícita e nunca altera a decisão oficial D-004 do Drive.
- O orçamento estimado não considera valores desconhecidos como zero disponível; apenas o excedente conhecido sobre a verba de passeios já provisionada é adicionado como delta.
- Nenhum serviço de rota em tempo real foi integrado.

## Modelo e módulos
- `trip_plan_model.py`: plano versionado, validação e aprovação de propostas.
- `trip_plan_repository.py`: GitHub REST, SHA otimista, allowlist de caminho sob `data/user_plans/`.
- `travel_advisor.py`: diagnósticos e recomendações explicadas.
- `travel_optimizer.py`: gerador limitado de calendários candidatos.
- `travel_advisor_ui.py`: tela, revisão/aceite, exportação e salvamento opcional.
- `tests/test_travel_advisor.py` e `tests/test_travel_advisor_ui_smoke.py`: regressões.
- `app.py`: roteamento para a aba nova; `.github/workflows/validate.yml`: CI ampliado.

## Ativar gravação GitHub: autenticação Google OIDC

O app segue em **somente leitura/exportação JSON** até a configuração pelo proprietário nos Streamlit Secrets. O login anterior por senha e hash SHA-256 foi descontinuado; nunca reutilizar `advisor_github.password_sha256`.

A configuração atual exige Google OAuth Client, Google OIDC com e-mail verificado e não expirado, `[advisor_github].owner_email`, e token GitHub restrito ao repositório, guardado exclusivamente no servidor. O proprietário autenticado confirma expressamente que o repositório é público antes de salvar.

**Instruções completas (sem publicar credenciais):** [GUIA_ATIVAR_SALVAMENTO_GITHUB_SEGURO.md](GUIA_ATIVAR_SALVAMENTO_GITHUB_SEGURO.md).

Em 15/11/2026, `clevertondecker/europe-trip` é **público**. Qualquer roteiro salvo ali poderá ser lido por terceiros; não incluir informações pessoais. O token GitHub tem poder de escrita no repositório selecionado, não apenas na pasta de planos. Para melhorar privacidade e segurança, considere um repositório de planos privado ou autenticação via GitHub App com tokens temporários.

GitHub registra versões do arquivo. A UI autenticada permite consultar planos, ler histórico de commits e pré-visualizar/restaurar como revisão local; uma restauração não é gravada sem uma nova confirmação explícita.

## Limitações para decisões reais
A matriz tem 44 combinações origem/destino, com somente 10 tempos ferroviários registrados na auditoria inicial. A maioria não possui horários do último trem, chegada porta a porta, custo normal ou sazonalidade verificada para 2027. Portanto:
- Recomendação sobre uma viagem é **candidata**, não garantia de viabilidade.
- Otimização de calendário é heurística e conservadora; não substitui serviço oficial de transporte ou reserva.
- Pontuações são pesos configurados, não modelo treinado em avaliações.
- Três propostas podem ser similares se poucas excursões tiverem informações suficientes.
- Para dados incompletos, o sistema identifica o bloqueio em vez de inventar uma alternativa confirmada.

## Próximos incrementos de engenharia
1. Autenticação OAuth/GitHub App de proprietário com mecanismo robusto de login e token temporário de escrita.
2. Importar por ID, listar revisões do GitHub e restaurar snapshots com aprovação.
3. Buscar horários reais de transporte e calendários de abertura para 2027, validando fontes e licenças.
4. Avaliar OR-Tools com restrições de horários, orçamento, pernoites e tempo de recuperação; não introduzir dependência até haver dados suficientes.
5. Inspeção visual da versão hospedada. CI/AppTest verifica código e componentes, **não** aparência real do Streamlit Cloud.
