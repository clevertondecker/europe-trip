# UX redesign 2.0 — inventário e migração

Data: 15/11/2026 · Origem: código do repositório `clevertondecker/europe-trip`.

## Problema de usabilidade inicial
O consultor expunha diretamente controles de JSON, ID `trip-...`, SHA/revisões do GitHub, autenticação, exportação e upload. A seleção de atrações ficava em `explore_packages`, datas em `explore_calendar` e planejamento aprovado em `advisor_plan`, exigindo importação manual. O orçamento também dependia do botão de envio do Explorador.

## Fluxo preferido (desktop e mobile)
1. **Minha viagem**: cartão resumindo atrações escolhidas, dias programados e status de salvamento, com ações de exploração, consultor e orçamento.
2. **Explorar destinos / Roteiro → Explorar atrações**: escolher cidades e atrações, interesses e passeios; alterações passam para o único `TripPlan`.
3. **Meu roteiro / Roteiro → Calendário**: visualizar passeios e ajustar janelas, sem reservar.
4. **Consultor de viagem / Roteiro → Consultor inteligente**: cards prioritários e propostas comparadas antes/depois.
5. **Orçamento**: cálculos com o mesmo conjunto de atrações e sem dupla contagem.
6. **Meu planejamento**: salvar online com Google, ou exportar backup opcional; histórico em seção avançada.

## Arquitetura de informação
Mantiveram-se os nomes de valores de navegação para compatibilidade com os links e testes, mas foram simplificados os títulos apresentados no menu lateral: Minha viagem, Explorar destinos, Comparar cidades, Meu roteiro e consultor, Orçamento, Decisões e pesquisas. As áreas antigas de pesquisa Itália/França continuam disponíveis no submenu do Roteiro.

### Estados vazios
- Nenhuma atração: convite para explorar destinos.
- Nenhum alerta: explicar que ausência de alerta não confirma horários de 2027.
- Nenhum planejamento salvo: status "Ainda não salvo".
- Nenhum login: "Backup disponível", com convite para login autorizado.
- Sem dados de rota/preço: informar lacuna em vez de exibir €0 ou economia fictícia.

### Wireframe textual mobile
```
┌──────────────────────────────┐
│ Nossa Europa 2027            │
│ Planejamento: salvo/pendente │
├──────────────────────────────┤
│ Atrações escolhidas          │
│ Dias organizados             │
│ Orçamento do casal           │
├──────────────────────────────┤
│ [Escolher atrações]          │
│ [Melhorar meu roteiro]       │
│ [Ver orçamento]              │
├──────────────────────────────┤
│ 1. Problema mais importante  │
│   Motivo e recomendação      │
│   [Ver detalhes]             │
├──────────────────────────────┤
│ [Salvar planejamento]        │
│ v Histórico e backup         │
└──────────────────────────────┘
```

## Modelo de estado
`advisor_plan` é a representação única versionada da sessão, mantida por `planning_session.py` e ações puras em `planning_store.py`. Compatibilidade com `explore_packages` e `explore_calendar` é derivada, sem importação manual a partir do consultor. Preferências passam a ser armazenadas no próprio plano (campo opcional em schema v1); planos antigos continuam válidos.

## Persistência
Os planos existentes `data/user_plans/trip-*.json` não são alterados automaticamente pela migração. O backend GitHub exige OAuth Google, proprietário autorizado, confirmação da visibilidade pública e controle SHA. A interface apresenta status de salvamento somente após confirmação de escrita. O salvamento automático só é habilitado por opção explícita e não tenta gravar propostas não aceitas.

## Limitações de interface
- A navegação mantém submenus técnicos de roteiros/transportes para não ocultar as pesquisas existentes.
- Streamlit AppTest não substitui validação visual do Cloud Browser.
- O app usa dados de rotas publicados e incompletos para 2026; recomendações para 2027 requerem atualização de fontes.
- Um site público associado a repositório público não deve receber dados sensíveis nos planos.
