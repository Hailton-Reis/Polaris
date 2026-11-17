# Atualizações do Polaris

A [beta.11 está publicada](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.11), P20261116.1/código 112. O atualizador exige o canal experimental ativado. A [auditoria P20261116.2](AUDITORIA_POS_BETA11_P20261116_2.md) corrige limites e retomada do download para a próxima versão, ainda sem APK. Uma publicação posterior deve comparar a identidade com o manifesto da beta.11 e aumentar versão/código; não substituir os anexos da beta.11 por esse código de desenvolvimento.

A [continuação P20261117.1](OPENCV_P20261117_1.md) integra/compila o OpenCV oficial e confere a saída nativa, junto às [proteções de backups](LEITURA_BACKUPS_P20261116_3.md). Também permanece sem novo APK/Release; o pacote instalado não inclui essas revisões posteriores.

A [P20261117.2](LIMPEZA_RECORTE_OCR_P20261117_2.md) acrescenta a limpeza de recortes Paddle em falhas de preparação. Continua no código de desenvolvimento, sem novo APK; a beta.11 instalada permanece no checkpoint público original.

A [P20261117.3](BUSCA_FONTES_P20261117_3.md) melhora a busca entre fontes e o tratamento de tentativas incompletas. Também permanece no desenvolvimento, sem substituir a beta.11 pública ou gerar uma atualização disponível no app.

A [P20261117.4](FILTRO_ADULTO_P20261117_4.md) acrescenta o filtro +18 de buscas, ligado por padrão e reversível. Conteúdo sem marcação pode aparecer. Também está somente no desenvolvimento; a biblioteca é preservada.

A [P20261117.5](FONTES_MISTAS_P20261117_5.md) mantém fontes mistas disponíveis, aplica o filtro +18 por obra e pede confirmação ao desligá-lo. Continua sem novo APK/Release.

## Escolha do canal

Em **Configurações → Atualizações do aplicativo**:

- **Buscar atualizações automaticamente** começa ativado. Ao abrir o app, ele consulta as Releases do Polaris, com no máximo uma tentativa automática por dia por canal. Não há consulta periódica com o app fechado.
- **Receber atualizações experimentais** começa **desativado**, inclusive quando o aplicativo instalado é um beta. Ative para incluir betas e outras prévias publicadas.
- **Verificar atualizações** consulta imediatamente, mesmo com a busca automática desligada, respeitando a escolha do canal experimental. Também fica em **Sobre**.

A consulta apenas avisa. O usuário escolhe baixar e confirma a instalação pelo Android. Desativar experimentais não desinstala nem rebaixa a versão atual. Uma versão estável posterior pode substituir um beta quando sua versão e seu código de compilação forem maiores.

Rascunhos são ignorados. No canal padrão, tanto a marcação `prerelease` do GitHub quanto um sufixo de prévia na versão impedem que o pacote seja oferecido. O canal experimental também encontra versões estáveis.

## Acesso ao GitHub

O endereço consultado é `Hailton-Reis/Polaris`, sem token de acesso embutido no aplicativo. O repositório e a [Release beta.10](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.10) agora são **públicos**. Ela contém um APK universal ARM32/ARM64, manifesto, hashes, roteiro e relatório de validação. Os dois descritores de arquitetura no manifesto apontam para o mesmo arquivo; apenas um download é necessário. O download pelo navegador do celular não exige uma conta do GitHub.

O aplicativo está configurado para consultar esse repositório. As versões beta dependem da opção **Receber atualizações experimentais**, desativada por padrão. Acesso público não equivale a validação de atualização no aparelho: consulta, download e instalação com a assinatura original ainda precisam desse teste. Uma instalação anterior pode encontrar a beta.10 ao ativar o canal experimental; instalar a própria beta.10 não cria uma versão posterior para o atualizador oferecer.

Falhas de rede e limites do GitHub são diferenciados de uma consulta concluída. Uma eventual indisponibilidade ou restrição futura do repositório também deve ser informada, em vez de ser apresentada como ausência de atualização.

## Critérios para oferecer um APK

O aplicativo consulta a lista paginada de Releases e compara versões SemVer, incluindo contadores numéricos como `beta.2` e `beta.10`. Não confia apenas na ordem exibida pelo GitHub.

Cada Release precisa ter um **`manifest.json`** junto dos APKs. O exportador do beta gera esse arquivo. O atualizador exige:

- Versão da Release igual à versão do manifesto e posterior à instalada.
- `version_code` maior que o instalado e `application_id` igual ao aplicativo instalado.
- Android mínimo compatível e APK para uma das arquiteturas suportadas pelo aparelho, respeitando a ordem de preferência do sistema.
- Arquivo publicado com nome e tamanho iguais aos metadados, com URL de download pertencente ao repositório do Polaris.
- Hash SHA-256 válido no manifesto e correspondente ao APK recebido antes de oferecê-lo para instalação.

O manifesto de atualização tem limite de 64 KiB. Releases sem os metadados ou sem APK compatível não são oferecidas. Se apenas houver atualização que exige Android mais novo, a consulta informa a incompatibilidade do sistema.

O `application_id` e a chave de assinatura precisam permanecer os mesmos entre beta e estável para atualizar a mesma instalação. Eles não devem ser trocados ao mudar de canal. O Android continua verificando a assinatura durante a instalação. Os APKs desta distribuição foram conferidos com a mesma assinatura da beta.8; uma compilação própria pode ter outra chave.

## Publicação pelo mantenedor

1. Concluir os testes pendentes, incluindo armazenamento e instalação, antes de distribuir o candidato.
2. Gerar o APK ARM da variante `beta` (`:app:assembleBeta -Ppolaris.universalArm=true`) e o `manifest.json` pelo exportador atualizado, usando a assinatura original. Na beta.11, `--previous-manifest integration/release-candidates/0.1.0-beta.10/manifest.json` é obrigatório. O exportador recusa identidade/assinatura divergentes, código não crescente, depuração ativa, componentes de teste/sandbox e classes JVM de teste no APK. A variante mantém o sufixo `.dev` da beta.10 instalada.
3. Conferir que versão, código, identificador, Android mínimo, nomes, tamanhos e hashes correspondem aos arquivos finais.
4. Anexar **`manifest.json` e os APKs** à mesma Release, com tag `v<version>`. As notas devem explicar mudanças, limitações e validação.
5. Para um beta, marcar a Release como **pré-lançamento**; mantê-la em rascunho enquanto não estiver liberada. Um rascunho não vira atualização disponível no aplicativo.
6. Somente depois de haver acesso público e uma Release liberada, conferir consulta, escolha de canal, download e atualização no celular, preservando biblioteca e vocabulário.

O primeiro beta foi publicado em 01/11/2026 e depois aberto ao público pelo mantenedor; os seis anexos tiveram nomes, tamanhos e hashes SHA-256 conferidos. O aceite de instalação e atualização nos aparelhos continua pendente.

## Espaço utilizado

Consultar não baixa o APK. Ao aceitar, o download é gerenciado fora da tela e pode repetir falhas transitórias, retomar bytes parciais quando o servidor permite e oferecer novamente a instalação pela tela ou notificação. O arquivo é verificado por SHA-256 antes do instalador Android.

A atualização usa o APK inteiro, sem patches entre versões. A retomada reaproveita bytes do mesmo arquivo, não transforma um APK antigo no novo. O download e o espaço temporário do instalador somam-se à instalação existente. A beta.8 pode precisar de atualização manual inicial para receber esse downloader.

## Estado de validação

A beta.10 / P20261106.1 tem um APK universal ARM32/ARM64 conferido por tamanho, SHA-256 e assinatura. A comparação final executou 738 testes JVM: 721 aprovações e as mesmas 17 falhas preexistentes, sem novas regressões. Os testes de versão, canal, seleção, metadados e integridade continuam incluídos. Os checks antigos do PR ainda têm pendências registradas no protótipo de backup e no preparo do SDK.

O APK universal mantém a identidade e a assinatura da beta.9 distribuída. Compilação, hashes e testes JVM não validam uma atualização real: retomada entre redes, instalação e preservação dos dados ainda exigem aceite nos aparelhos.

[Notas e evidência da beta.10](versoes/0.1.0-beta.10.md).

Na candidata P20261113.3, o guard confirmou que o certificado debug deste ambiente diverge da beta.10. O arquivo da chave original não foi encontrado nas fontes acessíveis; o certificado público não o substitui. Não publicar essa compilação como atualização nem desinstalar para contornar o conflito. [Registro atual](../integration/build-validation/20261113/README.md).

A [recuperação da assinatura original](../integration/signing-recovery/20261113/README.md) foi concluída após o registro anterior: o keystore recuperado corresponde ao certificado público da beta.10 e foi configurado somente no ambiente privado. A atualização real no aparelho continua pendente.

A mesma continuação gerou e verificou o APK universal beta.11/P20261113.3 (272.970.356 bytes, ARM32/ARM64, código 112). O exportador confirmou SAME_ID_AND_SIGNER contra a beta.10 e 16 testes de empacotamento passaram após correção do verificador de aliases. Ainda é candidata interna; não houve Release pública nem aceite de atualização no aparelho.

P20261115.2 remove a sandbox experimental dos fontes compilados e guarda o checkpoint anterior numa branch de arquivo. O aviso único permanece. Classes e manifestos foram inspecionados após compilação; a medida de tamanho fica para o pacote final. O APK interno P20261113.3 continua anterior a essa retirada e às demais revisões posteriores, sem representar a candidata atual. [Escopo atual](ARQUIVAMENTO_SANDBOX_P20261115_2.md).

A candidata P20261116.1 substitui o APK interno antigo como pacote atual de avaliação: beta.11/código 112, universal ARM32/ARM64, 259.481.310 bytes, mesmo ID/certificado da beta.10 e variante `beta` não depurável. Manifesto, oito DEX/68.658 classes, revisão, marca e bibliotecas nativas foram conferidos; sandbox/harnesses/classes JVM de teste ausentes, worker OCR preservado. [Build e verificação](DISTRIBUICAO_BETA_P20261116_1.md). O arquivo anterior foi preservado e é recusado pelos novos guards. Nenhuma Release pública foi criada; atualizar no aparelho e preservar dados continuam pendentes.
