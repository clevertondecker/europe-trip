# Agente 1 — Entrega financeira

Módulos novos, sem modificar os componentes centrais. `finance_margin_metrics.calculate_excursion_margin(finance_projection, known_costs, eur_fx, chf_fx, missing)` recebe o dicionário de `advisor_projection()` e a saída `package_cost()['known_by_currency']`. Retorna margem geral, total convertido de custos conhecidos, parcela coberta pela provisão, saldo nominal da provisão, excedente conhecido, percentual e pendências.

`finance_margin_ui.render_finance_margin_summary(metrics,profile=...)` exibe os valores e o aviso de incompletude. Integração prevista exclusivamente em `scenario_board_ui.py` pelo integrador. Sem atualização de orçamento oficial; não interpreta saldo como economia garantida.
