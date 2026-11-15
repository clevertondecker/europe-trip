# Relatório — Redesign do workspace Roteiro 2027

Data: 15/11/2026
Branch: `feature/roteiro-workspace-compacto-2027`

## Escopo implementado nesta entrega incremental

- A navegação da página Roteiro foi reorganizada em **Meus passeios**, **Descobrir**, **Orçamento** e **Calendário**, com **Visão geral** e **Guias e pesquisas** como acessos secundários.
- Os antigos painéis de atrações, Itália/Costa Amalfitana, França/escapadas, transportes, calendário de pesquisa e cronograma permanecem disponíveis em Guias e pesquisas.
- O consultor passou a receber o contexto da área ativa, mantendo a mesma instância do plano canônico.
- Configurações de cidade-base, otimização, teto, câmbio e aluguel foram recolhidas em painéis específicos.
- O status de salvamento e um resumo contextual da viagem aparecem no alto do consultor.
- Descoberta e quadro de cenários não são mais renderizados conjuntamente: o catálogo oferece busca, filtro de país e carregamento progressivo; o orçamento exibe a comparação dos estilos sem carregar os cards de edição.
- Edição, desfazer, aprovação em duas etapas, estado dos rascunhos por perfil e validação de propostas obsoletas continuam com suas funções originais.
- O salvamento, backups, histórico, OAuth Google, reconhecimento de repositório público e controle SHA foram mantidos em um painel de Meus passeios.

## Arquivos modificados

- `app.py`: navegação principal e encaminhamento aos guias antigos.
- `travel_advisor_ui.py`: áreas renderizadas condicionalmente, configurações e salvamento.
- `discovery_ui.py`: separação descoberta/quadros e filtros do catálogo.
- `scenario_board_ui.py`: modo financeiro resumido.
- `tests/test_scenario_board_ui.py`: rota atualizada para Meus passeios.
- `tests/test_workspace_navigation.py`: cobertura inicial das novas áreas.
- `README.md`: instruções da nova navegação.

## Integridade e restrições

Nenhum motor financeiro, schema JSON, biblioteca de persistência ou configuração de autenticação foi alterado. Não foram geradas reservas, cotações ou rotas fictícias. Os cálculos continuam delegados a `advisor_finance.py`, `finance_margin_metrics.py` e `scenario_editor_model.py`.

## Validação automatizada

GitHub Actions `Validate Streamlit app` — execução [209](https://github.com/clevertondecker/europe-trip/actions/runs/43682862697): **aprovada**. Inclui compilação Python e suíte de testes unitários / Streamlit AppTest. Os testes de navegação foram ampliados para verificar os filtros e que Orçamento não renderiza os controles pesados do editor.

## Refinamentos adicionais deste PR

- Cards de destinos com resumo mais curto e paginação de seis itens.
- Busca e filtros por país e categoria real de atração, ordenação por relevância, nome e tempo ferroviário conhecido. Alterar filtros reinicia a paginação.
- O orçamento retorna após renderizar a comparação, sem criar estado de rascunho nem executar editor de atrações.
- O painel de salvamento fica antes da grade de passeios e o histórico GitHub não é consultado sem solicitação explícita do usuário.
- CSS responsivo para navegação com controles de toque em telas estreitas.

## Verificação visual e acompanhamento

Inspeção visual real em navegadores desktop e mobile **não foi executada**. Os ajustes CSS são preliminares e devem ser conferidos na versão publicada. Testes de integração externa com Google OAuth e persistência de planos privados também dependem de credenciais/configuração do proprietário.

A execução automatizada não altera planos JSON nem valida configuração de segredos do Streamlit. Não afirmar que o app publicado foi inspecionado visualmente até realizar essa verificação.
