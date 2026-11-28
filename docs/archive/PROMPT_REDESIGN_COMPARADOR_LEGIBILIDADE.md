# Prompt executável — Redesign de legibilidade do Comparador de cidades

## Objetivo
Refatorar SOMENTE a tela "Comparar cidades" em Nossa Europa 2027 para reduzir a carga cognitiva das informações já coletadas. Base obrigatória: app.py, city_market.py, data/city_market_observations_2026.json, city_research.py, city_compare.py e a auditoria versionada. Não pesquisar nem alterar preços, notas, fontes ou status de decisão nesta etapa.

## Design A+B aprovado
Branco e azul claro predominantes, tipografia sans serif, poucas cores semânticas (azul = informação; verde suave = favorável; âmbar = não confirmado; cinza = histórico). Cards com dados expressivos, textos curtos, números legíveis, boa responsividade e distâncias consistentes.

## Nova arquitetura da tela
1. Cabeçalho com resumo e quatro KPIs (cidades pesquisadas, anúncios observados, cotações válidas para 2027, data do retrato).
2. Navegação por abas: "Visão rápida", "Moradia", "Transporte e custos", "Comparar e ajustar".
3. Visão rápida: quatro cartões uniformes, cada um com mediana da AMOSTRA de três anúncios, intervalo da amostra, passe urbano publicado, um ponto de atenção e evidência insuficiente; nenhuma classificação oficial de vencedora.
4. Moradia: tabela compacta com 12 observações, contas incluídas/fora, área e URL de catálogo, aviso de que não são ofertas individuais verificadas. Manter pesquisa detalhada e fontes acessíveis.
5. Transporte: tabela única com origem, destino, minutos, tarifa reduzida por pessoa/trecho e fonte operadora como link; passes mensais em tabela separada. Manter notas de elegibilidade Carte Fluo e validade 2025–26. Cesta histórica em card separado, sem diferenças inventadas entre cidades.
6. Comparar e ajustar: perfis e sliders preservados com inicialização correta; ranking editorial 2026, notas por critério e comparação de duas cidades, com pontos favoráveis e riscos bem diferenciados; método e auditoria nos expanders ao fim.
7. Conservar avisos de não decisão, zero cotações de 2027, não sincronização live da matriz histórica; não editar Drive ou orçamento financeiro.
8. Evitar botões de fonte repetidos após cada linha. Preferir URLs nas tabelas com LinkColumn.
9. Dados do usuário/externos escapados em HTML; atenção à legibilidade em tela menor.

## Critérios de aceite
- As cinco outras telas, login e sincronização Drive continuam inalterados.
- As quatro cidades exibidas no mesmo esquema.
- Score editorial e mediana de anúncios não confundidos com custo real de 55–65 noites.
- Fontes acessíveis em tabelas e áreas de metodologia.
- Todos os testes unitários e compilação Python passam no GitHub Actions.
- Publicar pela integração GitHub, sem push local; validar execução CI e pedir teste visual no Streamlit Cloud.
