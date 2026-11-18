# Implementação ROUTES 2A — diversidade geográfica sem alterar o plano

Especificação de origem: PR #110. A seleção de cidades-base é **somente uma hipótese de pesquisa**; nenhuma cidade é recomendada automaticamente.

- **Cadastradas** (6): Mulhouse, Strasbourg, Lille, Metz, Liège e Freiburg. São diferenciadas por ID usando `load_research()`.
- **Exploratórias não cadastradas** (3): Maastricht, Basel e Amsterdam. Permanecem em um conjunto isolado, fora dos denominadores do comparador. Se entrarem no catálogo no futuro, a análise falha até revisar explicitamente a classificação.
- **Cesta de demonstração fixa**: Aachen, Baden-Baden e Colônia, os mesmos destinos para as seis bases cadastradas. A matriz de 18 pares registra somente tempos históricos/estados, **não** viabilidade.
- **Integrações existentes**: `canonical_place()`, `load_research()`, `build_destination_discovery()`, `load_rail_evidence()`, `get_rail_evidence()`. Não houve alteração em `compare_wishlist_bases()`, nos datasets, `TripPlan`, prioridades ou shortlist.
- **Riscos P1/P2**: confundir candidata ausente com base sem pesquisa, escolher vencedora por volume de fontes, ou comparar cestas distintas. Testes verificam essas invariantes.
- **Próxima etapa**: explorar novas oportunidades em conjunto separado (#111), sem acrescentá-las ao cálculo da cesta original. Moradia e orçamento serão analisados por dados próprios.

**Aceite:** seis registradas e três não registradas, cesta fixa, 18 observações diretas, nenhuma alteração nas escolhas oficiais, todos os `None` explícitos. Sem atualização de UI nem cadastro automático.
