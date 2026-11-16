# Prompt — UX 3.9: Revisão completa de usabilidade, mobile e acessibilidade

**Estado:** RASCUNHO A · NÃO FINALIZADO (aguarda revisão UX independente)  
**Evidências:** `app.py` (mais de 1.800 linhas), `ux_navigation.py`, `itinerary_flow_ui.py`, `planning_context_ui.py`, `city_decision_ui.py`, `tests/test_ux33_planning_workflow.py`, `tests/test_ux34_city_decision.py`, `README.md`.  
**Dependência:** UX 3.5 no código real e, idealmente, primeiros fluxos 3.6–3.8 para testar. **Não esperar até o fim para corrigir problemas de acessibilidade críticos já encontrados.**

## Problema e resultado esperado

O projeto já reduziu o número de atividades principais, mas preserva muitos caminhos legados e controles especializados. O código automatiza algumas rotas via Streamlit AppTest; isso não garante que a tela seja compreensível em notebook, celular e com tecnologia assistiva. O README contém ainda uma descrição desatualizada dos menus.

**Resultado humano:** planejar a viagem com baixo esforço cognitivo em desktop e celular, sem perder o contexto, sem depender de termos técnicos ou se perder entre ferramentas parecidas.

## Prompt de implementação proposto

1. Realizar **auditoria real de interface**, se disponível, em telas estreita (~375px), média (~768px) e desktop (~1280px+), e fluxos de teclado/leitor de tela. Diferenciar observação em browser de inferência por `AppTest`.
2. Mapear as jornadas de ponta a ponta com usuários leigos: `Minha viagem → Continuar → escolher passeio → organizar dia → revisar → salvar`; `Explorar → Comparar bases → orçamento → voltar`; `Orçamento → analisar cotação → voltar à visita`.
3. Identificar e remover **controles redundantes**, opções do consultor duplicadas, navegação circular e expander que escondem ação principal. Preservar funcionalidades avançadas em contexto ou seções colapsadas, **sem acrescentar abas principais**.
4. Transformar terminologia técnica em linguagem de viagem: `Meu plano` versus `Alternativa`, `Período sugerido` versus `Data aprovada`, `Reservado` somente com ação externa verificada, `Ainda não cotado` versus `Custo 0`. Indicadores devem ter texto, não apenas cor/ícone.
5. **Mobile-first**: cards de cidades, matriz de impactos, orçamento e calendário adaptam-se a largura pequena sem scroll horizontal desnecessário ou informação truncada. Elementos táteis acessíveis, retorno contextual sempre disponível.
6. Revisar hierarquia de títulos, foco visível, labels de inputs, estados de erro, contrastes, controles de teclado e feedback de carregamento. Observar comportamento real do Streamlit, inclusive `st.rerun`, expander, formulário e componentes condicionalmente renderizados.
7. Garantir **tolerância a falha**: rede indisponível, pesquisa sem fonte, retorno de API com erro, conflito de revisão, recarregamento, navegação para cidade removida. Mostrar opções de recuperação sem descartar o trabalho.
8. Instrumentar **métricas locais sem dados pessoais** para testes: quantidade de ações/trocas de seção, erros, caminhos de retorno e conclusão da tarefa. Não transmitir histórico/itinerário sem consentimento; evitar analytics identificáveis.
9. Atualizar `README.md` e documentação de navegação para refletir as tarefas realmente disponíveis. Arquivar ou sinalizar textos antigos; não remover histórico de decisões.
10. Priorizar correções que **reduzem** elementos e complexidade. Só criar novo componente quando eliminar interação redundante demonstrável.

## Testes e sinais de sucesso

- Para cada jornada, medir baseline real (cliques, trocas de área, rolagem até a ação principal e tempo de conclusão) e repetir depois. **Não inventar porcentagem de melhoria** antes de medir.
- Retorno do orçamento ao passeio em edição exige no máximo uma ação, com filtros e campos ainda presentes.
- Celular: planejamento, seleção de datas, comparação e salvar sem rolagem horizontal de página; o usuário consegue concluir sem zoom ou mouse.
- Fluxos completos keyboard-only, com navegação por foco coerente e erros associados aos campos corretos.
- Simulação nunca vira plano oficial sem revisão/confirmar. Falta de cotação nunca aparece como valor zero.
- Atualizar testes `AppTest` e criar checks visuais/responsivos somente quando um navegador de verdade estiver disponível. Uma suíte verde não prova acesso real ou acessibilidade.
- Teste com pelo menos 2 perfis diferentes (quem já conhece o app e quem nunca o viu). Registrar dúvidas/fricção; se não houver usuário teste, documentar limitação e não afirmar validação humana.
- Comparar opções: revisão incremental do layout **versus** reescrever a navegação; escolher a menor solução que melhore execução de tarefas.

## Escopo e restrições

- Sem mudar `TripPlan`, cálculos financeiros ou protocolos de dados só por estética.
- Sem novas áreas principais, gamificação ou painéis de indicadores sem decisão associada.
- Respeitar `AGENTS_COORDINATION.md`: alterações em `app.py` e arquivos compartilhados somente pelo integrador.
- Nenhuma alteração em dados pessoais, Drive, Secrets ou autorização de publicação.

## Condição de encerramento do roadmap

Se os fluxos 3.5–3.9 estiverem compreensíveis, seguros e medidos, **encerrar a sequência no UX 3.9**. Somente criar proposta de UX 3.10 se evidência real de usabilidade/funcionalidade revelar problema relevante não resolvido por correção simples. Não completar números de versão por estética.

**Entregável futuro:** PR de qualidade e UX, antes/depois de métricas e evidências visuais, documentação atualizada; somente com aprovação A+B e testes.
