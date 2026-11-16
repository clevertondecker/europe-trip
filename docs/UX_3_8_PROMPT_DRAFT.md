# Prompt — UX 3.8: Orçamento com cotações e compromissos reais

**Estado:** RASCUNHO A · NÃO FINALIZADO (aguarda revisão UX independente)  
**Evidências:** `advisor_finance.py`, `unified_budget.py`, `finance_margin_metrics.py`, `outing_cost_evidence.py`, `city_decision_model.py`, `city_decision_ui.py`, `ux_navigation.py`.  
**Pré-requisito:** revisar os contratos finais da UX 3.5 para evitar dupla contagem de viagens e visitas repetidas.

## Problema e objetivo

A aplicação já possui cenários de **R$ 60 mil/R$ 70 mil**, referências históricas e alertas de ausência de preço. Quando começam a surgir **cotações individuais reais**, o usuário precisa comparar a previsão com **o que pretende reservar**, distinguir compromissos pagos e atualizar decisões sem perder os valores originais.

**Resultado humano:** entender, para duas pessoas, *quanto foi estimado, quanto tem cotação confiável, quanto está comprometido/pago, o que falta e como uma nova escolha impacta a reserva financeira*.

## Prompt de implementação proposto

1. Não criar um novo `unified_budget` nem substituir as premissas oficiais. Criar camada opcional de **itens financeiros vinculados** a etapa, cidade, visita (`visit_id`), acomodação, transferência ou categoria, cada um com `estado` (estimado, cotado, reservado, pago, cancelado), `moeda`, `quantidade`, `unidade`, `fonte`, `data`, `validade`, `custo`, `reembolsável?` e identificador seguro.
2. **Nunca** converter automaticamente tarifa mínima `desde` em cotação aprovada. Uma cotação exige escopo, data, moeda, quantidade de pessoas, condições e período. Sem fonte suficiente, o valor permanece provisório.
3. Separar visualmente **teto planejado**, **provisão para categoria**, **cotações verificadas**, **compromissos assumidos**, **pagamentos** e **não cotado**. A soma dos valores pagos não implica que as demais despesas são zero.
4. Exibir na **Orçamento → Resumo financeiro** um bloco compacto: total comprometido, margem estimada do envelope e cobertura dos custos principais. Em **Meu roteiro**, o custo de uma visita é contextual; em **Explorar**, uma simulação não altera compromissos reais.
5. Reconciliar automaticamente os dados **sem dupla contagem**: um trem por visita intermunicipal, não por atração; alojamento uma vez por período e ocupação; separar despesas duplicadas em categorias e o que já integra a provisão atual.
6. Permitir revisar uma nova cotação, substituir a anterior mantendo histórico e desfazer, sem transformar todas as cotações numa fatura total. Sempre mostrar diferenças: `antes → depois`, base de comparação e se é pagamento real ou estimativa.
7. Se houver valor em EUR/CHF, armazenar moeda e data da taxa utilizada; diferenciar câmbio simulado de taxa efetiva do pagamento. Sem conversão implícita para status de pago.
8. Integração privada conforme arquitetura UX 3.6; **não** armazenar comprovantes, dados bancários ou reservas pessoais no repositório público. Evitar capturar dados sensíveis desnecessários.
9. Reutilizar `advisor_finance`, `unified_budget`, `finance_margin_metrics` e `outing_cost_evidence`. A lógica nova deve ser uma **camada de reconciliação testável**, não uma nova fonte de dinheiro.

## Exemplos de jornada

- **Antes:** comparo uma cidade no UX 3.4 e vejo apenas provisão de aluguel.
- **Depois:** quando coloco uma cotação real de apartamento para 56–60 noites, o orçamento a identifica como **cotação não reservada**, vinculada à mesma comparação; aplicar uma nova base não troca automaticamente um compromisso.
- **Antes:** adiciono duas atrações em Colmar e vejo risco de duas passagens somadas.
- **Depois:** um dia/visita mantém um deslocamento intermunicipal; dois dias distintos preservam duas visitas distintas.

## Aceite

- Aluguel estimado vs. cotação de imóvel elegível: não misturar €/mês e € por estadia sem conversão explícita de período e taxas.
- Quatro casos: sem cotação → desconhecido; cotação histórica → estimado; cotação ainda válida → cotado; comprovante marcado manualmente → pago.
- Duas atrações numa visita não duplicam bilhetes intermunicipais; visita repetida em dia distinto é contada separadamente.
- Cancelamento e estorno não alteram silenciosamente o total do orçamento; histórico e status permanecem.
- Alterar câmbio de simulação não reescreve o valor efetivamente pago.
- Nenhum valor de reserva real aparece em estudo exploratório de outra base sem aviso explícito.
- Menos de duas mudanças de área para registrar cotação a partir da visita, consultar efeito no orçamento e voltar ao dia.
- Cobertura de testes com Decimal, moedas EUR/CHF/BRL, variações de datas, revisão obsoleta, logs seguros, UX por teclado e cenários com dados desconhecidos.

## Alternativa menor / condição de rejeição

Se o usuário ainda não possui cotações reais suficientes, **não** montar contabilidade completa. Entregar apenas um registro simples de `cotações para comparar`, com data/validade e impacto sobre as rubricas existentes; expandir a `pago` depois de validação de uso.

**Entregável futuro:** PR próprio após aceite A+B e checagem da UX 3.5/3.6; sem merge automático.
