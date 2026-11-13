# Beta.11 — checklist de consolidação

Base pública: beta.10/código111. Base de engenharia: P20261112.1, commit 6952e5e.
Este checklist acompanha o trabalho autorizado em 13/11. Não é uma declaração de lançamento.

| Frente | Estado |
| --- | --- |
| Jornada, XP, conquistas e grimórios | Implementados no checkpoint anterior |
| Login de fontes isoladas | Integração compilada P20261113.3 e concorrência testada em JVM; login real pendente |
| Sandbox: controles dinâmicos, provedores externos/OAuth e novels | Pendente |
| Biblioteca, fontes reais e backups entre leitores | Limpeza e gravação de backups verificadas em JVM; ida/volta e aceite completo pendentes |
| Leitura, OCR e tradução nos aparelhos | Pendente, incluindo diagnóstico do A12 |
| Armazenamento | Proteção de espaço na importação implementada nesta candidata; deduplicação/recuperação e medição física pendentes |
| Atualização beta.10 → beta.11 e distribuição não depurável | APK interno gerado com assinatura original; atualização no aparelho e variante não depurável pendentes |

Ordem: autenticação/sandbox → biblioteca/backups → armazenamento/leitura → teste ARM → pacote.
Não repetir funcionalidades já entregues com base nos documentos históricos. Não transformar
resultado de teste de componentes em aprovação da próxima beta inteira.

A [primeira revisão](LOGIN_E_ARMAZENAMENTO_P20261113_1.md) e a [proteção de backups P20261113.2](../integration/backup-safety/20261113/README.md) registram código, testes e limites.
A publicação não foi iniciada; a beta.10 continua sendo a versão pública.

A [validação P20261113.3](../integration/build-validation/20261113/README.md) compila a integração Android e executa906 testes JVM sem falhas/skips. Não há APK final, teste de login real ou aceite ARM. O bloqueio anterior de dependências foi resolvido nesta revisão.

A [recuperação da assinatura original](../integration/signing-recovery/20261113/README.md) foi concluída após o registro anterior: o keystore recuperado corresponde ao certificado público da beta.10 e foi configurado somente no ambiente privado. A atualização real no aparelho continua pendente.

A mesma continuação gerou e verificou o APK universal beta.11/P20261113.3 (272.970.356 bytes, ARM32/ARM64, código 112). O exportador confirmou SAME_ID_AND_SIGNER contra a beta.10 e 16 testes de empacotamento passaram após correção do verificador de aliases. Ainda é candidata interna; não houve Release pública nem aceite de atualização no aparelho.
