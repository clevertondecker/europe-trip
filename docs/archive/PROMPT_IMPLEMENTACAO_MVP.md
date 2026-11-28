# Prompt de implementação executado — MVP Streamlit Europa 2027

## Papel

Atue como engenheiro sênior de aplicações Python/Streamlit, designer de interfaces de viagem e especialista em visualização geográfica e financeira.

## Objetivo

Construir **um MVP executável somente leitura** para o planejamento da viagem Europa 2027, usando como evidência o Google Drive `Europa 2027`. O aplicativo deverá combinar **visual editorial de viagem e fotos/mapa (60%)** com **dashboard de orçamento e decisões (40%)**, seguindo paleta azul-petróleo, areia e off-white.

## Fontes oficiais (não alterar)

- `00_COMECE_AQUI`: guia e hierarquia das fontes;
- `01_ESTADO_ATUAL`: fatos fixos, direções, decisões abertas;
- `02_REGISTRO_DE_PESQUISAS`: classificação de evidências;
- `03_PENDENCIAS_E_PROXIMOS_PASSOS`: questões pendentes;
- `20_BASE_DE_CONHECIMENTO/Europa_2027_Base_COMPLETA.md`: contexto e fontes históricas;
- `10_MODELO_FINANCEIRO/Europa_2027_COMPLETO_ORGANIZADO.xlsm`: cenários, custos e pesquisas detalhadas.

## Funcionalidades da primeira versão

1. Tela inicial com imagem de destino licenciado, indicadores (casamento, viajantes, duração e orçamento), mapa, resumo de etapas, próximos passos.
2. Mapa interativo (pontos reais de cidades, não rotas inventadas), filtros por país e status (roteiro proposto, candidata, passeio possível), tooltip e detalhes com link da fonte.
3. Roteiro/linha do tempo com fases e janela de datas, separando casamento fixo de viagem ainda não reservada.
4. Orçamento visual com cenários de R$ 60.000/70.000 para **duas pessoas**, valores históricos R$ 59.975/69.683 e reservas incluídas. Implementar simulação isolada de aumento hipotético no aluguel e câmbio, sem sobrescrever fontes ou recalcular Excel.
5. Pesquisas, decisões e pendências com links para arquivos originais.

## Invariantes

- Casamento em 04/09/2027; partida somente depois da cerimônia.
- Itália antes da França é uma direção de planejamento e não uma reserva.
- Mulhouse e Strasbourg são opções, não uma escolha final.
- Suíça/Luxemburgo/Alemanha são possibilidades, não visitas compradas.
- Não apresentar simulações de novembro de 2026 como cotações 2027.
- Não depender do RAG local; não assumir que a autenticação do Drive nesta conversa funcione dentro do Streamlit.
- Sem ferramentas de escrita no Drive nesta etapa; fonte original sempre preservada.

## Arquitetura mínima

- `app.py` único app Streamlit com navegação por cinco seções.
- `data_model.py` para validação, filtros e cálculos determinísticos.
- `data/trip.json` como **snapshot derivado**, com data da referência e URLs dos arquivos do Drive.
- `tests/test_data_model.py` com testes de valores, datas, geografia e simulação.
- `requirements.txt`, tema `.streamlit/config.toml` e README de execução local no Mac.
- `PROMPT_DE_EVOLUCAO.md` para mudanças futuras.

## Critérios de aceite

- Fontes e status claros nos componentes.
- Sintaxe Python válida; testes unitários passando.
- Projeto entregue como ZIP dentro da pasta `50_PAINEL_STREAMLIT` no Google Drive, com código-fonte separado para manutenção.
- Status de execução honesto: se Streamlit não estiver disponível no ambiente de execução, não alegar renderização final validada.

## Resultado da execução desta especificação

Código e ZIP foram criados; testes e compilação Python passaram. A renderização do Streamlit deve ser validada em ambiente com dependências instaláveis. Veja `RELATORIO_DE_IMPLEMENTACAO.md` para os limites e o caminho de execução.
