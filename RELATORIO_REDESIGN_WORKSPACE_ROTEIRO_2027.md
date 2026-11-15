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

## Validação pendente

Executar em ambiente com as dependências do projeto:

```bash
python -m compileall -q .
python -m unittest discover -s tests -v
```

Validar AppTest e conferir desktop/mobile em um ambiente Streamlit. Esta entrega não afirma inspeção visual nem testes locais executados. Confirmar CI antes de fazer merge.

## Próximas melhorias propostas

- Cards ainda mais compactos e paginados no editor (sem alterar seu modelo).
- Filtros adicionais por categoria, ordenação e tempo disponível, usando somente campos verificáveis do catálogo.
- Consolidar controles de salvamento para eliminar renderizações GitHub não necessárias.
- Testes end-to-end de autorização, histórico e importação de backup.
- Revisar responsividade real em dispositivos móveis.
