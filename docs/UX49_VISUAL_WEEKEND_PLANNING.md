# UX 4.9 — Planejamento visual de fins de semana

## Diagnóstico e hierarquia

A criação e a edição usavam `st.form`, que entrega os valores ao Python apenas na submissão. A criação aparecia antes dos agrupamentos e a disponibilidade era apresentada em tabela. As opções de sábado consideravam dois dias mesmo quando a viagem tinha mais noites.

O planejador agora aparece antes do editor de datas individuais na atividade Organizar viagem. A ordem é resumo compacto, Minhas viagens com ação de criação, passeios não agrupados, editor contextual e lista de fins de semana. Cada grupo possui detalhes recolhidos e uma única entrada de edição. O calendário inteligente reutiliza o mesmo componente em seu modo exclusivo.

## Contratos reutilizados

`create_group`, `update_group`, `validate_groups`, `available_weekends` e o arquivo privado de continuidade permanecem como pontos de integração. O schema do sidecar permanece na versão 1. Arquivos antigos continuam passando pelo importador existente.

`eligible_weekends(state, plan, catalog, *, destinations, nights=0, period=..., group_id=None)` retorna uma lista com `start`, `end`, `eligible` e `reason`. A projeção experimenta cada sábado através dos mesmos validadores de criação/edição, sem modificar o estado recebido. A edição substitui o próprio grupo e por isso não conflita com sua ocupação anterior. O filtro de apresentação também respeita o período flexível escolhido. Backups antigos com períodos flexíveis históricos continuam válidos.

Zero ou uma noite ocupa sábado/domingo. Duas noites incluem segunda e três incluem terça. A interface informa que disponibilidade em dias úteis depende da rotina de trabalho do usuário. Uma data que se torna incompatível permanece visível com aviso e bloqueia o salvamento até ser substituída ou removida explicitamente.

O rascunho de edição fica em `ux49_editor`, separado dos valores transitórios dos widgets, para sobreviver à navegação. Alterações dos agrupamentos usam o indicador privado de alterações pendentes existente. Sucesso na sessão pede salvamento ou exportação. A reconciliação de mudanças no roteiro emite aviso quando ajusta grupos.

## Validação

Regressões de UX 4.9 cobrem ocupação do próprio grupo, conflito na segunda-feira, imutabilidade das entradas, criação, edição, ordem dos destinos e conservação de nome/observações quando pernoites invalidam uma data. A suíte UX 4.8 cobre o arquivo de continuidade com grupos, compatibilidade legada, descanso e reconciliação.

A inspeção visual de produção e o CI são registrados no PR. Gravação e restauração com credenciais reais do armazenamento privado exigem uma sessão autenticada. AppTest e testes de arquivo local não comprovam esse serviço remoto.
