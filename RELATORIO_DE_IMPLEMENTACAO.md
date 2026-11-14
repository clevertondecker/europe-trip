# Relatório de entrega — MVP Streamlit Europa 2027

**Data:** 14/11/2026  
**Etapa:** versão 0.1 — visualização somente leitura  
**Local:** pasta `Europa 2027/50_PAINEL_STREAMLIT` no Google Drive.

## Escopo executado

- Interface com cinco áreas: Visão geral, Mapa & destinos, Roteiro, Orçamento, Pesquisas & decisões.
- Filtros de mapa por país e estágio (proposta / candidata / opcional).
- Indicadores da viagem; links diretos para documentos oficiais do Google Drive.
- Orçamento histórico 60k/70k do casal, reserva já incluída, alerta de folga pequena e simulador de acréscimo de aluguel.
- Livro de dados estruturados local `data/trip.json` compilado dos documentos existentes.
- Documentação, prompt de evolução e testes unitários de dados.

## Verificações realizadas

- `python -m compileall -q app.py data_model.py`: OK (sintaxe Python).
- `python -m unittest discover -s tests -v`: OK, 6 testes executados.
- Verificações: valores 60k e 70k, alteração de aluguel, soma de componentes, filtro geográfico, restrições de datas e coordenadas.
- **Não foi possível executar o processo Streamlit neste ambiente**: o pacote `streamlit` não está instalado e o ambiente não consegue consultar PyPI para instalar dependências. Consequentemente, a renderização final da interface e a execução do mapa **ainda precisam ser testadas em uma máquina com Streamlit instalado**.

## Limitações conscientes do MVP

- Não há conexão automática entre `data/trip.json` e o Google Drive. A conexão usada nesta conversa não é uma credencial da aplicação.
- Não há mapas com rotas multitransporte reservadas, apenas locais e categorias.
- Orçamento exibe simulações de novembro de 2026 e faz apenas cálculo hipotético de alteração no aluguel. Não lê nem recalcula fórmulas do Excel `.xlsm`.
- Sem edição de decisões e pesquisa diretamente pelo Streamlit.
- Foto panorâmica hospedada no Wikimedia Commons requer internet, com licença/crédito no README e rodapé do app.

## Próximo passo técnico

1. Abrir o projeto no Mac e executar os comandos do README.
2. Validar visualmente as cinco telas e mapa, ajustar CSS e ergonomia.
3. Implementar Google Drive API somente leitura por OAuth próprio.
4. Evoluir motor financeiro após mapear fórmulas e categorias oficiais do Excel.
