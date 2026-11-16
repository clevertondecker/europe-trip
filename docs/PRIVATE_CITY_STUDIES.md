# Estudos exploratórios privados — implementação inicial

Os estudos UX 3.4 eram apenas rascunhos em `st.session_state`, com exportação/importação JSON. O backup privado UX 3.6 pode incluí-los em arquivo completo, mas isso não proporciona listagem, renomeação, duplicação e exclusão independentes.

Esta entrega usa **o mesmo bucket e identidade de proprietário**, mas um objeto por proprietário `ux36/owners/<sha256(email)>/city_studies.json`, isolado de `current.json`. Um único documento com até 40 estudos versionados protege o limite de tamanho e usa `ifGenerationMatch` para CAS na coleção. Nenhum identificador de proprietário fornecido pelo JSON concede acesso. Estudos não escrevem no `TripPlan`.

Operações: carregar explicitamente; criar a partir da comparação atual; reabrir hipóteses; renomear, duplicar e excluir com confirmação; exportar/importar JSON antigo permanece no painel local. Não há edição implícita de dados oficiais.

**Limites conhecidos:** a coleção tem uma geração única para evitar escrita concorrente silenciosa; conflitos exigem recarregar e reaplicar manualmente. Não há mesclagem automática de dois rascunhos simultâneos, nem fotos/comprovantes privados. E2E real em segundo navegador e falhas de rede dependem de teste humano, não de CI. Campos de pesquisa histórica são recalculados pelo código atual ao reabrir.

**Atenção:** esta branch foi criada sobre `main`; o PR A de autosave deve entrar antes e a branch B deve então ser sincronizada com `main` para teste final.
