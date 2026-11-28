# Prompt executado — fase 2: alimentação real e conciliação financeira

## Contexto e problema
Projeto `clevertondecker/europe-trip`, após casamento 04/09/2027, casal,
estadia França + Itália. A fase anterior pesquisou menus de dias úteis,
alguns trens e transporte urbano, mas a projeção global tinha rubricas
já embutidas de supermercados, restaurantes e excursões. Somar
diretamente menus turísticos criaria dupla contagem.

## Missão
Pesquisar e conectar novos dados **verificáveis em 15/11/2026** sobre
comida cotidiana, restaurantes de fim de semana e transporte ferroviário,
aumentando a segurança financeira e a rastreabilidade sem inventar
tarifas para o segundo semestre de 2027.

## Implementação obrigatória
1. Pesquisar cardápios com preço individual e horários confirmados em
   páginas dos restaurantes de Colmar, Strasbourg, Mulhouse e Basel.
2. Marcar explicitamente dia da semana, prato/entrada/menu, unidade,
   moeda, publicação, data da consulta e URL. Não usar almoço de dia
   útil para domingo, não usar restaurante fechado nesse dia.
3. Pesquisar alguns preços de itens de supermercado com URLs de
   varejista oficial, quantidade/unidade e condições de loja.
   **Não derivar custo mensal de cesta incompleta**.
4. Incluir alternativa de transporte coletivo `Pass Groupe Week-End`
   de TER Grand Est somente como opção condicional €40/grupo/dia,
   sem presumir cobertura internacional ou disponibilidade 2027.
5. Construir JSON independente, versionado e validado, com metadados
   de fonte e campos desconhecidos claramente diferenciados.
6. Criar modelo puro de refeição por destino/data: se calendário marcar
   sábado/domingo, filtrar apenas restaurantes com ofertas nesses dias;
   se não houver data ou preços compatíveis, retornar informação
   insuficiente e **não usar €0**.
7. Calcular exemplos Econômico/Equilibrado/Aproveitar usando observações
   de menor preço, ponto central da amostra e maior preço, sem tratar
   observações heterogêneas como média estatística do mercado.
8. Conciliar excursões e uma refeição turística com verbas existentes:
   `excursions` e `dining`; registrar o quanto cada verba já cobre.
   Não somar custo bruto de restaurante às duas verbas já incluídas.
9. Sempre exigir tarifa **normal verificável**, ou passeio dentro da
   própria cidade, para cálculo completo de um subtotal.
   Tarifas com Carte Fluo não significam automaticamente desconto
   para as duas pessoas; cartão €30 só uma vez, e passagem transfronteira
   exige validação.
10. A projeção conciliada é **simulação separada**, não orçamento oficial,
    e deve ser suprimida quando faltar data, almoço elegível ou
    tarifa normal para qualquer passeio do plano.
11. Mostrar pendências: retornos, transporte urbano, outros cafés/jantares,
    ingressos desconhecidos, hospedagem, clima, câmbio, refeições
    em casa e eventos extraordinários.
12. Conectar a `Meus passeios`, `Orçamento` e `Simular roteiros`,
    mantendo a interface simples com expander opcional e fontes.
13. Criar testes para Colmar em domingo 10/10/2027, preço de
    Colmar/Mulhouse, troca da base para Strasbourg, roteiro sem
    data, cenários e ausência de mutação do `TripPlan`.
14. Salvar o relatório Markdown, PR e CI; integrar somente com testes
    verdes. Expor precisamente o que não foi verificado.

## Aceite
A tela apresenta uma estimativa **mais fundamentada, porém parcial**,
deixa claro por que pode permanecer o mesmo total global,
e nunca transforma dados desconhecidos em preço zero ou uma
suposição matemática em tarifa oficial.
