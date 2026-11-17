# ARCH 1.3 — CI e contratos de datasets

Adiciona duas etapas independentes ao workflow: `pip check` (consistência
das dependências instaladas) e validação determinística de datasets turísticos
via `python tools/validate_research_data.py`. Os testes existentes permanecem
no passo completo `unittest discover -s tests -v`.

O validador verifica 30 IDs de cidades-base, o catálogo histórico de 14
destinos e 65 atrações, identidade e fontes dos 30 registros DQ3.2, aliases
canônicos, duplicações de pares ferroviários, contrato `int | null` em
minutos e que os retornos de 2027 não estão declarados como verificados.
Ele **não** verifica que uma fonte externa permanece online ou que uma
citação turística esteja correta hoje.

Não adicionamos dependência de lint sem baseline, nem lockfile arbitrário
incompatível com Streamlit Cloud: versões reprodutíveis e separação de jobs
ficam condicionadas à análise de compatibilidade e desempenho reais. Não
modifica `requirements.txt`, serviços, TripPlan, UI ou dados originais.


## Revisão explícita do baseline

A validação estrutural aceita expansões legítimas: cardinalidades não são fixadas no validador. O checkpoint separado `data/research_snapshot_baseline.json` registra contagens aceitas para este snapshot (30 bases, 14 destinos, 65 atrações canônicas, 30 registros DQ3.2 em 23 cidades e 34 rotas exploratórias). Quando o catálogo crescer, a estrutura deve continuar válida, mas a pipeline falhará até que o baseline versionado seja atualizado em PR revisado, com fonte e justificativa. O teste comprova ambos os comportamentos e verifica aliases semânticos na mesma cidade.
