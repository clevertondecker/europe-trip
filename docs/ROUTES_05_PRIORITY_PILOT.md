# ROUTES 5 — primeiro lote de pesquisa prioritária

Implementação do PR de especificação #114. **Não bloqueia a primeira cesta por #110/#111:** matriz read-only com três cidades-base já cadastradas (Mulhouse, Strasbourg, Lille) e três destinos públicos já cadastrados (Aachen, Baden-Baden, Colônia). Assim são **9 pares**, antes de abrir novos corredores/cidades.

Reutiliza `get_rail_evidence()` e preserva a precedência de observações históricas. Quatro páginas correspondentes de operador foram encontradas e registradas no dataset **separado** `data/corridor_priority_pilot_2026_11.json` como **páginas para pesquisa adicional**, não como horários/viagens específicos, muito menos disponibilidade de 2027. Fontes:

- [Mulhouse–Baden-Baden](https://www.sncf-connect.com/train/horaires/mulhouse/baden-baden)
- [Mulhouse–Colônia](https://www.sncf-connect.com/train/horaires/mulhouse/cologne)
- [Strasbourg–Colônia](https://www.sncf-connect.com/en-en/train/timetables/strasbourg/cologne)
- [Lille–Colônia](https://www.sncf-connect.com/en-en/train/timetables/lille/cologne)

**P1:** usar página genérica como evidência de duração/dia/retorno. Todos os tempos novos permanecem `null` até amostra comprovada; nunca sobrescrever tempo de `get_rail_evidence()`. **P2:** viés por cobertura de pesquisa ou leitura de wishlist privada; cesta é fixa e pública, sem score nem preferências pessoais.

**Dependências:** auditoria #108; contratos #109 são recomendados antes de integrar novas observações cronometradas. Não depende de expandir o cadastro (#110/#111).

**Aceite:** matriz determinística 9/9, URL de referência e data registrada, status honesto, zeros retornos 2027 e nenhum custo para duas pessoas inferido. Próxima rodada pesquisa horário de ida/volta por sábado/domingo, atração aberta e estação exata para poucos pares prioritários; não pesquisa 1.380 pares automaticamente.
