# Polaris beta.11 — candidata interna P20261116.1

Este pacote reúne a Jornada/XP e conquistas, biblioteca unificada, leitura/tradução, melhorias de armazenamento e backups. Ainda não é uma Release pública; a atualização e os dados nos aparelhos aguardam a rodada final.

## Instalação

Há um único APK para Android 8 ou posterior, com ARM32 e ARM64. O Android escolhe a arquitetura compatível. Os dois registros de arquitetura no `manifest.json` apontam para esse mesmo arquivo.

A instalação é por cima da beta.10, preservando seu identificador e assinatura original. Mantenha um backup local pela tela de dados do aplicativo. Se o Android recusar a atualização por assinatura, registre o erro e confira a origem dos APKs; não desinstale para contornar o conflito.

## O que conferir na rodada final

- Atualização, biblioteca, downloads, Jornada e vocabulário existentes.
- Importação de documentos, acesso à pasta escolhida e retomada da leitura.
- Criação e restauração de backup, categorias e progresso, inclusive com um backup antigo.
- Capítulos reais, documentos, tradução e páginas longas nos aparelhos ARM32/ARM64.

A pasta `testes` contém exemplos sintéticos de documentos, idiomas e faixa longa. Eles ajudam a iniciar a conferência; a qualidade de OCR/tradução também exige páginas reais autorizadas.

## Extensões e conta

A sandbox de extensões foi pausada e retirada do aplicativo. O aviso único exige “Estou ciente” e “Terei cuidado, relaxa”. Consulte `ISOLAMENTO_DE_EXTENSOES.md` deste pacote para os riscos atuais. O aviso não isola o código das extensões.

Conta do Polaris, login Google e sincronização em nuvem ficam para outra etapa. Os backups locais continuam disponíveis. Login em sites de leitura é uma função separada.
