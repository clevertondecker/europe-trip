# Modelo obrigatório de pesquisa de nova cidade-base — Europa 2027

Use este modelo **antes** de adicionar uma cidade ao ranking. Não copie notas de outra cidade, nem invente valores ausentes. Para incorporar ao aplicativo, preencha os mesmos campos do arquivo `data/city_research_audit_2026.json`, incluindo fonte e status de cada gate, e adicione notas editoriais auditadas a `data/cities_france_2026.json` somente após aprovação do método.

## 0. Identificação
- ID: slug único (ex.: `colmar`)
- Nome / país:
- Data da pesquisa, atualização e responsável:
- Casal: 2 pessoas; 55–65 noites após 04/09/2027; França após a Itália; home office e sem carro
- Tipo: **histórico / triagem / pesquisa de 2027 / oferta confirmada**
- Status: `insufficient`, `preliminary`, `decision_ready` (usar último só após comprovar todos os critérios)

## 1. Imóveis e contratos — MÍNIMO 3 ELEGÍVEIS
Para cada imóvel:
| Campo | Registro |
|---|---|
| URL individual + data de consulta | |
| Endereço / bairro e distância estação | |
| Área, quartos, cozinha e ocupação de 2 | |
| Internet real, mesa e trabalho remoto | |
| Entrada e saída exatas | |
| Duração mínima e elegibilidade documental | |
| Preço base, moeda e unidade | |
| Contas, limpeza, plataforma e outras taxas | |
| Caução reembolsável (fora do gasto líquido) | |
| **Total em EUR para o casal e 55–65 noites** | |
| BRL no câmbio **datado e documentado** | |
| Pagamento, cancelamento, riscos | |
| Confirmação explícita do anfitrião | |
| Validade da cotação | |
| Resultado: elegível / pendente / excluir (porquê) | |

Se não houver três ofertas elegíveis, registrar a deficiência e continuar a pesquisa — **não transformar três anúncios encontrados em três ofertas válidas**.

## 2. Custo cotidiano para 2 adultos
- Cesta de mercado semanal (itens e quantidades iguais para todas as cidades); 8–9 semanas
- Restaurante/bar: cenários de 1,5 / 3 / 4,5 saídas semanais, valores já incluídos no orçamento original
- Transporte local / passes, táxi eventual, academia, serviços
- Despesas por semana, por mês e pelo período exato, identificando origem e período do preço
- Não somar despesas duas vezes no orçamento global

## 3. Mobilidade / excursões
Para 5 destinos realmente desejados: estação inicial e final, acesso a pé/ônibus, trem de ida e última volta no sábado/domingo, preço ida e volta do casal, duração porta-a-porta, fonte da operadora, data de consulta, sazonalidade e riscos de conexão.

## 4. Viagem completa
- Custo porta-a-porta Itália → cidade francesa para duas pessoas e bagagem
- Custo cidade → aeroporto de retorno e voo Brasil (JOI/CWB/FLN/NVT/GRU)
- Impostos e seguros que realmente se aplicam; valores de referência separados das cotações

## 5. Rotina e qualidade de vida
- Bairro real de cada imóvel e disponibilidade a pé de supermercado, estação, academia, farmácia
- Segurança por bairro: observações e estatísticas oficiais separadas de opiniões
- Internet contratada e comprovação de conectividade, ergonomia do escritório
- Vida social e mobilidade após o horário de trabalho no Brasil
- Natureza / atrações com viabilidade sazonal de setembro–novembro

## 6. Critérios e notas
Para cada critério (0–5): definição mensurável, indicadores, fontes, amostra, motivo da nota, limitações; revisão por outra fonte quando possível. Sempre manter **nota editorial histórica** separada da **confiabilidade da pesquisa**.

## 7. Evidências e qualidade
Para cada dado: `valor | unidade | EUR/BRL | tipo de evidência | data de publicação | consultado em | válido para | URL individual | condições | nível de confiança`.

Gates oficiais: `rental_inventory`, `rental_total`, `living_cost`, `intercity`, `flights`, `daily_life`, `eligibility`, `evidence`.

## 8. Auditoria final
- [ ] Mesma cobertura que as cidades já analisadas, sem campos vazios disfarçados
- [ ] Pelo menos 3 cotações elegíveis nas datas reais
- [ ] Contrato e ocupação válidos; custo integral, caução distinguida
- [ ] Sem preços inventados, sem tarifas de 2026 anunciadas como 2027
- [ ] Custos do casal incluem origem, Itália, França e retorno sem dupla contagem
- [ ] Fontes e datas rastreáveis; alterações com histórico
- [ ] Testes automáticos passam; aprovação humana antes de alterar decisão D-004

### Arquivos a atualizar
1. `data/city_research_audit_2026.json` — nova entrada com campos idênticos.
2. `data/cities_france_2026.json` — somente se houver notas editoriais justificadas e aceitas.
3. `RELATORIO_AUDITORIA_CIDADES.md` — resumo das descobertas e lacunas.
4. Executar `python -m unittest discover -s tests -v` e publicar no GitHub.

**A existência de uma cidade no catálogo ou no ranking não significa recomendação de aluguel ou autorização de reserva.**
