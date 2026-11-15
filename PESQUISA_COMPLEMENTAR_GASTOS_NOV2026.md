# Pesquisa complementar — supermercado, cardápios de fim de semana e conciliação do orçamento

Data da revisão: **15/11/2026**. Os preços são observações atuais no comércio da França,
não garantias para setembro a novembro de 2027. A pesquisa prioriza França
(assumindo estadia com cozinha), e restaurantes de fim de semana em Colmar,
Strasbourg e Mulhouse. Basel, Metz e Nancy continuam com lacunas.

## 1. Novas evidências estruturadas

Fonte de dados: `data/grocery_weekend_evidence_2026_11.json`.

### Supermercado francês — quatro preços observados

| Produto | Unidade | Preço observado |
|---|---|---:|
| Leite semidesnatado Carrefour Classic | 1 L | € 1,05 |
| Espaguete Carrefour Classic | 500 g | € 0,70 |
| Arroz longo Carrefour Classic | 1 kg | € 1,75 |
| Ovos Carrefour Classic | 12 un. | € 2,99 |
| **Subtotal de quatro embalagens** | **Não é uma cesta diária completa** | **€ 6,49** |

Fontes: [Carrefour leite](https://www.carrefour.fr/r/cremerie/laits/lait-demi-ecreme),
[Carrefour massa](https://www.carrefour.fr/r/epicerie-salee/pates),
[Carrefour arroz](https://www.carrefour.fr/r/epicerie-salee/pates-riz-feculents/riz),
[Carrefour ovos](https://www.carrefour.fr/r/cremerie/oeufs).

**Limitações:** preços de loja, entrega/drive e promoções podem variar;
não comprovam custo de vida de cada cidade. Não abrangem café, água, frutas,
legumes, verduras, proteínas, queijos, refeições prontas, almoço, jantar ou mês
inteiro. Nenhum cálculo os transforma automaticamente em gasto diário ou mensal.

### Restaurantes com preço e operação publicada aos fins de semana

| Destino | Estabelecimento e prato publicado | Dias | Preço/pessoa |
|---|---|---|---:|
| Colmar | Savanna · prato vegetariano/vegano | sábado e domingo | €17 |
| Colmar | Savanna · salmão grelhado | sábado e domingo | €25 |
| Colmar | Le Zinc · choucroute garnie | **sábado, não domingo** | €21 |
| Strasbourg | Brasserie des Haras · prato do dia | sábado e domingo | €27 |
| Strasbourg | Brasserie des Haras · menu completo | sábado e domingo | €49 |
| Mulhouse | Restaurant Hug · salada campagnarde, porção prato | sábado, não domingo | €14,50 |

Fontes oficiais: [Savanna](https://savanna-colmar.fr/),
[Le Zinc](https://lezinc-colmar.com/),
[Brasserie des Haras](https://les-haras-brasserie.com/),
[Restaurant Hug](https://www.restaurant-hug.fr/carte-menu/).

**Não comparar diretamente** prato avulso com menu de três etapas; a amostra é
pequena e não representa uma média. Se o passeio estiver marcado para um
**domingo**, o sistema não usará o preço de menu do dia útil nem o restaurante
que fecha domingo. Sem data, o preço de refeição permanece pendente.
A data exata em 2027 ainda requer verificação de feriados, eventos,
mudança de menu, abertura real e reserva.

## 2. Alternativa ferroviária adicional

[Pass Groupe Week-End TER Fluo Grand Est](https://www.ter.sncf.com/grand-est/tarifs-cartes/tarifs-regionaux/pass-groupe-week-end)
publica **€40 por dia**, válido a grupos de **2 a 5 pessoas** aos sábados,
domingos e feriados, no universo de trens e ônibus TER Fluo elegíveis.
É uma alternativa a verificar em cada percurso, não economia automática.
Não afirmar cobertura integral até Basel nem que vale em TGV ou outro operador.

Continua valendo [Carte Fluo](https://www.ter.sncf.com/grand-est/tarifs-cartes/cartes-reduction/carte-fluo),
€30/ano, com desconto do acompanhante aos fins de semana/feriados e outras
regras de elegibilidade. A tarifa normal de quase todas as rotas segue pendente.

## 3. Conciliação e dados que não podem ser duplicados

O orçamento existente `advisor_projection` inclui:
- `excursions`: provisão para passes e ingressos, cujo subtotal hoje usa
  preços históricos com Carte Fluo sem validar a compra do cartão.
- `dining`: alimentação fora, **já modelada** como duas saídas semanais
  a €60 para o casal no período francês.
- `groceries`: alimentação cotidiana em casa.

O novo cálculo `reconcile_researched_itinerary` faz, sem salvar nem modificar:

1. Lê os passeios confirmados e suas datas na grade de viagem.
2. Consulta a refeição do dia apropriado (sem inventar funcionamento).
3. Usa tarifa ferroviária **normal publicada** quando existe, sem supor
   benefício Carte Fluo ou divisão de cartão para vários passeios.
4. Compara somente os valores observados e conhecidos às provisões já
   presentes, sem somar alimento ou excursão duas vezes.
5. Se faltar data/tarifa/almoço, **oculta a projeção conciliada**, informa
   a lacuna e mantém a projeção atual separada.
6. Quando houver cobertura para todos os passeios selecionados, mostra
   **apenas uma simulação de referência parcial usando preços 2026**.
   Não corresponde a custo completo nem cotação para 2027.

### Exemplo: domingo 10/10/2027, Colmar a partir de Mulhouse

- Tarifa regular conhecida para duas pessoas, ida e volta: €43,20
  (referência SNCF; data/retorno 2027 não verificados).
- Dois exemplos de prato no Savanna: €17 ou €25 por pessoa; ponto
  médio aritmético dessa pequena amostra €21 por pessoa. **Não é mediana
  representativa da cidade**.
- Um almoço para casal ilustrativo: €42.
- Subtotal combinado (sem outros custos ou ingressos adicionais):
  €85,20 = **R$536,76** com EUR/BRL hipotético 6,30.
- O custo não se soma integralmente à projeção global, pois parte já
  pode estar prevista em `dining` e `excursions`.

Mudando a base para Strasbourg, **não há tarifa normal documentada**
suficiente na matriz. O sistema não exibirá projeção reconciliada.

## 4. Pendências importantes

- **Supermercado mensal:** falta cesta nutricional completa, quantidades
  reais consumidas por dois adultos, supermercados locais e comparação por
  cidade. A pequena cesta de €6,49 **não serve como estimativa mensal**.
- **Domingos em Mulhouse:** sem preço publicado e funcionamento confirmado
  simultaneamente nos exemplos coletados.
- **Basel:** faltam cardápios de fim de semana com preços comparáveis.
- **Metz/Nancy:** faltam custos de supermercado local e restaurantes, além
  de várias rotas, horários e tarifas.
- **Retornos ferroviários em 2027:** frequência, conexão exata, último trem,
  interrupções e trajetos porta-a-porta não confirmados.
- **Viagem e imprevistos:** orçamento de contingência já existe; não aplicar
  uma segunda porcentagem diretamente sem verificar o que já cobre.
- **Refeições adicionais:** jantar, cafés, bebidas e alimentação durante
  trabalho remoto ainda não conciliados com hábitos reais do casal.

## 5. Critérios para considerar concluída a estimativa global

Só atualizar o total oficial quando houver dados representativos o
suficiente para reconciliar **todas** as parcelas da viagem, calendário,
refeições substituídas, transporte, pernoite, contingências e fontes.
Até lá, mostrar intervalos/histórico + pendências é mais correto que
uma falsa precisão.
