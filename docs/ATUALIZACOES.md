# Atualizações do Polaris

## Escolha do canal

Em **Configurações → Atualizações do aplicativo**:

- **Buscar atualizações automaticamente** começa ativado. Ao abrir o app, ele consulta as Releases do Polaris, com no máximo uma tentativa automática por dia por canal. Não há consulta periódica com o app fechado.
- **Receber atualizações experimentais** começa **desativado**, inclusive quando o aplicativo instalado é um beta. Ative para incluir betas e outras prévias publicadas.
- **Verificar atualizações** consulta imediatamente, mesmo com a busca automática desligada, respeitando a escolha do canal experimental. Também fica em **Sobre**.

A consulta apenas avisa. O usuário escolhe baixar e confirma a instalação pelo Android. Desativar experimentais não desinstala nem rebaixa a versão atual. Uma versão estável posterior pode substituir um beta quando sua versão e seu código de compilação forem maiores.

Rascunhos são ignorados. No canal padrão, tanto a marcação `prerelease` do GitHub quanto um sufixo de prévia na versão impedem que o pacote seja oferecido. O canal experimental também encontra versões estáveis.

## Acesso ao GitHub

O endereço consultado é `Hailton-Reis/Polaris`, sem token de acesso embutido no aplicativo. O repositório e a [Release beta.9](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.9) agora são **públicos**. Ela contém dois APKs completos, manifesto, hashes, roteiro e relatório de validação. O download pelo navegador do celular não exige uma conta do GitHub.

O aplicativo está configurado para consultar esse repositório. As versões beta dependem da opção **Receber atualizações experimentais**, desativada por padrão. Acesso público não equivale a validação de atualização no aparelho: consulta, download e instalação com a assinatura original ainda precisam desse teste. Uma instalação anterior pode encontrar a beta.9 ao ativar o canal experimental; instalar a própria beta.9 não cria uma versão posterior para o atualizador oferecer.

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
2. Gerar os APKs ARM e o `manifest.json` pelo exportador atualizado, usando a assinatura original.
3. Conferir que versão, código, identificador, Android mínimo, nomes, tamanhos e hashes correspondem aos arquivos finais.
4. Anexar **`manifest.json` e os APKs** à mesma Release, com tag `v<version>`. As notas devem explicar mudanças, limitações e validação.
5. Para um beta, marcar a Release como **pré-lançamento**; mantê-la em rascunho enquanto não estiver liberada. Um rascunho não vira atualização disponível no aplicativo.
6. Somente depois de haver acesso público e uma Release liberada, conferir consulta, escolha de canal, download e atualização no celular, preservando biblioteca e vocabulário.

O primeiro beta foi publicado em 01/11/2026 e depois aberto ao público pelo mantenedor; os seis anexos tiveram nomes, tamanhos e hashes SHA-256 conferidos. O aceite de instalação e atualização nos aparelhos continua pendente.

## Espaço utilizado

Consultar não baixa o APK. Ao aceitar, o download é gerenciado fora da tela e pode repetir falhas transitórias, retomar bytes parciais quando o servidor permite e oferecer novamente a instalação pela tela ou notificação. O arquivo é verificado por SHA-256 antes do instalador Android.

A atualização usa o APK inteiro, sem patches entre versões. A retomada reaproveita bytes do mesmo arquivo, não transforma um APK antigo no novo. O download e o espaço temporário do instalador somam-se à instalação existente. A beta.8 pode precisar de atualização manual inicial para receber esse downloader.

## Estado de validação

A beta.9 / P20261104.4 tem APKs ARM32 e ARM64 conferidos por tamanho, SHA-256 e assinatura. A comparação final executou 707 testes JVM: 690 aprovações e as mesmas 17 falhas preexistentes, sem novas regressões. Os testes de versão, canal, seleção, metadados e integridade continuam incluídos. Os checks antigos do PR ainda têm pendências registradas no protótipo de backup e no preparo do SDK.

Os APKs mantêm a identidade e a assinatura da beta.8 distribuída. Compilação, hashes e testes JVM não validam uma atualização real: retomada entre redes, instalação e preservação dos dados ainda exigem aceite nos aparelhos.

[Notas e evidência da beta.9](versoes/0.1.0-beta.9.md).
