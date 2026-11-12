# Polaris 0.1.0-beta.10 — APK universal e recuperação de fontes

**Pré-lançamento público para testes · P20261106.1 · código 111 · Android 8 ou superior.**

## Baixar e instalar

Baixe **Polaris-0.1.0-beta.10-universal.apk** (261,1 MB). É um único APK para ARM32 e ARM64: o Android escolhe as bibliotecas compatíveis na instalação. Não inclui x86/x86_64. Os recursos comuns são compartilhados no pacote; não há download de uma segunda versão.

A assinatura e o identificador são os mesmos da beta.9 distribuída. Instale por cima do Polaris. **Guarde seu backup original**, sobretudo antes de testar restauração ou mescla de fontes. Não desinstale para contornar conflito de assinatura. Para localizar esta versão pelo app, ative **Receber atualizações experimentais**.

## O que mudou desde a beta.9

- Um APK universal substitui os dois downloads por arquitetura. O pacote é cerca de 97,3 MB menor que a soma dos dois APKs anteriores.
- A lista de capítulos da fonte principal é salva antes da descoberta de alternativas, evitando esperar essa busca para mostrar o que já chegou.
- Recuperação após restauração procura alternativas para fontes ausentes, inclusive em obras antigas/concluídas. Usa extensões autorizadas e habilitadas, confirma identidade e numeração e respeita a fonte fixada pela pessoa.
- A descoberta verifica amostras de páginas e bytes de imagem. Entre fontes com amostra aprovada, prioriza português nos idiomas habilitados. Habilite português/português brasileiro nos filtros para incluí-los.
- Quando a lista de páginas falha, o leitor pode tentar até três edições já confirmadas do mesmo capítulo, respeitando fonte fixa e modo somente baixados.
- Menos carregamentos simultâneos, cache e threads do PaddleOCR em processos de 32 bits ou com pouca memória. Sobre mostra informações de compatibilidade para ajudar no diagnóstico.
- Inspeção preventiva de extensões antes do carregamento, quarentena e aprovação vinculada à versão exata. Preferências internas de confiança não são importadas de backups; repositórios novos restaurados exigem revisão local.
- Proteção de caminhos e exigência de HTTPS para downloads de plugins de novels.

Mantém o assistente de repositórios e instalação interna em lote, as melhorias anteriores de OCR/tipografia, a tradução no aparelho e os downloads recuperáveis de atualização. Nenhum novo modelo de OCR foi acrescentado nesta versão.

## Limitações conhecidas

**A sandbox completa de extensões ainda não está integrada.** As extensões atuais executam no modo de compatibilidade, no processo do aplicativo, com aviso. A inspeção preventiva pode bloquear código legítimo e não detecta todos os riscos; uma assinatura ou inspeção sem alertas não garante segurança. A prova de isolamento Android foi feita em componente separado, sem extensões reais.

**A exportação de obras mescladas para Mihon/Tachiyomi ainda precisa de normalização e validação real.** Alguns capítulos alternativos usam URLs específicas do Polaris. O formato de backup continua existente, mas isso não garante que essas obras funcionem ao voltar para outro leitor. Preserve o backup original; o campo Mihon `nextUpdate` também não é preservado.

O problema relatado no A12 ainda não teve sua causa confirmada nem aceite no aparelho. Não há medição que comprove ganho de velocidade ou memória nele. A amostragem de fontes não testa todos os capítulos nem a qualidade editorial. Falhas que surgem apenas em imagens posteriores ainda não têm recuperação completa. O fluxo com extensões reais, extensões já instaladas pelo Android, Android 14+ e migração por banco/UI continua em validação. A fila de preparação de extensões depende do processo e não retoma seus downloads depois que ele é encerrado.

## Validação

738 testes JVM: **721 aprovações e as mesmas 17 falhas preexistentes**, sem novas falhas, testes ausentes ou ignorados. Os 31 casos novos passaram. Também passaram 13 controles do empacotamento/overlay e seis verificações Android de um componente independente de isolamento. Esses resultados não representam uma suíte totalmente verde nem aceite do aplicativo completo em celulares.

O APK foi conferido contra as 240 alterações de fonte compiladas e manteve a assinatura da beta.9. O manifesto oferece dois descritores de arquitetura apontando ao mesmo arquivo para compatibilidade com o atualizador antigo; há apenas um APK.

SHA-256 do APK:
`f1a556d2620a5984c76cebe2dc5a10e461d8d5a2feb6a91018371beaec0a90da`

[Implementação e evidências](https://github.com/Hailton-Reis/Polaris/tree/v0.1.0-beta.10) · [Registro de testes](https://github.com/Hailton-Reis/Polaris/blob/v0.1.0-beta.10/integration/universal-recovery/20261106/TEST_RESULTS.json) · [Relatar problema](https://github.com/Hailton-Reis/Polaris/issues/new/choose)

Ao relatar problema, envie a versão copiada em Sobre, Android, aparelho, fonte/extensão e os passos para reproduzir.
