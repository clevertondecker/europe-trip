# ARCH 1.2 — extração incremental do `app.py`

Primeiro recorte de baixo risco: renderização do mapa (camadas Scatterplot e
TextLayer, paleta de status, tooltip e ViewState) foi movida para
`map_presentation_ui.render_map_view()`.

O entrypoint `app.py` preserva a função `map_view()` e a mesma assinatura,
chamando o módulo extraído. O ponto de entrada, autenticação, bootstrap do
TripPlan, sincronização Drive, CSS e navegação não mudaram.

Próximos recortes são condicionados a AppTests: separar funções de navegação
e layout em PRs próprios, sem reorganizar callbacks e widgets em lote.
A remoção de linhas, isoladamente, não é critério de sucesso.
