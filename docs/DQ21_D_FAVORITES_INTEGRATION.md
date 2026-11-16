# Data Quality 2.1 D — integração UX sem recriar telas

## Base
Reutiliza UX 4.1 e DQ 2.0 com o mesmo seletor de favoritas; não altera a cesta original de **15 destinos** nem remove os blocos financeiros UX 4.4, moradia, backups, fonte e abertura de ficha.

## Integração
`dq21_decision_model.decision_research(selected,work_day=None,brazil_hours=None)` une os modelos A/B/C sob demanda, respeita cidade e ordem e retorna `aguardando_modulos` se A/B/C ainda não foram mergeados.

`dq21_comparison_ui.render_dq21_panel` insere um painel discreto em **Explorar → Cidades-base → Comparar favoritas**, somente quando duas ou três favoritas pertencem a Mulhouse/Strasbourg/Freiburg. Seções: Passeios / Morar e trabalhar / Chegada e volta / Fontes e pendências; dados em tabelas curtas e detalhes sob consulta. DQ 2.0 continua acessível como pesquisa histórica, sem duplicar lógica.

## Decisões de UX
- Seleção das mesmas favoritas, sem alteração no `TripPlan`, sem classificar cidades por pontuação.
- "Retorno 2027 não confirmado" é diferente de "destino impossível".
- Trabalho 9–18 não é predefinido: usuário escolhe cenário opcional e data (horário de verão europeu calculado pelo `zoneinfo`).
- Aeroportos FRA/ZRH têm voos divulgados em 2026, não passagens para 2027 nem voos finais ao destino do usuário no Brasil.
- A comparação financeira UX 4.4 não recebe dados novos sem orçamento completo.
- Não somar pernoites/hospedagem às despesas do orçamento oficial.

## Testes
CI: `python -m compileall -q .`; `python -m unittest discover -s tests -v`. Testar DQ21 em combinação com A/B/C numa branch temporária de validação sem merge. Depois, inspeção visual 375/768/1280, teclado e backup real: ainda dependem de browser autorizado.

## Pendências
Operador com horários de retorno específicos para as 15 combinações, tempos porta a porta com hospedagem escolhida, disponibilidade e preços reais de 2027, clima DWD primário reconciliado e aeroportos de destino final no Brasil. Não atribuir status de pesquisa concluída sem essas provas.
