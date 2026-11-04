# Compatibilidade de backups e preparação de fontes

Requisito do produto: facilitar repositórios e instalar extensões privadamente sem prejudicar importação/exportação de backups Tachiyomi, Mihon e variantes compatíveis. Beta.9 permanece sem lançamento. Este documento fixa o contrato da implementação futura; não declara novos testes de restauração aprovados.

## Estrutura preservada

A instalação privada muda a localização do código da extensão. Deve preservar pacote, assinatura verificada, identificadores das fontes, URLs e chaves das configurações. Não exige substituir o formato do backup nem recriar a biblioteca.

O código Android atual conserva os campos ProtoBuf de Backup/BackupManga, incluindo fontes, obras, capítulos, categorias, histórico, progresso, favoritos e configurações. O campo106 de Backup guarda repositórios com URL e chave de assinatura. Campos existentes não podem ser renumerados ou reaproveitados.

Dados específicos do Polaris devem ser adicionais e opcionais. A compatibilidade dos campos comuns deve ser testada nos dois sentidos; não se presume que todos os forks compreendam recursos exclusivos do Polaris. O protótipo de backup de obras virtuais mencionado nos checks de CI não será ativado como parte da instalação em lote.

## Restauração antes da preparação online

1. Oferecer importar backup durante a configuração inicial, antes de sugerir repositórios ou instalar fontes em lote.
2. Restaurar os dados selecionados mesmo sem extensões instaladas ou conexão. Manter registros de fontes ausentes e oferecer prepará-las posteriormente.
3. Respeitar repositórios e preferências restauradas. As sugestões não substituem URLs, chaves, credenciais, configurações nem escolhas existentes.
4. Mostrar as fontes necessárias para a biblioteca e as demais disponíveis, permitindo preparar somente as necessárias, todas dos idiomas escolhidos ou uma seleção manual.
5. Solicitar autorização para baixar/executar extensões. Restaurar dados não significa confiar automaticamente em código novo ou em assinaturas diferentes.
6. Uma falha de download, repositório indisponível ou extensão obsoleta não remove obras, progresso ou configurações restauradas. Repetir a preparação não repete a importação nem cria cópias da biblioteca.

Manter a identidade original ao instalar a mesma extensão privadamente. Uma fonte substituta com identificador diferente exige um fluxo de migração próprio; sem inferir correspondência apenas pelo título ou sobrescrever silenciosamente a origem. A sequência lógica de capítulos na interface não autoriza descartar registros de edições no backup.

Backups de biblioteca e preferências não devem ser apresentados como cópias dos APKs das extensões, de todos os arquivos de capítulos ou de modelos de tradução. Preservar o comportamento de cada formato efetivamente suportado.

## Aceitação obrigatória

- Decodificar backups representativos e anonimizados/sintéticos de versões identificadas de Tachiyomi/Mihon e dos forks que declararmos suportados, usando o codec real.
- Restaurar sem extensão instalada; conferir identidades de fontes/obras, categorias, capítulos lidos, última página, marcadores, histórico e configurações suportadas.
- Preparar a extensão privadamente depois da restauração e confirmar que a mesma obra volta a resolver sua fonte, preservando os dados.
- Exportar do Polaris e restaurar nos aplicativos/versões declarados compatíveis; comparar os campos comuns. Documentar limites dos campos específicos de cada fork.
- Verificar backup sem repositórios, fonte removida, assinaturas divergentes, falha/cancelamento e repetição da preparação, além de restauração em instalação já existente.
- Preservar a extensão anterior quando uma atualização privada falhar. O instalador atual precisa de substituição segura antes da instalação em massa: hoje remove o arquivo de destino antes de concluir a cópia do novo.

A compatibilidade ampla é uma meta com matriz de versões e resultados, não uma garantia para qualquer backup de qualquer fork. Os ensaios de layout/OCR já realizados não substituem esta aceitação.

## Primeira evidência pelo codec

A [rodada de interoperabilidade de 04/11/2026](../integration/backup-interop/20261104/README.md) passou em seis testes do decodificador e mapeamentos reais do Polaris, com arquivos sintéticos dos DTOs fixados de Tachiyomi v0.15.3 e Mihon. Os dois leitores de referência aceitaram as reexportações e conferiram os valores comuns. A rodada identifica explicitamente campos não preservados e formatos não ensaiados; a restauração em banco e a preparação de fontes privadas continuam pendentes. Não houve mudança no formato de produção nem publicação da beta.9.
