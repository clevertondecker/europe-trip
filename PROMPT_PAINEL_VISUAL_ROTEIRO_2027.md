# Prompt de implementação — painel de viagens visual (Nossa Europa 2027)

## Contexto
Aplicativo Streamlit Python existente no repositório clevertondecker/europe-trip.
Uma única fonte de verdade é TripPlan, com custos parciais e evidências históricas.
Casamento em 04/09/2027; viagem candidata começa depois. Itália seguida de temporada na França.
Roteiro de duas pessoas, teto configurável R$ 60 mil ou R$ 70 mil.

## Objetivo
Transformar Roteiro → Visão geral em um dashboard editorial de viagens, mantendo
funcionamento e sem recriar um editor de plano.

## Requisitos
1. Hero estilo diário de viagem, responsivo, com contexto Itália → França.
2. Quatro indicadores reais: destinos, atrações, datas planejadas e teto do orçamento.
3. Mapa interativo com coordenadas verificadas do catálogo; distinguir base hipotética
   dos passeios aprovados; não desenhar rotas fictícias.
4. Orçamento integrado ao advisor_finance: projeção, margem, progresso proporcional
   ao teto, despesas conhecidas, pendências e indicação de preços históricos.
   Não somar passeios duplicadamente, já que existe provisão no cenário.
5. Cards com fotos licenciadas e crédito, nomes, atrações e datas reais dos
   destinos aprovados; estado vazio orienta descobrir destinos.
6. Botões nativos para ir a Orçamento, Descobrir e Meus passeios.
7. Resguardar roteiro de pesquisa anterior em painel secundário.
8. Sem reservas, cotações inventadas, novos serviços, mudança de esquema JSON
   ou gravação de estado ao apenas visualizar a tela.
9. CSS responsivo sem perder controles acessíveis.
10. Criar testes unitários para seletor do painel e AppTest para navegação.
11. Publicar via pull request, validar GitHub Actions e só integrar após CI verde.
12. Documentar limites: visualização real no navegador, OAuth e dados de 2027
    não podem ser considerados verificados pelo teste automatizado.

## Arquivos esperados
travel_dashboard_ui.py, app.py, assets/styles.css, tests/test_travel_dashboard.py.
