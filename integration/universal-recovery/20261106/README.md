# Universal ARM, fontes e segurança — P20261106.1

**Publicação posterior:** a candidata foi liberada como pré-lançamento público em 06/11/2026. Este diretório conserva o registro de compilação anterior à autorização. Veja [o registro público e os downloads conferidos](../../release-candidates/0.1.0-beta.10/README.md).

**Beta.10 / código 111 / candidata interna sem publicação.** A [beta.9 pública](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.9) permanece inalterada.

O único APK `Polaris-0.1.0-beta.10-universal.apk` tem **261.130.442 bytes** (261.1MB / 249.0MiB), SHA-256 `f1a556d2620a5984c76cebe2dc5a10e461d8d5a2feb6a91018371beaec0a90da` e a assinatura da beta.9. Os dois descritores do manifesto apontam para esse mesmo arquivo. Há uma linha de hash e bibliotecas de leitura/OCR em ambas as arquiteturas. Assets, fontes e bibliotecas nativas conferidos permanecem idênticos aos APKs .4 da beta.9. O tamanho instalado e o desempenho físico não foram aprovados.

O empacotamento Gradle foi refeito sem o estado incremental de APK; os **2192 arquivos lógicos** foram conferidos byte a byte por SHA-256 antes/depois. Isso removeu preenchimento do contêiner sem mudar código, recursos ou chave. Não houve montagem manual ou reassinatura de um ZIP.

## Comportamento e limites

[Guia da candidata](../../../docs/UNIVERSAL_FONTES_SEGURANCA_P20261106_1.md): resposta principal antes da descoberta adicional, recuperação de fonte ausente, prioridade de português entre idiomas habilitados e amostras que abrem, reserva de edições do mesmo capítulo, limites de concorrência e fluxo após restauração. A busca não confirma uma obra apenas pelo título, não testa todas as páginas e não altera fonte fixada pela pessoa.

[Segurança](../../../docs/ISOLAMENTO_DE_EXTENSOES.md): inspeção preventiva/quarentena antes de carregar APKs, exceção vinculada a bytes, importação de estado interno bloqueada e certificados restaurados pendentes de revisão. Plugins de novels têm validação de caminhos/HTTPS própria; não são certificados pelo scanner DEX. O executor de extensões em sandbox ainda não está integrado. O mantenedor escolheu compatibilidade opcional com aviso quando o isolamento não for suportado.

## Evidência executada

- **738 testes JVM: 721 aprovações e as mesmas 17 falhas preexistentes**, sem casos ausentes, novos erros ou testes ignorados. Foram adicionados 31 casos comparados à beta.9 .4. [Comparação](unit-comparison.json), [classes selecionadas](selected-tests.json) e [falhas anteriores](preexisting-failures.json).
- Compilação e testes executados no mesmo grafo Gradle, com conclusão de assembleDebug. O exit 1 é dos testes antigos; o último empacotamento separado terminou com exit 0.
- **240 arquivos** do overlay coincidem com os usados na compilação. [Hashes](compiled-overlay.json), [artefato](artifact-check.json), [manifesto](manifest.json) e [SHA-256](SHA256SUMS.txt).
- Quatro guardas do aplicador de patch e nove do empacotador aprovadas; sintaxe do driver shell aprovada. Fontes atuais mais os scripts permitem reconstrução, mas uma compilação própria pode ter outra assinatura.
- **Seis controles Android de isolamento passaram em API 26 x86_64**, num APK independente de17KB, com UIDs separados. [Resultado e reprodução](../../extension-isolation/20261106/README.md). Não é execução de extensão real nem aceite do leitor.

## Antes de distribuir

A falha do A12 ainda não foi reproduzida no aparelho. A instalação/atualização real, assistente com fontes reais, extensões compartilhadas já instaladas pelo Android, consumo, Android 14+ e recuperação de redes continuam pendentes. O publicador GitHub atual também precisa aceitar o novo formato de um arquivo antes de uma futura publicação.

O formato ProtoBuf e as identidades originais permanecem; seis casos de codec passaram. **Não há aceite da ida/volta real pelo banco e pela interface do Mihon/Tachiyomi**, nem garantia de todos os forks. O exportador atual não normaliza capítulos alternativos com URLs `polaris://` para leitores externos; esse caso precisa de desenho e validação próprios. Guarde o backup original. A limitação de `nextUpdate` também permanece.

[Resultados completos](TEST_RESULTS.json). Esta evidência não autoriza chamar a candidata de versão estável ou migração universalmente compatível.
