# Auditoria — Explorar → Passeios por cidade-base (17/11/2026)

## Causa raiz confirmada

O seletor `base_options()` oferece **30** cidades da pesquisa ampliada, mas `attractions_ui.render_explorer()` só apresentava os cards de atrações se a base estivesse no conjunto `{mulhouse,strasbourg,metz,nancy}`, por depender da matriz `base_destination_routes_2027.json`. Para todas as outras **26 bases**, a tela mostrava aviso e executava `return`, escondendo **65 atrações em 14 destinos** já existentes no catálogo. Essa era uma limitação de integração/UX, não evidência de que não existam passeios nas cidades.

Há três níveis de dados, que NÃO devem ser equiparados:
1. `data/attractions_2027.json`: **14 destinos, 65 atrações** e descrições/fotos/visitas; não contém automaticamente pesquisa de saída de 30 cidades-base. Nem todas as cidades candidatas são destinos turísticos próprios desse catálogo.
2. `data/base_destination_routes_2027.json`: matriz **4 × 14 = 56 pares**, dos quais **14** registram duração de trem (4 Mulhouse, 5 Strasbourg, 2 Metz e 3 Nancy). Não possui tarifa/retorno 2027 confirmado.
3. `data/exploration_bases_2027.json`, `data/base_city_rail_evidence_expanded_2026_11.json`, `data/five_base_comparison_evidence_2026_11.json`: amostras de ligações históricas para várias bases adicionais; **não** equivalem à matriz completa de passeio, podem ter destinos fora dos 14 canônicos e não certificam retorno ou última milha.

### Situação da pesquisa (30 bases)

`Tempos fora da matriz` significa haver ao menos um destino, em qualquer fonte histórica examinada, com tempo documentado. `No catálogo de atrações` conta destinos distintos **entre os 14** com algum tempo observado; não representa score de mobilidade e não prova viabilidade 2027. Dados de documentos diferentes podem ter recortes e datas incompatíveis; não foram agregadas tarifas nem itinerários de volta.

| Cidade-base | Na matriz de passeios | Algum tempo ferroviário histórico | Destinos do catálogo com tempo (de 14) | Diagnóstico |
|---|---|---|---:|---|
| Mulhouse | Sim | Sim | 8 | Matriz parcial; faltam muitos retornos e última milha |
| Strasbourg | Sim | Sim | 11 | Matriz parcial; referências adicionais dispersas |
| Metz | Sim | Sim | 4 | Matriz parcial |
| Nancy | Sim | Sim | 4 | Matriz parcial |
| Lille | Não | Sim | 4 | **P1**: 8 trechos amostrados, tela ocultava dados |
| Offenburg | Não | Sim | 2 | **P1**: há referência Strasbourg/Freiburg |
| Karlsruhe | Não | Sim | 1 | **P1**: há referência Strasbourg |
| Dijon | Não | Sim | 0 | **P1/P2**: rotas para Beaune/Lausanne/Lyon fora dos 14 destinos canônicos |
| Trier | Não | Sim | 1 | **P1/P2**: o adaptador concilia `luxembourg_city` com o destino `luxembourg`; ainda requer retorno e acesso |
| Aachen | Não | Sim | 0 | **P2**: dado Cologne fora do catálogo |
| Reims | Não | Sim | 0 | **P2**: dado Amsterdam fora do catálogo |
| Arras | Não | Sim | 0 | **P2**: dado Lille fora do catálogo |
| Besançon | Não | Sim | 0 | **P2**: dado Dijon fora do catálogo |
| Freiburg im Breisgau | Não | Não | 0 | **P1**: shortlist sem trechos históricos nos datasets selecionados |
| Liège | Não | Não | 0 | **P1**: shortlist sem trechos históricos |
| Colmar | Não | Não | 0 | Falta pesquisa saindo da base; Colmar já tem atrações como destino |
| Sélestat | Não | Não | 0 | Falta pesquisa de saída |
| Saint-Louis | Não | Não | 0 | Falta pesquisa de saída |
| Belfort | Não | Não | 0 | Falta pesquisa de saída |
| Thionville | Não | Não | 0 | Falta pesquisa de saída |
| Haguenau | Não | Não | 0 | Falta pesquisa de saída |
| Saverne | Não | Não | 0 | Falta pesquisa de saída |
| Kehl | Não | Não | 0 | Falta pesquisa de saída |
| Baden-Baden | Não | Não | 0 | Falta pesquisa de saída |
| Saarbrücken | Não | Não | 0 | Falta pesquisa de saída |
| Lörrach | Não | Não | 0 | Falta pesquisa de saída |
| Arlon | Não | Não | 0 | Falta pesquisa de saída |
| Namur | Não | Não | 0 | Falta pesquisa de saída |
| Luxembourg City | Não | Não | 0 | Base `luxembourg_city`, destino turístico `luxembourg`; falta tabela de saída |
| Esch-sur-Alzette | Não | Não | 0 | Falta pesquisa de saída |

> Nota: a coluna `Algum tempo` considera todos os destinos das amostras, inclusive os que não existem nos 14 destinos do catálogo de atrações. Não concluir que as 17 bases sem tempo observado são mal conectadas — só não pesquisadas nos dados analisados.

## O que o PR melhora imediatamente

- **Todas as 30 cidades selecionáveis** passam a oferecer uma visão de **14 destinos e 65 atrações já catalogadas**, em formato **somente leitura** quando fora das quatro bases canônicas.
- Indica os pares com tempo histórico de ida quando já disponíveis (do adaptador `rail_evidence_unified_model` ou da base exploratória), com link à fonte.
- Mostra destinos sem tempo como `Rota ainda não pesquisada`, e custo do casal, duração de retorno e última milha como desconhecidos.
- Nenhuma tarifa de outra base, soma de preços, viagem gratuita, score de viabilidade ou escolha do usuário é reutilizada/inferida.
- **Não** altera a matriz canônica, `TripPlan`, reservas, orçamento, fotos, CSS ou dados de pesquisa.

## Próximas melhorias de dados, em ordem sugerida

**Onda A — fechar shortlist com lacunas evidentes:** Freiburg e Liège (sem tempos observados); Trier, Aachen e Dijon (amostras só para destinos fora do catálogo); completar Lille, Offenburg, Karlsruhe contra destinos de interesse comuns. Pesquisar corredores com TER/SNCF, DB, SBB e SNCB. Para cada par registrar estação de partida/chegada, data e tipo de dia (sábado/domingo), ida e retorno, trocas, tempo típico e mínimo, tipo de bilhete e tarifa normal do casal quando verificada.

**Onda B — atrações locais:** diferenciar *cidade-base* de *destino do catálogo*. Por exemplo Lille, Arras, Dijon, Trier e Aachen são candidatas a base, mas não têm fichas de atrações próprias no catálogo de 14 destinos. Pesquisar atrações locais com ID canônico, fonte de turismo, duração de visita (editorial e identificada), entrada e acesso, sem duplicar o catálogo; submeter em PR próprio.

**Onda C — comparar adequadamente:** mesma cesta de destinos por base, frequência, retorno de domingo, último trem, distâncias pedestres (os dados geográficos DQ 3.0/P3 continuam incompletos), tarifa normal para duas pessoas e pernoite quando indicado. Não criar ranking único enquanto cobertura for assimétrica.

## Validação

`tests/test_outing_base_coverage.py` cobre as 30 cidades, preservação das 65 atrações, tempos/fonte de Lille, Offenburg e Karlsruhe, ausência de dados para Freiburg, deslocamento local sem preço zero, rejeição de cidade inválida e dados originais imutáveis. Testes do projeto devem passar antes de integrar. Uma verificação visual real no Streamlit ainda dependerá de navegador.

O PR é **incremental de UX e integração read-only**, não uma promessa de que todas as 30 cidades agora tenham tempos ferroviários verificados.
