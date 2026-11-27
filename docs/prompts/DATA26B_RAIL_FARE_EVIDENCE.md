# DATA26B — Evidência tarifária individual
Reutiliza validate_service_leg e weekend_roundtrip_evidence; não substitui DATA24 nem altera preços oficiais.
Dataset inicialmente vazio. Valores em centavos/unidades menores da moeda, total para duas pessoas, por ida ou ida e retorno conforme trechos explícitos. Fonte documental não confirma oferta atual ou 2027.
Não agrega preços nem calcula ranking; comparabilidade exige mesmos trechos, datas, moeda, classe, condições e quantidade. Ausência de preço não equivale a zero.
CI e revisão obrigatórias; QA visual pendente.

## Revisão
Identidade inclui estações, instantes UTC, serviços e baldeações normalizadas. Preço não integra a chave; divergências de preço/estado/taxas na mesma chave são conflitos. Consulta pode incluir instante com offset ou apenas data; não inventar hora. Perfil fixo dois adultos, elegibilidade explícita (none ou descrição, null desconhecido), estrutura de bilhete e condições textuais de flexibilidade/reembolso/restrições. Taxas incluem reservas obrigatórias. Escopo derivado dos trechos, calendário separado da coerência temporal; estações diferentes não comprovam transferência urbana. Nenhuma viabilidade ou confirmação independente. Dataset vazio preservado. Testes ampliados; CI, paridade DATA24 e QA visual ainda precisam de confirmação.

## Fechamento da revisão
Reembolso e alteração são dimensões explícitas (permitido, condicional, não permitido, desconhecido). Instantes de consulta equivalentes em UTC compartilham identidade mesmo com datas locais diferentes. Contadores completos separados por escopo. AppTest com múltiplas ofertas, preço zero e desconhecido; teste de paridade DATA24 com fixture não vazia. Removidos expanders aninhados e widgets de link repetidos. Resultados de CI e QA visual ainda não confirmados.
