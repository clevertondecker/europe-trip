# UX109 — Refinamento visual da ficha individual de cidade-base

## Problema observado
Depois de UX107/108 a página individual ainda mostra um cabeçalho global redundante, KPIs soltos, síntese extensa/repetitiva e títulos de assunto duplicados por expanders.

## Objetivo
Uma ficha de destino compacta, editorial e responsiva, sem duplicar a lógica de pesquisa.

## Escopo obrigatório
1. **Cabeçalho**: em `app.py` suprimir somente o título genérico `Explorar cidades-base` quando `itinerary_section == "Explorar bases"` e o contexto de handoff válido for `profile`. Outros fluxos mantêm o título.
2. **Identidade**: título de cidade já existente; fotografia compacta **somente** com registro exato e licenciado do serviço `ux100_base_card_photos`. Priorizar imagem local; quando houver Commons curado no catálogo, reutilizar `render_base_card_photo()` do UX100 com seu fallback visual e créditos. Sem imagem válida, não reservar espaço em branco. Não fazer hotlink arbitrário nem criar nova cadeia de imagens. Confirmar visualmente a falha externa antes de considerar QA completo. Exibir crédito/autoria/licença. Sem foto, deixar apenas texto e não espaço em branco.
3. **Cards KPI**: reaproveitar duas métricas canônicas de anúncios históricos 2026 e X/Y destinos da pesquisa histórica, distinguindo-os do roteiro escolhido. CSS namespace `ux109-*`; nenhuma alteração em coverage matrix ou ranking.
4. **Síntese curta**: máximo 2 fatos distintos (evidências com proveniência) e 2 lacunas simples; evitar duas frases sobre o mesmo meio de transporte e duas URLs genéricas “Consultar fonte”. Usar nomes de link úteis, não remover referências dos detalhes.
5. **Detalhes**: não repetir `#### Moradia...` imediatamente acima de `Moradia · anúncios...`; deixar **uma entrada visual por assunto** usando `st.expander` atual e manter seções de moradia, transporte, cotidiano, fontes e investigação opcional REC05. Não criar nested expander adicional.
6. **Não quebrar** `fixed_city=None`, `compact=False`, handoffs, favoritos, simulação hipotética, mapa, `CHOICE`, escopo ou `TripPlan`. Preferir ajuste pequeno a novas camadas de apresentação.

## Testes / aceite
- AppTest para Mulhouse, Strasbourg e cidade sem foto/anúncios; confirmar ausência do cabeçalho global só no perfil, dados reais, menos títulos redundantes, origem preservada.
- Outros modos continuam íntegros; ações e keys estáveis.
- `python -m compileall -q .`; `python tools/validate_research_data.py`; `python -m unittest discover -s tests -v`.
- Verificar Streamlit real em 1440/768/390px quando disponível; não alegar QA visual por causa de AppTest.
- Abrir PR draft; sem merge automático.
