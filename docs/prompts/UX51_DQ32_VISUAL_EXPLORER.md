# UX 5.1 — Explorador visual DQ3.2

## Objetivo
Deixar a matriz exploratória legível para decisões de viagem sem mudar a
precedência de evidências nem fingir disponibilidade logística em 2027.

## Mudanças
- Durações apresentadas como `18 min`, `1h30`, `4h48`; inteiros
  originais continuam inalterados no domínio.
- Resumo visível com total de destinos, referências, lacunas e atrações locais.
- Países, faixa de tempo de **ida** e ordenação por menor tempo, maior
  número de atrações ou nome.
- Alternância entre tabela e cartões nativos do Streamlit.
- Coluna de país, tipo de evidência e link direto à fonte; remover
  `Passeio confirmado: Não`, redundante para lista exploratória.
- Detalhes mostram fonte, consulta e confiança quando disponíveis,
  atrações individuais e pendências reais de retorno, estação, tarifa e acesso.
- Manter `ux_dq32_opportunity_group` e
  `ux_dq32_selected_destination` por compatibilidade.
- Não criar motor de rotas ou estimar retorno a partir de tempo mínimo.

## Critérios de aceite
1. `format_travel_minutes(90) == "1h30"`,
   `format_travel_minutes(49) == "49 min"`, sem alterar minutos no dataset.
2. Filtrar até 1h não inclui pares de 1h01; desconhecidos não
   entram em filtros por duração, mas aparecem em "Todos".
3. Países e ordenação funcionam com diferentes bases (Mulhouse e Lille).
4. Nenhum clique altera TripPlan, base oficial ou reservas.
5. Tabela preserva minutos de auditoria e oferece fonte por linha;
   cartões usam informações reais, sem imagens inventadas.
6. Mobile não apresenta cortes e exige inspeção visual após deploy.
7. Validar com `python -m compileall -q .` e
   `python -m unittest discover -s tests -v`.

## Restrições
Não mexer nos datasets de pesquisa, autenticação, sincronização
ou contratos ferroviários. As fontes publicadas em 2026 são
mínimos de ida, não viagens datadas para setembro–novembro de 2027.

## Inspeção visual
CI e AppTest não são prova de responsividade. Verificar tela real
em 1440×900 e 390×844 e comparar com a captura anterior antes
de considerar a experiência visual integralmente aprovada.
