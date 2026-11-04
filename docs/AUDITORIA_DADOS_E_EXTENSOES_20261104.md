# Auditoria inicial de dados, backups e extensões

Revisão estática de 04/11/2026 após os testes de interoperabilidade. Os três achados P1 receberam correções no candidato interno P20261104.3; veja [implementação e evidências](../integration/safe-storage/20261104/README.md). Os trechos abaixo registram o diagnóstico anterior. Isso não declara auditoria completa de segurança ou aceitação em todos os aparelhos. A beta.9 permanece sem lançamento. Os seis testes de codec e os dois leitores de referência continuam sendo evidência separada da restauração no banco e do instalador Android.

## P1 — preservar a extensão funcional durante atualização

**Achado antes da correção:** `ExtensionLoader.installPrivateExtensionFile` executa `target.delete()` antes de `copyAndSetReadOnlyTo`. O tratamento de erro também apaga o destino. Uma falha após a remoção pode deixar a fonte sem seu arquivo anterior. O helper de cópia também remove o destino em sobrescritas; trocar somente a chamada externa não resolve a sequência.

**Correção implementada no candidato .3:** escrever e conferir um arquivo temporário no mesmo diretório, finalizar a gravação e somente então substituir o destino de modo seguro, com exclusão mútua para operações do mesmo pacote. Preservar a exigência de arquivo somente leitura no Android14+. Comunicar instalação concluída depois da substituição; remover somente temporários na falha. Atualização, cancelamento e desinstalação precisam de coordenação para não ressuscitar uma fonte removida durante a cópia.

**Aceite:** falhas de leitura/gravação, pouco espaço, cancelamento e reinício durante a preparação conservam a extensão anterior; sucesso substitui integralmente o conteúdo. Arquivos temporários não são carregados como extensões. Testar efetivamente Android8 e14+, versões/assinaturas divergentes e duas operações simultâneas no mesmo pacote.

## P1 — retenção de backups após concluir o novo

**Achado antes da correção:** `BackupCreator.backup` remove backups excedentes antes de criar/escrever o novo. O limite atual é4; a preparação conserva3 e elimina os mais antigos. Se a nova escrita falhar, a retenção já terá sido reduzida. Isso não significa que todas as cópias anteriores são removidas.

**Correção implementada no candidato .3:** limpar backups excedentes somente depois de concluir e conferir o novo, protegendo os arquivos anteriores em caso de falha. Revisar nomes com precisão de minuto para duas gravações próximas; o comportamento de nomes repetidos depende também do provedor de documentos e deve ser testado.

**Aceite:** com4 backups existentes, erro de escrita não elimina nenhum deles; após sucesso, preservar as4 cópias adequadas. Repetir com SAF/provedores de documentos, arquivos com nomes coincidentes e falhas de exclusão/renomeação. Não presumir que operações SAF tenham a mesma atomicidade de arquivos locais.

## P1 — distinguir backup validado de backup que não pôde ser relido

**Achado antes da correção:** a validação por `BackupFileValidator` está em `runCatching` com aviso no log. Uma falha dessa validação não impede o retorno de sucesso ou a atualização do horário do backup automático.

**Correção implementada no candidato .3:** distinguir arquivo inválido/corrompido de falta de permissão ou capacidade do provedor para reler. Um arquivo que falhou ao decodificar não deve ser tratado como cópia verificada. Um destino somente gravável precisa de resultado explícito de verificação indisponível, sem confundir esse caso com corrupção. A retenção deve preservar a última cópia comprovadamente válida.

**Aceite:** simular gzip truncado, protobuf inválido, falha ao fechar/gravar e destino que permite gravar mas não reler. Conferir notificação, horário de sucesso, arquivo produzido e preservação das cópias anteriores.

## P2 — confiança em fontes após restaurar backup

**Comportamento confirmado:** backups podem incluir repositórios e suas chaves de assinatura. `TrustExtension.isTrusted` aceita assinaturas que correspondam às chaves dos repositórios configurados ou a uma confiança manual específica. O carregador rejeita extensões sem assinatura ou sem confiança; atualizações privadas também verificam continuidade de assinatura e bloqueiam versões inferiores.

**Contrato para o novo fluxo:** restaurar repositórios/configurações deve preservar dados sem equivaler à autorização silenciosa para baixar e executar todas as extensões. A confirmação de preparar fontes precisa mostrar quais repositórios fornecerão código. Mudança de chave/autor exige tratamento específico. Identificadores de fonte, pacote e preferências não devem ser reescritos para facilitar instalação.

**Aceite:** backup com repositório novo/chave diferente não inicia instalação em lote por si só; assinatura divergente não substitui a fonte anterior; biblioteca continua restaurável sem extensões. Distinguir na fila fonte baixada, instalada, aguardando confiança e disponível para pesquisa. Arquivo instalado não garante que o carregador o aceitou como fonte utilizável.

## P2 — restauração e instalação em lote ainda precisam de testes de integração

Executar restauração no banco real, com fonte ausente, biblioteca existente, duas restaurações e cancelamento. Conferir categorias, progresso, marcadores, histórico, repositórios e preferências. Em seguida, preparar a mesma extensão privadamente e confirmar que as mesmas identidades continuam resolvendo sem duplicar obras. Instalação em massa deve ter fila limitada, escolha de idiomas, progresso, cancelamento, repetição apenas das falhas e política de atualização escolhida pela pessoa.

A preparação de todas as fontes não pode disparar consultas simultâneas a todos os provedores em cada pesquisa. A busca precisa limitar concorrência, ter prazo por fonte e permitir interromper a operação, inclusive em ARM32 com pouca memória.

## P2 — padrão de OCR e limites de interoperabilidade

A escolha de PaddleOCR como padrão para inglês ainda requer implementação da resolução por idioma e preservação da escolha manual. Hoje o padrão armazenado é ML Kit e o fluxo pode interromper uma tradução se Paddle estiver selecionado para outro idioma. A medição de qualidade favoreceu Paddle nos recortes em inglês, sem validar velocidade/RAM em ARM.

O campo de agendamento `nextUpdate` do snapshot Mihon testado não é preservado atualmente. Backups antigos que dependem de campos legados com numeração0 e outros forks ainda não foram aprovados. O [relatório do codec](../integration/backup-interop/20261104/README.md) descreve exatamente os dois snapshots e o que foi conferido.

## Ordem sugerida

1. Substituição segura dos arquivos de extensão e retenção/validação dos backups.
2. Restauração em banco e preparação privada das fontes sem alteração de identidades.
3. Consentimento de repositórios, fila em lote e atualizações com recuperação de falhas.
4. Busca com limites de recursos, resolução do OCR por idioma e aceitação ARM32/ARM64.

Os checks antigos do GitHub continuam com as pendências de protótipo de backup e preparação do SDK descritas em [CI_DIAGNOSTICO.md](../integration/release-candidates/0.1.0-beta.9/CI_DIAGNOSTICO.md). O candidato .3 recompila os APKs com as correções P1; esses checks antigos continuam sem aprovação.
