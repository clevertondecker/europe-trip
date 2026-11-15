# PROMPT EXECUTADO — Comparativo verificável de cinco cidades-base (15/11/2026)

## Objetivo
Aprofundar Offenburg, Trier, Mulhouse, Strasbourg e Lille após a triagem de 30
cidades no `Nossa Europa 2027`, com metodologia reproduzível, preços
observados e deslocamentos documentados; sem adicionar dados falsamente
precisos ao orçamento oficial.

## Restrições e dados canônicos
- Casal (2 adultos); casamento em 04/09/2027; viagem começa depois.
- Janela técnica **hipotética** para comparação de 60 noites:
  entrada 19/09/2027 e saída 18/11/2027. NÃO é data aprovada.
- Consulte `main` antes de editar; preserve `TripPlan` v1 e os módulos
  originais de ranking, orçamento, pesquisas e referências.
- Priorize fontes primárias de imóveis (HousingAnywhere, Wunderflats,
  ImmoScout) e operadoras de trem (SNCF, Deutsche Bahn, CFL).
- Tarifas `desde` são preços individuais **condicionais**, não ida e volta
  do casal, e nunca se aplicam automaticamente em 2027.

## Pesquisa
1. Reusar os anúncios individuais e catálogos de 2026 existentes.
2. Verificar **ao menos três referências de anúncio por base**; se
   faltar ocupação de dois adultos, contrato de 60 noites, internet, taxa
   total, disponibilidade de 2027 ou distância até a estação, deixar
   pendência identificada. Não confundir imóveis de 80–90 m² com
   estúdios de 25–40 m² como ofertas homogêneas.
3. Selecionar um conjunto **idêntico de 15 destinos geográficos** para
   todas as cinco bases. Usar matriz de rotas encontrada, sem completar
   conexões não verificadas. Uma rota com tempo pode não ter tarifa.
4. Onde possível, cadastrar menor duração por operadora, melhor opção
   regional distinta de ICE/TGV, dia de referência, conexão, fonte,
   tarifa promocional condicionada e indicador de retorno.
5. Calcular métricas transparentes de cobertura, faixa de tempo
   ferroviário mínimo e acesso a países; não contar destinos com dados
   ausentes como perto, longe ou gratuitos.
6. Rejeitar ranking definitivo ou custo total de 60 noites até haver
   3 opções de apartamento privadas, comparáveis, incluindo taxas e
   com confirmação da mesma janela de 2027 e conjunto de passeios
   com horários completos e custo normal do casal.

## Produto Streamlit
1. Criar painel comparativo em `Explorar bases → Pesquisa ampliada`:
   5 bases, 15 destinos fixos, filtro por base/destino e visão de cobertura.
2. Mostrar custos dos anúncios **por mês observado**, sem extrapolar para
   custo contratado de 60 noites. Registrar link e condições; quando
   faltar anúncio individual, apontar claramente para o catálogo.
3. Permitir orçamento de sensibilidade **apenas com valores inseridos
   pelo usuário** (aluguel total, alimentação, transportes, passeios,
   extras) e separar caução reembolsável. Não modificar a projeção
   oficial nem usar a média de aluguel como preço 2027.
4. Reusar o modelo de ranking reproduzível; permitir notas somente
   quando houver evidências de todos os critérios.
5. Testar: cidade sem rotas não aparece como barata; categorias não
   verificadas não se tornam zero; dois países distintos não são
   contados duas vezes; cenário é não persistente; `AppTest` sem
   mutação do TripPlan.

## Entrega
- Datasets auditáveis JSON e relatório Markdown de fontes, resultados
  provisórios e incertezas.
- Testes automatizados contra o repositório completo; PR e CI antes
  do merge. Evitar qualquer deploy de preço não comprovado.
- Indicar claramente os itens faltantes para o ranking decisório.
