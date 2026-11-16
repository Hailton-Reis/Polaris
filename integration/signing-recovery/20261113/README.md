# Recuperação da assinatura original — 13/11/2026

O usuário localizou no ambiente anterior o keystore que assinou a beta.10 e forneceu uma cópia criptografada em CMS/DER, RSA4096/AES256-CBC, destinada ao certificado público deste ambiente. O SHA-256 do transporte confere com o valor informado. A cópia foi decifrada em pasta privada com permissões 700/600, fora dos repositórios.

O certificado foi exportado diretamente do keystore recuperado. Seu SHA-256 corresponde a `signer_sha256` do manifesto público beta.10: `3ae747069cc9015ca1777f94fd56b030501f45d6af380426a572ad60e94d8227`. Essa verificação substitui o bloqueio de chave não localizada registrado historicamente em integration/build-validation/20261113/signing-check.json. A chave debug gerada anteriormente continua diferente; ela não é usada como substituta.

O build local foi configurado pelo mecanismo existente de keystore.properties, ignorado pelo Git e com permissão 600. Não foi criada outra chave de assinatura. Nenhum keystore, chave privada de transporte, senha ou arquivo criptografado integra esta evidência ou o repositório. recovery.json registra somente identificadores públicos e resultados.

O empacotamento universal ARM também exclui explicitamente bibliotecas x86/x86_64 antes do processamento nativo. A seleção anterior de ABIs por si só ainda deixava esses intermediários de emulador no merge/strip; o build anterior esgotou disco nessa fase. A alteração não afeta as variantes de emulador sem polaris.universalArm=true.

A compilação e 906 testes JVM da revisão P20261113.3 permanecem documentados em integration/build-validation/20261113. A configuração de assinatura e a exclusão de arquivos de emulador não alteram esse código de aplicação. O resultado desta nova tentativa de APK é registrado separadamente, sem converter identidade de assinatura em aceite de atualização real no aparelho.

Para caber no disco deste executor, três APIs opcionais do host NDK (LLDB/libclang), não vinculadas pelos executáveis clang/strip/linker usados no build, foram temporariamente comprimidas sem perdas e verificadas por hash. Os três arquivos originais foram restaurados e seus hashes conferidos antes de concluir a rodada; isso não altera bibliotecas nativas do APK.


## Resultado final

**APK interno beta.11/P20261113.3 gerado e verificado.** :app:assembleDebug terminou BUILD SUCCESSFUL em 9min, 325 tarefas (15 executadas/310 atualizadas). O guard de disco não precisou interromper a execução: mínimo 343.154.688 bytes livres. O cache de transforms regenerável foi removido após o build para exportar o pacote e restaurar integralmente as três bibliotecas opcionais do host NDK.

O APK universal tem 272.970.356 bytes (260.3MiB), versionCode 112, application_id `app.mihon.tachiyomiat.dev` e o certificado original da beta.10. SHA-256: `ada69c1e08a679489575a0622e43a8825de5e443083d978281c1d2a688631c98`. O exportador verificou a revisão nos DEX, marca Polaris compilada, as duas arquiteturas ARM com dependências obrigatórias e ausência de x86. O manifesto registra SAME_ID_AND_SIGNER contra a beta.10. apk-verification.log é a verificação real de assinatura; native-inventory.json relaciona as bibliotecas de cada ABI.

A primeira exportação encontrou um defeito antigo no validador de marca: contava também os ícones dos aliases de conquistas e exigia dois ícones no manifesto inteiro. Agora verifica os atributos diretos da application, mantendo icon/roundIcon Polaris e permitindo os aliases já implementados. Três testes reproduziram a falha antes da correção (13 passaram, dois falharam e um erro); depois 16/16 passaram. Os testes também impedem que um alias correto esconda roundIcon ausente na application ou substitua uma application inexistente. Não houve alteração nas artes ou no APK para contornar a conferência.

Quatro testes completos de aplicação/idempotência/CRLF/drift do overlay passaram nesta continuação. Os 906 testes JVM foram executados na etapa anterior, sem falhas/skips; não foram reexecutados aqui. O código de aplicação está preservado: alterações desta continuação são configuração privada de assinatura, filtro de bibliotecas de emulador no build e correção Python do verificador de marca.

**Ainda não é lançamento público nem aceite de aparelho.** Login real, sandbox dinâmico/novels, biblioteca/backups, armazenamento/OCR/tradução, atualização beta.10→beta.11 e distribuição não depurável continuam no checklist. A identidade da assinatura permite a instalação sobre a beta.10, mas não comprova o comportamento nem preservação de dados em um aparelho real. Nenhuma Release foi criada ou atualizada; o atualizador continua sem uma nova versão pública.
