# Extensões: isolamento, compatibilidade e quarentena

Decisão do mantenedor em 06/11/2026, America/Fortaleza: permitir um modo de compatibilidade opcional para extensões antigas, com aviso explícito de execução fora da sandbox. A beta.9 pública permanece inalterada. Esta análise não declara um executor isolado concluído.

## Limite atual confirmado no código

O `ExtensionLoader` cria um `ChildFirstPathClassLoader` e instancia a extensão no processo do Polaris. A extensão privada é um APK guardado internamente, mas seu código compartilha o UID, memória e permissões do aplicativo. Guardar o arquivo privadamente, verificar a assinatura ou usar outro class loader não cria uma sandbox.

A assinatura criptográfica comprova integridade e identidade do signatário; um autor confiável ainda pode distribuir um bug, ser comprometido ou publicar código malicioso. A proteção do Android em relação a outros aplicativos continua existindo, mas não separa o Polaris das extensões executadas dentro dele. Extensões já instaladas como aplicativos Android também têm uma existência fora do Polaris: o leitor não controla o que esses aplicativos fazem por conta própria.

## Camada preventiva implementada na candidata P20261106.1

Antes de criar o class loader, o carregador inspeciona os arquivos DEX do APK, bibliotecas nativas e permissões declaradas. Capacidades selecionadas exigem revisão: comandos/processos, código executável adicional, provedores de dados do Android, APIs de controle do aparelho/instalação e permissões sensíveis. A leitura tem limites de tamanho, quantidade de entradas e tabelas; erro de inspeção mantém a ativação bloqueada.

O aviso **Em quarentena** lista os motivos. É possível manter a extensão instalada e inativa, excluir ou, quando o código pôde ser inspecionado, aceitar explicitamente aqueles mesmos bytes. A aprovação é vinculada a pacote e SHA-256; uma atualização diferente não herda a exceção. As preferências de aprovação usam `Preference.appStateKey`, excluído da exportação normal de preferências do backup. O estado não autoriza automaticamente repositórios restaurados.

A restauração também ignora chaves de estado interno inseridas manualmente num arquivo. Repositórios novos ou com certificado diferente trazidos pelo backup ficam pendentes de revisão local: os campos portáveis são preservados, mas não passam a conceder confiança aos APKs instalados. Uma segunda importação não remove essa pendência. O guia de preparação libera somente as identidades escolhidas num lote confirmado; a confiança individual explícita continua disponível. Um repositório que já tinha a mesma identidade revisada neste aparelho conserva sua decisão local.

Os plugins JavaScript de novels têm outro carregador. Esta inspeção de DEX não certifica seus scripts. A candidata valida seus identificadores e caminhos para impedir que metadados de repositório escolham arquivos fora da pasta de plugins, e exige HTTPS na URL de download e no destino final. Assinatura de scripts, limites completos de recursos e isolamento desse runtime continuam exigindo uma etapa própria. O código de quadrinhos em compatibilidade também pode alcançar APIs do host; recursos como Shizuku reforçam a necessidade de uma fronteira de processo real.

Essa análise é estática e conservadora: referências podem existir sem serem executadas; reflexão, ofuscação e outras técnicas podem ocultar comportamentos. **Não é detecção de todas as tentativas de invasão, prova de ataque nem garantia de segurança.** Uma extensão sem achados ainda executa no modo de compatibilidade atual. A interface informa esse limite e identifica versões cujo risco foi aceito. Código ilegível não recebe uma exceção por essa interface.

## Executor isolado: critérios antes da adoção

O isolamento efetivo deve usar um serviço Android com `android:isolatedProcess="true"`, sem permissões herdadas do aplicativo, e uma API pequena de comunicação entre processos. Um processo comum com outro nome ainda compartilha o UID e não atende a esse requisito.

1. O processo isolado recebe somente o APK aberto para leitura e os dados necessários à operação atual. Não recebe banco, diretórios, objetos `Context` do host, credenciais globais ou um `NetworkHelper` do processo principal.
2. Metadados, capítulos, páginas, filtros e preferências precisam de contratos de IPC com limites de tamanho, paginação, validação, cancelamento e prazo. Não se devem serializar objetos arbitrários da extensão ou expor o contêiner de injeção de dependências do host.
3. O acesso HTTP deve passar por um intermediário com identidade de extensão e autorização da sessão. Cookies e preferências são separados por extensão. Endereços locais/privados, esquemas inesperados e redirecionamentos precisam de controle no intermediário; não basta conferir a primeira URL.
4. No Android 8, um processo de trabalho deve atender uma extensão por vez, descartando o processo antes de reutilizá-lo para outra. APIs mais novas de serviços isolados não podem se tornar um requisito silencioso que elimine ARM32/API26.
5. Extensões que dependem de arquivos privados do host, bibliotecas nativas não autorizadas, WebView ou outras APIs incompatíveis precisam de adaptação ou da escolha explícita do modo de compatibilidade. Falha do executor isolado não deve executar código automaticamente no host como reserva.
6. Pedidos bloqueados pelo intermediário podem produzir eventos auditáveis e quarentena, com motivo e ação de manter/excluir. Uma falha HTTP, demora ou fechamento do processo não deve ser apresentado como invasão comprovada. O aplicativo não consegue observar universalmente toda tentativa de acesso feita diretamente ao Android.
7. A interface deve identificar **Isolada**, **Compatibilidade: sem isolamento** ou **Quarentena**, sem chamar uma extensão de segura por não ter disparado alertas. A candidata atual ainda não apresenta o estado Isolada, pois não há executor integrado.

## Aceite necessário

Uma prova independente já executou **seis verificações em Android 8/API26 x86_64**, com o processo principal no UID10065 e o serviço isolado no UID99000. O serviço não herdou a permissão de internet, não leu nem alterou os arquivos privados sintéticos do processo principal, não conectou diretamente ao socket de teste e recusou um comando IPC não previsto. [Fontes, reprodução e resultados](../integration/extension-isolation/20261106/README.md).

Isso comprova a fronteira de isolamento desse componente, **não um executor integrado de extensões no Polaris**. O teste usa um APK próprio de 17KB, sem obras ou dados pessoais; não inicia o leitor, não executa uma extensão real e não valida desempenho ARM, Android14+, o intermediário HTTP ou a interface de quarentena.

Os testes precisam executar código de extensão real no UID isolado e demonstrar negação de leitura/gravação do banco e preferências do host, acesso a arquivos não fornecidos, instalação/controle do aparelho e acesso direto à rede. Também precisam cobrir pedidos IPC inválidos, resposta excessiva, redirecionamento para rede privada, separação de cookies e preferências, cancelamento, consumo de memória/CPU, encerramento e reinício. O fluxo deve ser conferido em Android 8 e 14+, ARM32 e ARM64.

A prova deve verificar que o caminho normal nunca instancia classes da extensão no processo principal e que a compatibilidade só acontece após a decisão explícita. Mesmo depois desses testes, não se promete risco zero contra falhas do próprio Android ou do sistema operacional.

## Referências oficiais consultadas

- [Serviço Android e isolatedProcess](https://developer.android.com/guide/topics/manifest/service-element)
- [Práticas de segurança e sandbox do Android](https://developer.android.com/guide/practices/security)
- [ABIs e seleção automática na instalação](https://developer.android.com/ndk/guides/abis)
