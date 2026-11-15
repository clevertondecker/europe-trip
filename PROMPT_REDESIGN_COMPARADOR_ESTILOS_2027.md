# Prompt executado — Comparador de estilos de viagem

## Contexto
Projeto Streamlit clevertondecker/europe-trip. O TripPlan é a única fonte
de verdade para o roteiro aprovado; os três estilos são propostas.
Casamento em 04/09/2027; viagem após essa data, com Itália e França.
Cotações são referências históricas e incompletas para 2027.

## Objetivo
Transformar Simular roteiros em comparador visual, explicável e auditável:
- Cards compactos de Econômico, Equilibrado e Aproveitar ao máximo.
- Quantidade real de destinos, novidades, atrações, datas propostas,
  bilhetes conhecidos, pendências, projeção global e margem.
- Tabela comparativa com fonte nos cenários existentes.
- Destinos presentes em mais de um estilo e exclusivos.
- Mapa de pontos com carregamento sob demanda, sem trajetos inventados.
- Critérios reais e pesos de otimização explicados sob demanda.
- Detalhamento de despesas conhecidas vs verba provisionada, sem duplicar.
- Ações distintas para adicionar sugestão ao roteiro oficial, editar/remover
  rascunho e navegar aos passeios já aprovados.
- Comparativo antes/depois e confirmação com lista de novos passeios,
  atrações e datas antes de aplicar toda a proposta.
- Preservar seletor da aba Orçamento, calendário, salvamento, rollback
  e controles de aprovação, com testes unitários e integrados.
- Nenhuma alteração automática do TripPlan por mudar estilo; somente
  botão explícito de inclusão individual ou aprovação integral pode alterar.
- Não presumir disponibilidade, preço futuro ou economia garantida.
- Evitar trabalhos pesados de mapa na visualização inicial.
- Integrar à main só quando CI aprovado.

## Limites intencionais
Os perfis alteram seleção de passeios, não são três padrões independentes
de hospedagem ou refeições. Na UI, sinalizar parcelas financeiras não cotadas
e valores coincidentes por causa da provisão de excursões.
