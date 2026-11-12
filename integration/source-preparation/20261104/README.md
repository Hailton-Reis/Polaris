# Assistente de fontes — P20261104.4

Beta.9 / P20261104.4, versionCode 110, Android 8/API 26 mínimo. Publicada como pré-lançamento em 05/11/2026 UTC, substituindo os anexos .2 do rascunho. A beta.8 foi preservada. O aceite completo em celulares continua pendente. [Registro de publicação e downloads verificados](../../release-candidates/0.1.0-beta.9/README.md).

O [guia do fluxo](../../../docs/ASSISTENTE_DE_FONTES_BETA9.md) descreve o uso inicial, restauração de backup antes da preparação, consentimento, sugestões ou link próprio, seleção por biblioteca/idiomas/manual, preparação privada e recuperação de falhas.

## Proteções implementadas

- Repositórios e preferências restaurados não iniciam instalação em lote. Consentimento e seleção pertencem ao fluxo atual, sem adicionar campos ao backup.
- A inclusão de um repositório mostra URL e certificado antes da confirmação, e refaz a conferência antes de gravar. A atualização de metadados não substitui um certificado diferente sem revisão explícita.
- Seleção da biblioteca por sourceId de 64 bits, preservando URLs, categorias, progresso e configurações. Fontes ausentes não provocam exclusão de registros.
- Pacotes de repositórios conflitantes exigem escolha de origem. Extensões incompatíveis com as versões de biblioteca suportadas ou sem download HTTPS são excluídas. Instalações existentes no Android não são convertidas privadamente.
- Fila com dois trabalhadores, prazo por item, cancelamento de pendentes e repetição somente dos itens com falha/cancelamento. As fontes carregadas e as aguardando revisão têm estados diferentes.
- Certificado, pacote e versão são fixados para cada tentativa. A autorização do repositório é conferida antes do download e antes da instalação; a assinatura criptográfica do arquivo preparado é verificada antes da substituição atômica.
- O instalador padrão do usuário não é alterado. A escolha prévia de ocultar fontes adultas é respeitada.

## Evidências e limites

Os resultados finais ficam em `TEST_RESULTS.json`, no comparativo JVM e no registro Android desta pasta. O perfil de empacotamento compila ARM32, ARM64 e x86_64; os splits padrão do projeto continuam incluindo também x86 e universal. O perfil reduz somente os artefatos desta execução para caber no ambiente de compilação.

O controle Android usa os helpers realmente compilados de assinatura e substituição de arquivos, com um APK sintético assinado e outro alterado após a assinatura. Não inicializa o leitor completo, não executa uma extensão real e não valida a interface do assistente. O arquivo de teste não contém obras, dados pessoais ou chave privada. A chave sintética de assinatura permanece fora do repositório.

A aceitação da interface, de repositórios e extensões reais, de aparelhos ARM32/ARM64 e de Android 14+ continua necessária. O resultado de carregamento não garante que o servidor de uma fonte continuará disponível. Não foi implementado rollback de falhas de execução posteriores à instalação de código válido, retomada de APKs de extensões após encerrar o processo, atualização automática sem confirmação ou migração automática para fontes com IDs diferentes.

A [interoperabilidade do codec](../../backup-interop/20261104/README.md) permanece uma evidência separada: seis testes e dois leitores de referência para os campos comuns dos snapshots identificados. Restauração/mescla no banco real, nextUpdate e formatos legados não aprovados continuam pendentes. Não se declara compatibilidade universal entre todos os forks.

## Resultado final

- 707 testes JVM: 690 aprovações e as mesmas 17 falhas anteriores, sem novos erros, testes ignorados ou casos ausentes.
- 52 casos selecionados passaram; 34 casos foram adicionados nesta revisão.
- Dez guardas de aplicação do patch e empacotamento passaram; 219 arquivos do overlay correspondem aos arquivos compilados.
- Os três APKs do perfil e o APK de instrumentação foram gerados. Os dois ARM passaram nas verificações de assinatura, revisão, nome e ícone.
- Quatro controles de componentes passaram em Android 8/API26 emulado: assinatura válida, arquivo alterado rejeitado preservando a extensão anterior, pacote/certificado revistos e substituição atômica somente leitura. A interface completa não foi ensaiada.
- Assets, fontes tipográficas e bibliotecas nativas dos dois ARM são idênticos aos do candidato .3; não foram acrescentados modelos de OCR/tradução. O aumento do contêiner APK está registrado no comparativo de artefatos.

[Resultados completos](TEST_RESULTS.json), [comparativo JVM](unit-comparison.json), [controle Android](android-runtime.json), [artefatos](artifact-check.json). O [reprodutor](../../../scripts/extensions/build_preparation_probe.py) exige um diretório de saída fora de checkouts Git, gera sua própria chave sintética local e nunca instala ou publica o pacote automaticamente. O código Java e o manifesto do controle estão em `android-probe/`.
