# Compatibilidade de backups e preparação de fontes

Requisito do produto: facilitar repositórios e instalar extensões privadamente sem prejudicar importação/exportação de backups Tachiyomi, Mihon e variantes compatíveis. A revisão P20261111.1 está em desenvolvimento, posterior à beta.10 pública. Este documento fixa o contrato de compatibilidade. O assistente está descrito em [Assistente de fontes](ASSISTENTE_DE_FONTES_BETA9.md); os testes do fluxo não declaram a restauração em banco aprovada.

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
- Preservar a extensão anterior quando uma atualização privada falhar. A revisão P20261104.3 implementou a substituição segura; a revisão .4 acrescenta a conferência criptográfica e a vinculação ao pacote, certificado e versão revistos.

A compatibilidade ampla é uma meta com matriz de versões e resultados, não uma garantia para qualquer backup de qualquer fork. Os ensaios de layout/OCR já realizados não substituem esta aceitação.

## Primeira evidência pelo codec

A [rodada de interoperabilidade de 04/11/2026](../integration/backup-interop/20261104/README.md) passou em seis testes do decodificador e mapeamentos reais do Polaris, com arquivos sintéticos dos DTOs fixados de Tachiyomi v0.15.3 e Mihon. Os dois leitores de referência aceitaram as reexportações e conferiram os valores comuns. A rodada identifica explicitamente campos não preservados e formatos não ensaiados; a restauração em banco e a preparação de fontes privadas continuam pendentes. Não houve mudança no formato de produção nem publicação da beta.9.

## Edições favoritas associadas no Polaris

A [biblioteca unificada P20261110.1](BIBLIOTECA_UNIFICADA_P20261110_1.md) preserva os favoritos nativos de cada fonte, capítulos, histórico e categorias. O backup exporta esses registros e uma associação opcional no memo, por fonte/URL. Outro leitor pode mostrar as edições separadas; nenhuma dependência do agrupamento é exigida para acessar os registros nativos. Ainda falta validar a ida e volta pela interface e pelo banco dos leitores externos. A prova local de produção do criador/restaurador e de IDs diferentes está no registro dessa revisão.

## Preferências de extensões isoladas

A [revisão P20261110.3](SANDBOX_PREFERENCIAS_FILTROS_P20261110_3.md) mantém as chaves `source_<id>` e os tipos dos valores no backup. Dentro do Polaris, cada pacote/assinatura tem um armazenamento separado. Configurações antigas ou restauradas não concedem acesso automático a esse conteúdo: a tela da fonte oferece importar explicitamente os campos compatíveis, preservando o arquivo original. Isso inclui eventuais credenciais; confiança em código novo continua sendo uma decisão local.

A seção de configurações de fontes da restauração aceita apenas nomes nativos canônicos com IDs Long, incluindo IDs legados negativos. Nomes arbitrários de arquivos e namespaces internos da sandbox são ignorados. A mudança não altera o Protobuf. A exportação sem configurações privadas omite também chaves obviamente sensíveis das fontes isoladas por uma heurística de nomes; não detecta universalmente todo segredo. Controles e tipos personalizados precisam de aceite específico.

## Sessões e recompensas P20261111.1

[Cookies persistentes isolados](SESSOES_E_ICONES_P20261111_1.md) não integram o backup da biblioteca: os arquivos são privados por extensão/assinatura e cifrados com uma chave local. Restaurar uma biblioteca não transfere automaticamente logins de navegador ou cookies. O progresso de leitura continua no campo existente; as opções de ícone liberadas usam uma preferência StringSet comum adicional. Ícones já escolhidos/restaurados continuam disponíveis. Não há alteração de esquema Protobuf/SQL nem dependência obrigatória desses cosméticos para ler os registros nativos em outro aplicativo.
