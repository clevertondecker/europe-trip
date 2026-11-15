# Agente 2 — Evidências de custos de passeios

A implementação cobre 11 destinos, com quatro categorias de despesas adicionais sem cotação completa: transporte urbano, refeições extras, hospedagem eventual e retorno intermunicipal.

**Importante:** foram criadas 44 pendências explícitas, **não 44 preços pesquisados**. Valores inexistentes permanecem `null`. Bilhetes e tarifas já existentes continuam exclusivamente no catálogo original, sem serem duplicados.

API: `load_outing_evidence(catalog=...)`, `evidence_for_outing(destination_id,attraction_ids,data=None)`. Retorna `items`, `pending`, `known_by_currency`, `source_metadata`; a integração pode apresentar pendências no card sem somá-las como zero ao preço real. Atualização com preços reais exigirá URL HTTPS, data, validade, moeda e unidade; fontes não foram inventadas.

Contrato de integração: o integrador injeta `evidence_for_outing(...)` no detalhamento do cenário sem modificar `package_cost` e sem dupla contagem de despesas provisionadas.
