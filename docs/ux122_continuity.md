# UX122 — Continuidade e limpeza da jornada Planejar

## Inventário de rotas
| Antes | Agora | Contrato |
| --- | --- | --- |
| Sidebar global + botão de revisão + botão de cópia privada | Sidebar: Salvar minha viagem | Mesmo writer save_private_now, geração otimista, fingerprint completo; sem botão quando confirmado |
| Backup dentro da revisão/Visão geral | Sidebar: Cópia e recuperação, em todas as tarefas | Mesmo schema, prévia, confirmação e cancelamento; restauração local desativa autosave até novo opt-in |
| Autosave duplicado | Cópia e recuperação | Mesmo estado canônico, desligado por padrão |
| REC05 no painel de revisão | Pesquisas e decisões (atalho na Visão geral), fila por prioridade | Modelo, fontes e exportação mantidos |
| Ferramentas complementares | Explorar > Comparar bases / Minha lista; Planejar > Meus destinos; Orçamento | Board de situação preservado na área proprietária; orçamento usa rota oficial |
| Propostas italianas e guias, mapa, simuladores | Rotas existentes e atalhos específicos da Visão geral | Sem alteração de contratos de pesquisa |
| Calendário e viagens agrupadas | Organizar | Aceitar novo modo de navegação no arquivo sem alterar fingerprint de decisões |
| Outras etapas e deep links | Manter atalhos de inclusão, revisão e organização existentes | Compatibilidade de callbacks; não criar wizard obrigatório |

O resolver visual é somente leitura e usa fingerprint de decisões confirmadas + geração + disponibilidade real do store. Erro/conflito têm prioridade. Save manual rerun único; não reenvia snapshot confirmado e não marca sucesso com geração inválida. A restauração tem vínculo com identidade e fingerprint de prévia, valida antes de mutar, preserva os estudos sem transformar propostas em decisões. Nenhum write público foi adicionado.

Testes de UI, armazenamento simulado, reabertura em sessão nova, modo agrupado, status e falhas. QA visual real (1440/1024/768/390px) e teste contra bucket de produção não foram realizados; não confundir mocks e CI com validação remota real.
