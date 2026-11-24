# DATA24C — Auditoria técnica de moradia

Depende de DATA24A (#253). Ampliar o mesmo gerador de docs/audits/data24_research_coverage.md, sem página no app ou novo relatório concorrente. Reutilizar observed_housing, housing_short_stay_research_model, UX506/REC04 e evidências canônicas. Distinguir anúncios históricos, catálogo, preço mensal/temporada, bairros, 56–60 noites, duas pessoas, internet, taxas/caução, contrato/disponibilidade 2027; não misturar amostras ou tratar ausência como zero. Contagens com universo explícito, estados não aplicável/indeterminado, fontes/datas/condições, lista de lacunas para pesquisas posteriores. Não coletar novos dados, modificar orçamento/persistência ou ranking. Testes de paridade, ausência, unidades, fontes, determinismo e integração ao snapshot público. CI verde.

## Entrega
Implementar sequencialmente após pré-requisitos. Antes de implementar, atualizar base com alterações integradas ou estabelecer stack revisável; evitar conflitos em app.py e no gerador. Manter draft até código, suíte completa e checks do HEAD confirmados; não mergear sem autorização. Documentar limitações e evidência de testes. DATA25–28 serão definidos a partir dos resultados, não neste PR.

**Status:** especificação publicada; implementação pendente.