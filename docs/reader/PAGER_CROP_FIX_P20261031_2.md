# Bordas e coordenadas de tradução — Polaris P20261031.2

## Diagnóstico confirmado pelo usuário

As capturas de Sobre confirmam **Polaris P20261031.1**, compilado em 31/10/2026 às 20:31 no PC do usuário. Páginas 2, 3 e 4 do capítulo 1.3 de Guilty Library mostram inglês e máscaras/textos em português deslocados no paginado, sem uso de zoom. As capturas das mesmas páginas em tira longa mostram o alinhamento esperado.

O usuário confirmou que **Cortar bordas** estava ativado no paginado e que, ao desligá-lo, a tradução alinhou. Não foi necessário retraduzir. Esse teste identifica o recorte como causa do problema relatado. A sincronização de viewport adicionada em P20261031.1 não resolveu esse caso.

## Por que acontecia

Os arquivos de OCR/tradução usam coordenadas da imagem original. O decoder do paginado pode remover bordas antes de informar as dimensões ao leitor; as coordenadas `s` do SSIV são explicitamente relativas à imagem recortada. As preferências de recorte do paginado e da tira longa são separadas.

Calibrar apenas pela largura não recupera o deslocamento do retângulo removido. Por exemplo, em uma imagem de 1000 px recortada em 100 px de cada lado, uma coordenada original x=100 corresponde à borda visível x=0. Multiplicar pela razão entre larguras não produz essa subtração. O decoder atualmente usado também não expõe os deslocamentos do recorte em sua API pública.

## Comportamento da correção

- Páginas com metadados de tradução são decodificadas com a imagem original, preservando as bordas. Isso mantém a imagem e as coordenadas salvas no mesmo espaço.
- Páginas sem tradução continuam seguindo a preferência de recorte do usuário. A preferência salva não é alterada.
- A regra vale para paginado e tira longa, incluindo a preferência separada de cada modo. As bordas ficam visíveis nas páginas traduzidas; esta correção não implementa recorte com remapeamento de OCR.
- Se uma tradução chegar a uma página que já estava aberta e recortada, o holder solicita uma nova decodificação sem recorte. A camada não é apresentada nas coordenadas antigas durante essa transição. Editar uma tradução sobre uma imagem já preservada não exige nova decodificação.
- O estado de recorte e o trabalho de recarga são limpos ao reciclar o holder. As configurações do leitor explicam por que páginas traduzidas preservam margens.

O identificador em Sobre passa a **Polaris P20261031.2**. Os dados salvos de tradução, o OCR, a fonte tipográfica, os provedores e a biblioteca permanecem. Não há migration15, alteração de esquema ou habilitação de backupv2. A expansão PDF/EPUB/DOCX/TXT e busca federada continua adiada por decisão do usuário.

## Verificação

Quatro testes de política cobrem tradução já salva com recorte solicitado, chegada da tradução em imagem já recortada, preservação da escolha em páginas sem tradução e reciclagem do holder. Esses testes validam as decisões de decodificação/recarga, não a renderização Android completa.

Os resultados de compilação, aplicação do overlay, assinatura e comparação JUnit estão em `integration/reader-translation-ux/TEST_RESULTS.json`. A evidência visual disponível valida o ajuste manual na P20261031.1. O comportamento automático da P20261031.2 ainda precisa ser conferido no emulador Windows.

## Uso e aceite visual

O usuário pode continuar no paginado atual com **Cortar bordas desligado**, conforme o teste que já alinhou a página. Não há necessidade de novo OCR.

Na próxima atualização pelo mesmo CMD (4 e depois 9), conferir **P20261031.2** em Sobre. Reabrir a mesma página no paginado e na tira longa. Ativar a preferência de corte deve manter a imagem original nas páginas traduzidas; páginas sem tradução devem continuar recortando conforme a preferência. Conferir também zoom/deslocamento e, quando possível, uma tradução chegando a uma página já aberta.
