# Consultor inteligente sem LLM — implementação (15/11/2026)

## Como acessar
**Roteiro → Consultor inteligente** no Streamlit [Nossa Europa 2027](https://nossa-europa-2027.streamlit.app/).

Esta função adiciona regras e otimização determinísticas aos componentes já existentes, **sem integração com OpenAI/Gemini**.

## Funcionalidades
- Perfil padrão **Equilibrado**; alternativos **Economizar** e **Aproveitar ao máximo**. Pesos transparentes por interesse, custo, conforto e calendário.
- Importa a seleção de atrações em `st.session_state["explore_packages"]`, permite escolher outra base e gera diagnósticos com fontes e sugestões.
- Diferencia preços historicamente publicados, tarifas condicionais e custos desconhecidos; EUR e CHF só são agregados em BRL após câmbio hipotético informado.
- Analisa logística: retorno não verificado, Carte Fluo, trechos longos, Alpes/pernoite e falta de preços.
- Otimizador heurístico de até três propostas de calendário. **Não planeja trajetos com duração desconhecida, pernoites sem logística completa nem combinações impossíveis**. Só agenda na França em férias/finais de semana e não substitui atividades já agendadas. Tempo de visita é estimativa editorial.
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

## Configuração de escrita no GitHub — opt-in e com cuidado
O aplicativo, sem configuração, permite apenas **exportar/importar JSON**. Isso é intencional: ele pode ser público, e a integração atual com o Drive é somente leitura.

Para habilitar gravação, é necessário configurar no **Streamlit Secrets** uma seção chamada `[advisor_github]`, contendo:
- `token`: token server-side associado a conta GitHub ou GitHub App com permissão de **Contents: Read & Write** no repositório `clevertondecker/europe-trip`. Preferir GitHub App de acesso restrito e com token temporário, ou token de menor escopo possível.
- `password_sha256`: SHA-256 hexadecimal de senha de proprietário **longa, aleatória, exclusiva**, que não deve ser versionada. O hash não é uma solução de identidade multiusuário: não usar para acesso público amplo.

**Atenção:** o token de escrita pode ter permissão técnica no repositório inteiro; a aplicação limita o caminho em código, mas isso NÃO equivale a um token restrito ao diretório. Para uso público e produção, substituir a autenticação simplificada por OAuth/GitHub App com verificação de usuário e proteção contra tentativas distribuídas. **Não colocar credenciais em chat, README ou commit.**

Sem os dois Secrets, nenhum usuário da interface consegue chamar o método de gravação. A gravação exige senha do proprietário, segue confirmação explícita por botão e valida o SHA antes de sobrescrever. Em conflito, falha sem perda silenciosa.

O GitHub tem histórico de alterações do arquivo como rastreabilidade; **UI de listagem/restauração de versões passadas ainda não está implementada**. Exportação JSON e conteúdo dos commits permitem recuperação manual.

**Visibilidade:** a versão salva em um repositório público pode ser lida por qualquer pessoa! Não armazenar dados pessoais, reservas com nomes, número de documento, endereços privados ou outras informações sensíveis nele. Verifique se o repositório é privado antes de armazenar itinerários pessoais.

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
