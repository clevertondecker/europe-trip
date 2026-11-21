# UX 6.0 — Direção de produto, decisões e matriz de revisão

**Status:** decisão de produto aprovada para revisão de prompts; NÃO IMPLEMENTADA. Documento referencial da UX 6.1–6.5.
**Repositório:** https://github.com/clevertondecker/europe-trip

## Por que mudar
A experiência antiga tem quatro áreas e treze abas; a wishlist de destinos (`ux502_interests`), a comparação, a seleção canônica (`TripPlan`) e o salvamento são caminhos separados. O teste real demonstrou que uma cidade aparece na lista, mas pode não aparecer no editor de roteiro. Adicionar cópias de lista sem mudar o contrato apenas mascara a separação.

### Evidências do código (rever ao implementar)
- `ux_navigation.py` define 4 áreas / 13 abas e aliases legados.
- `ux504_guided_journey_model.py` apresenta passos lineares e recomenda comparação antes de planejar quando há wishlist sem passeio.
- `ux502_destination_interests_model.py` valida `destination_id` e guarda interesse fora do TripPlan.
- `planning_session.commit_outing()` usa `load_attractions()` canônico e confirmação explícita; `trip01_supplemental_discovery.py` usa overlay apenas exploratório.
- `itinerary_flow_model._validated_choice()` e `catalog_plan_validation.validate_catalog_packages()` exigem 1–5 atrações. `selected_rows()` da etapa francesa descarta visitas sem `packages`.
- `continuity_ui.save_private_now()` salva arquivo de continuidade em GCS via `PrivateArchiveStore`, enquanto o planejamento público pode ser salvo pelo GitHub em outro fluxo. Login OIDC não comprova disponibilidade GCS.

## Decisões de UX (ADR)
| ID | Decisão | Por que | Impacto |
|---|---|---|---|
| UX60-1 | Três áreas: Explorar, Planejar, Orçamento | Reduz sobreposição de Minha viagem e Meu roteiro | UX 6.4 migra 13 abas, preserva aliases |
| UX60-2 | Jornada não linear com próxima ação contextual | A escolha de base/custo/datas não tem ordem fixa | UX 6.4 / guided home |
| UX60-3 | Uma visão de destinos com estados combinados | Evita duas listas de lugares idênticas | UX 6.1 somente projeção |
| UX60-4 | Cidade planejada sem atração obrigatória | O usuário decide visitar cidade antes dos detalhes | UX 6.2 evolui contrato TripPlan, testa migração |
| UX60-5 | Lista/timeline primeiro, calendário detalhado opcional | Trabalho remoto torna os períodos mais úteis que dias isolados | UX 6.3 |
| UX60-6 | Orçamento visível desde descoberta, não passo final | Viabilidade pode mudar decisão de interesse ou base | UX 6.4 |
| UX60-7 | Salvar é capacidade transversal; GCS privado ≠ GitHub público | Evita perder dados ou confundir login com persistência | UX 6.5 |
| UX60-8 | Não inventar evidências de transporte/preço/reservas | Datas são 2027; pesquisa tem graus de completude | Transversal |

## Comparação de alternativas e tradeoffs
- **Incremental antiga:** manter 4 áreas + duplicar wishlist no roteiro + exigir atrações + painéis de calendário/salvamento. Menos mudança inicial, mas maior retrabalho cognitivo e risco de inconsistência.
- **Redesenho escolhido:** 3 áreas + board único de projeção + visita canônica sem atrações + timeline + indicador global de save. Melhor clareza e escalabilidade, mas maior custo de migração, especialmente UX 6.2; priorizar testes de compatibilidade.
- **Não criar uma única tabela persistida universal** para wishlist e TripPlan: eles representam compromissos diferentes. Unidade é de **interface/projeção**, não de armazenamento autoritativo.
- **Não retirar comparação** da UX: é opcional e pode acontecer antes ou depois de planejar visitas.
- **Não exigir salvar a cada passo**: status claro, ação manual e autosave privado só com opt-in, validação segura de geração.
- **Dados de 2027:** duração editorial e viagem indicativa não equivalem a tarifa/horário/retorno confirmado.

## Estados do produto — revisão após análise adversarial

| Faceta | Autoridade | Critério verificável |
|---|---|---|
| Quero conhecer | Wishlist | Favorito/prioridade ativa, sem confirmação de visita |
| No roteiro | TripPlan | Inclusão explícita de cidade; após UX 6.2, 0–5 atrações |
| Atrações escolhidas | TripPlan | Seleção efetiva de pelo menos uma atração |
| Em grupo de viagem | `weekend_groups` validado | Vinculado a grupo, mesmo se período e data ainda pendentes |
| Organizado temporalmente | TripPlan e grupos validados | Período conhecido (não `Ainda não definido`) e/ou data exata confirmada |
| Reservado | Confirmação externa | Nunca inferir a partir de favoritar, planejar, agendar ou agrupar |

Facetas coexistem: Colmar pode estar desejado, no roteiro, agrupado e datado ao mesmo tempo, **mas é uma única cidade e uma visita**. Um grupo `Fim de semana na Suíça` com Basel e Lucerna, `start_date=None` e período não definido **não** aumenta o contador `com período/data`.

**Limites conscientes de escopo:**
- UX 6.3 mantém `assignments: date -> destination_id` para **um passeio francês principal por dia**. Vários destinos podem pertencer a um grupo de fim de semana sem ocuparem individualmente a mesma data; múltiplos passeios no mesmo dia são uma decisão futura e não bloqueiam esta versão.
- UX 6.2 precisa garantir o caminho completo 0 atrações: adicionar → agenda francesa e italiana → grupo → editar → custo pendente → exportar/importar → recuperar. Não usar `packages[dest]=[]` fictício para contornar o contrato.
- UX 6.5 distingue fingerprint de **decisões persistíveis** do fingerprint do **arquivo integral**; navegar não pode exibir falso aviso `Alterações não salvas`.
- UX 6.4 normaliza rotas antigas de arquivos GCS/JSON **antes da validação de navegação**, mantendo validação estrita do conteúdo do plano.

## Cenários de usuário e aceites
| Cenário | Atrito atual | Fluxo esperado | Aceite verificável |
|---|---|---|---|
| A. Primeiro acesso | Muitas escolhas antes de pesquisar | Explorar ou configurar preferências; nada obrigatório | Sem visitas iniciais e sem escrita remota |
| B. Exploração com 6 cidades | Wishlist não se reflete no roteiro | 6 destinos visíveis em Planejar como interesse, 0 visitas confirmadas | Sem duplicação e sem `0 lugares` ambíguo |
| C. Escolha de cidade-base | Comparação tratada como passo obrigatório | Comparar alternativas quando quiser, com custos e incertezas | Trocar simulação não troca base oficial |
| D. Planejamento parcial | Obrigatoriedade de atrações no commit | Adicionar cidade com 0 atrações, completar depois | Mesmo ID, datas/visitas conservadas |
| E. Trabalho remoto | Calendário sugere sem todos os parâmetros | Lista/timeline por etapa, fim de semana e horário declarado | Não supor expediente nem reserva |
| F. Mudança de planos | Remoções e mudanças em módulos diferentes | Ações confirmadas com prévia e impacto | Tirar da wishlist não apaga visita; mudar base não apaga datas |
| G. Retomar dias depois | Login não prova save e public/private confusos | Status GCS global e restauração versionada | Mesmo conteúdo e geração ou aviso de conflito, sem overwrite |

*Contagens de cliques e desempenho real não são afirmados sem medição. Testes com usuários reais e AppTest da UI renderizada são necessários para validar clareza, entendimento e acessibilidade.*

## Dependências e execução sugerida
1. **#167 / UX 6.1** — projeção de destinos; não altera schema, apresenta `Quero conhecer`.
2. **#171 / UX 6.2** — **gate técnico**: ADR/migração do contrato de visitas vazias e catálogo suplementar; depois implementar a edição canônica.
3. **#170 / UX 6.5** — auditoria e status/save transversal; o teste final deve cobrir schema de visita da UX 6.2.
4. **#169 / UX 6.3** — organização por período/data/grupo; depende de visitas válidas e calendário.
5. **#168 / UX 6.4** — consolidação da navegação em 3 áreas; depende das telas anteriores para não apontar links vazios.

**Estratégia de branches:** os cinco PRs foram criados a partir de `main` e ainda contêm apenas prompt. Na implementação, rebase/merge de `main` atualizado para a branch antes de editar; tratar conflitos de `app.py`, `ux_navigation.py`, `itinerary_flow_ui.py` e `continuity_ui.py` conscientemente. Revisar após cada CI, nunca integrar só a especificação.

## Veredito e riscos
- #167 — REDESENHAR: uma projeção, não uma segunda lista persistida.
- #171 — REDESENHAR: evoluir contrato do TripPlan com migração testada, sem criar fantasmas de `packages`.
- #169 — AJUSTAR: timeline default, calendário como modo alternativo.
- #168 — REDESENHAR: 3 áreas, aliases e matriz de compatibilidade.
- #170 — REDESENHAR: status global, salvar/recuperar sem etapa obrigatória.

Principais riscos: perda silenciosa em backup antigo, duplicação de visitas, edição de widgets após instanciação do Streamlit, comparações com destinos suplementares sem transporte, conflitos GCS não tratados, vazamento em GitHub público, mudanças indevidas nas 1.380 relações ferroviárias. Mitigar com validações de domínio, golden fixtures, unit+AppTest, comparação de dados antes/depois e review de segurança.

## Critérios transversais mínimos (Given / When / Then)
- **GIVEN** wishlist com Obernai e Basel **WHEN** renderizo Planejar **THEN** vejo ambos sem auto-commit.
- **GIVEN** cidade sem atrações **WHEN** confirmo no contrato novo **THEN** posso salvá-la/recuperá-la e editar depois.
- **GIVEN** visita com dia definido **WHEN** altero período **THEN** recebo prévia de consequências.
- **GIVEN** abro link antigo **WHEN** a UI de 3 áreas inicializa **THEN** sou levado à função equivalente.
- **GIVEN** GCS 412 **WHEN** salvo **THEN** não perco a versão local nem sobrescrevo servidor.
- **GIVEN** visita foi só explorada **WHEN** acesso orçamento **THEN** valor faltante aparece pendente, não como zero.

**Este documento não autoriza código funcional, merge ou publicação.**
