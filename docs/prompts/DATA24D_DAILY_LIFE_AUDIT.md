# DATA24D — Auditoria técnica de vida cotidiana

Depende de DATA24A e DATA24C na integração do relatório. Ampliar o mesmo gerador técnico usando round2, city packs, market e perfil canônico. Cobertura por domínio: alimentação/restaurante, cesta local, passes urbanos, clima, serviços/academia quando pesquisados. Distinguir premissa compartilhada do orçamento de evidência específica, unidades/período/pessoas, fonte/data/escopo, não inferir custo local. Contagens de lacunas, estados indeterminados, sem percentuais comparativos no app. Não coletar novos dados, mudar UI/orçamento ou persistência. Testes de ausência, fontes, paridade, determinismo e regressão. CI verde.

## Entrega
Implementar sequencialmente após pré-requisitos. Antes de implementar, atualizar base com alterações integradas ou estabelecer stack revisável; evitar conflitos em app.py e no gerador. Manter draft até código, suíte completa e checks do HEAD confirmados; não mergear sem autorização. Documentar limitações e evidência de testes. DATA25–28 serão definidos a partir dos resultados, não neste PR.

**Status:** especificação publicada; implementação pendente.