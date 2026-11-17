# ARCH 1.4 — Performance baseada em medição

A tela `Explorar → Comparar → Pesos das 30 cidades` construía as métricas
macro do DQ3.2 a cada rerun do Streamlit, carregando repetidamente fontes e
fazendo o join completo entre 30 cidades e destinos. Criamos um adaptador
`arch14_macro_coverage_cache.py` que lê os datasets uma vez por lote de
cidades e guarda **apenas** uma tabela determinística de pesquisa no
`st.cache_data(ttl=300)`. O cache não recebe `TripPlan`, credenciais,
estados de autenticação, seleções privadas ou mutações de sessão.

A mesma interface mantém as colunas e os valores anteriores. A chave do
cache é uma tupla ordenada dos IDs das cidades, de forma que filtro de 12
finalistas e lista das 30 cidades são entradas distintas. O TTL de 300s
limita desatualização quando os dados locais forem recarregados; o deploy
de código invalida a função no Streamlit.

Teste de paridade compara as 30 cidades, ordem/filtro e independência das
respostas cacheadas. Há medição simples com `perf_counter()` sem limiar
de velocidade frágil ao ambiente de CI. **Não afirmamos ganho porcentual**
sem observabilidade em runtime.

Sem exclusão de código legado, alterações em dados, TripPlan, CSS,
rede, login ou deploy. Investigação de outros gargalos (mapas, fluxo
Drive, cache de índices) fica para um pacote posterior com métricas.


## Invalidação e medições

`st.cache_data(ttl=300)` expira automaticamente cada resultado aproximadamente 300 segundos depois de criado. Além disso, a chave inclui a tupla ordenada de cidades; alterações nessa entrada obtêm outro valor. `cached_macro_coverage_rows.clear()` força invalidação manual (testada). Após um novo deploy de código, o cache de função pode ser invalidado; **não depende disso como única garantia**. A ausência de mudanças no código não invalida imediatamente um arquivo JSON alterado em disco antes do TTL; esse é um limite explícito do contrato.

O teste `test_cache_cold_warm_and_explicit_invalidation` emite `ARCH14_CACHE_BENCHMARK` com três durações em milissegundos para as 30 cidades (cache frio, cache quente e após `clear`). São amostras de CI, não latência em produção nem SLA. Registrar os valores verificados no relatório após o CI.
