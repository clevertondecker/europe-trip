# UX118 — Corrigir foto compartilhada de Metz

## Diagnóstico
UX117 exibia fallback com crédito LuxFoto09. O consumidor UX100 consultava diretamente o catálogo histórico, ignorando a correção de `preferred_destination_photo` já utilizada na descoberta UX501.

## Ajuste
Reutilizar essa resolução no fallback do catálogo UX100, preservando precedência dos arquivos WebP locais e dos registros Commons curados. Não duplicar a exceção de Metz nem modificar o catálogo histórico, os outros destinos ou o CSS. Imagem de centro histórico/catedral confirmada em Commons:
- https://commons.wikimedia.org/wiki/File:Metz_centre_ville_crop.jpg
- https://upload.wikimedia.org/wikipedia/commons/3/36/Metz_centre_ville_crop.jpg
- Philippe Gisselbrecht / Ville de Metz, CC BY-SA 4.0.

## Validação
Teste de igualdade com a resolução UX501, URL, créditos, licença, fallback e preservação das fotos existentes. Executar CI completa. Confirmar a foto publicada no navegador após deploy; o recurso é remoto e o fallback continua necessário. Não ampliar escopo nem adicionar consultas de rede durante resolução.
