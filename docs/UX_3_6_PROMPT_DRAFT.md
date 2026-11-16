# Prompt — UX 3.6: Meu espaço seguro, recuperar e continuar

**Estado:** RASCUNHO A · NÃO FINALIZADO (aguarda revisão UX independente)  
**Origem:** [issue #30](https://github.com/clevertondecker/europe-trip/issues/30), `city_decision_ui.py`, `city_decision_store.py`, `planning_status.py`, `trip_plan_repository.py`, `planning_session.py`, `itinerary_flow_ui.py`.  
**Pré-requisito:** revisar a implementação **real** da UX 3.5, não somente seu prompt.

## Problema e resultado esperado

O viajante consegue escolher destinos e criar rascunhos, mas parte do trabalho permanece apenas em memória de sessão ou em um arquivo JSON manual. Isso exige entender a diferença entre plano oficial, estudo exploratório, backup e publicação em GitHub **público**.

**Resultado humano:** abrir Nossa Europa 2027 em outro dia/dispositivo e **retomar o mesmo planejamento** com segurança, sabendo o que está salvo, o que ainda é rascunho e o que pode ser perdido.

## Prompt de implementação proposto

1. **Mapeie primeiro** todos os estados e formatos de `TripPlan`, `flexible_visits`, `assignments`, `italy_proposal`, estudos de cidade, calendário 3.5, versões e rascunhos. Identifique quais já são persistentes, quais são `st.session_state` e quais exigem JSON.
2. Faça uma análise de **privacidade, custos e ameaças** antes de selecionar backend. Considere conta autenticada, storage privado de baixo custo compatível com Streamlit Community Cloud, limites operacionais e políticas de recuperação. Não grave estudos privados em GitHub público, logs, analytics ou Drive oficial por conveniência.
3. Crie um **único estado de salvamento** observável no topo contextual: `Salvo`, `Alterações não salvas`, `Salvando`, `Erro`, `Apenas nesta sessão`. Cada rascunho sabe a que revisão pertence e onde está armazenado. Nunca exibir `Salvo` antes do retorno do backend.
4. Implemente a jornada **Continuar planejando**, retomando a etapa/dia/destino/passeio, filtros úteis e estudo sem mudar o plano canônico. Diferencie claramente recuperação de dados efetivamente persistidos do contexto efêmero da sessão.
5. Ofereça **histórico de versões e restauração com pré-visualização de diferenças**, não sobrescreva plano de outra sessão sem resolução explícita de conflito. Restauração não cria reservas e deve mostrar perdas de informação se o catálogo evoluiu.
6. **Autosave opt-in** apenas se o backend seguro e os casos de conflito estiverem comprovados. Se não houver solução privada viável, implemente somente melhoria da exportação/importação local, mais um aviso honesto; não esconda limitações.
7. Não criar aba `Meu armazenamento` obrigatória. Integrar ações em **Minha viagem → Resumo**, **Meu roteiro** e na configuração, com informações técnicas recolhidas e rótulos leigos.

## Integração, invariantes e segurança

- Manter `TripPlan` como fonte única; arquivos legados seguem legíveis. Nunca tratar estudo hipotético como mudança oficial.
- `planning_session` controla commits; usar compare-and-swap/versionamento para evitar perda silenciosa.
- Backend autentica o usuário antes de ler/gravar; validar autorização, expiração e segregação de usuários. Evitar vazamento de URL, notas, reservas ou identificadores.
- Sem alterações em `AGENTS_COORDINATION.md` ownership, OAuth/Secrets ou no Drive oficial sem projeto e autorização.
- Não disparar rede para cada tecla, não quebrar fluxo offline ou sem login: oferecer backup local.
- Reaproveitar `planning_status` e UX 3.5 para sincronizar o estado; nunca criar uma segunda máquina de estados de roteiro.

## Aceite observável

- Novo plano → adicionar passeio → organizar data → salvar → sair/reabrir → **Continuar** leva ao mesmo contexto; todos os dados persistidos permanecem.
- Se backend não estiver disponível, interface informa que o plano está só na sessão e fornece backup; sem falsa garantia.
- Duas sessões editam a mesma revisão: a segunda encontra conflito, vê diferenças e escolhe; nada sobrescrito automaticamente.
- Estudo alternativo salvo/reaberto não troca base oficial e não contamina custos/associações.
- Backup JSON histórico e schema atual validados; entradas maliciosas ou arquivos grandes falham com mensagem compreensível.
- Testes `AppTest`, integração de backend com casos de erro, permissões, logout e concorrência; teste manual desktop/mobile.
- UX: medir cliques para retomar em outro dispositivo, percepção inequívoca do status de salvamento e taxa de recuperação de rascunho.

## Alternativa menor / condição de rejeição

Se custo, confiabilidade e segurança do backend forem desproporcionais à viagem de duas pessoas, **não** construir uma plataforma de usuários. Primeiro reduzir fricção de backup/download, resumir estados e oferecer restaurar em um clique **após upload voluntário**. A revisão UX pode reduzir esta proposta a esse MVP.

**Entregável futuro:** PR próprio após aprovação A+B, com design, testes, demonstração de recuperação e sem merge automático.
