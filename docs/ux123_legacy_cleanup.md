# UX123 — Limpeza conservadora das análises legadas

## Objetivo
Retirar comparações e rankings redundantes antes de desenhar a localização definitiva da pesquisa exclusiva. Não iniciar DATA24 nem coletar novos dados.

| Antes | Depois nesta etapa | Destino a decidir |
| --- | --- | --- |
| Comparar mesmas viagens no expander de comparação | Removido deste expander, matriz UX87/97 é a principal | Avaliar chamadas restantes no explorador legado separadamente |
| Ranking editorial de quatro cidades e sliders | Retirados da interface; fontes, riscos, vantagens e anúncios continuam consultáveis | Ficha individual / evidências |
| Comparações lado a lado de 2–3 finalistas e perfis | Removidas; usar comparação moderna | Nenhuma segunda seleção |
| DQ31 pesos e tabela comparativa | Removidos; detalhes de última milha, retorno, fontes e lacunas preservados | DATA24 / logística de destino |
| Pesos Geral/Economia/Explorador no inventário | Retirados da UI, modelo documental histórico preservado | DATA24 calcular cobertura real sem nota editorial |
| DQ32 e matriz documental | Mantidos provisoriamente, identificados como pesquisa histórica | DATA24 |
| Perfis individuais legados e evidências originais | Mantidos provisoriamente; removido comparador duplicado | Conhecer cidade, consolidar campos que ainda faltam |
| Estudos de troca | Mantido renderer completo porque suporta estudos locais, JSON e nuvem privada | Planejar acesso e migração de estudos antes de retirar UX34 não contextual |
| Estudo histórico | Três seções de referências sem ranking; documentos preservados | Migrar informações ainda exclusivas (passe urbano, tarifas condicionadas, custo, contrato, links) |
| Preferências antigas de widgets | Normalização de modos retirados antes da criação dos widgets | Não confundir estado de UI com persistência de decisões |

Não excluir JSONs, fontes, validadores, cálculos financeiros ou modelos históricos utilizados em outros fluxos/testes. UX114/117 revisão oficial e confirmação de troca, UX87/97 comparação moderna, simulações REC04, favoritos, wishlist e TripPlan permanecem. O expander residual é explicitamente temporário. Não apagar os estudos privados.

Teste: atualizar contratos antigos de navegação para verificar as rotas preservadas, ausência dos controles aposentados e nenhuma alteração do planejamento. A suíte de modelos de ranking histórico continua válida porque os arquivos permanecem como evidência histórica. QA visual e CI ainda a confirmar.

A entrada residual preserva o modo de estudos de troca como padrão de compatibilidade, evitando quebrar a recuperação de estudos existentes. O estudo histórico agora também aceita as quatro candidatas DATA23 ao abrir detalhes. Remoção física de módulos e CSS compartilhados permanece condicionada à auditoria de consumidores; a limpeza desta etapa limita-se a código comprovadamente redundante no painel.
