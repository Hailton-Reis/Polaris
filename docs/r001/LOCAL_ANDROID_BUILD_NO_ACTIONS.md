# Polaris R001 — Android build sem GitHub Actions

**2026-10-20.** A conta do proprietário está sem cota do GitHub Actions. Isso bloqueia jobs hospedados; **não indica uma falha no código Android**. Este procedimento executa localmente o gate já existente da issue #2, sem criar um workflow e sem pagar por minutos de Actions.

## O que instalar no Windows

1. [Git for Windows](https://git-scm.com/downloads/win) (inclui **Git Bash**).
2. [Python 3](https://www.python.org/downloads/windows/) (marque a opção para adicioná-lo ao PATH, se apresentada).
3. [Temurin JDK 21](https://adoptium.net/temurin/releases/?version=21); deixe `JAVA_HOME` apontar para este JDK.
4. [Android Studio](https://developer.android.com/studio). Em **SDK Manager → Show Package Details**, instale **Android SDK Platform 37**, **Build Tools 36.0.0 e 37.0.0**, **NDK 29.0.14206865 e 28.2.13676358**, **CMake 3.22.1**, **Platform Tools** e **SDK Command-line Tools**. Aceite as licenças do SDK no Android Studio.

Reserve pelo menos **25 GB livres** para fontes, SDK, dependências e APKs. Precisa de rede para os primeiros downloads do Git, Gradle e bibliotecas. Não coloque credenciais, tokens, cookies ou dados de navegação nos logs que compartilhar.

## Comandos — PowerShell

Abra o **PowerShell** em uma pasta para o projeto:

```powershell
git clone --branch r001/multisource-foundation https://github.com/Hailton-Reis/Polaris.git
cd Polaris
py -3 tools\local-android\polaris_local.py check
```

O modo `check` não clona nada, não inicia compilação, não altera repositório ou celular. Corrija apenas as linhas `[FALTA]`. Se `py` não estiver disponível, use `python`.

Com o ambiente pronto:

```powershell
py -3 tools\local-android\polaris_local.py prepare
py -3 tools\local-android\polaris_local.py build
```

O comando `prepare` clona o Yomotsu **exatamente** no commit fixado `0fb80c439ef816eeb50674f1b90af39918b176d8`. O comando `build` executa o script de validação já versionado `scripts/r001/build_issue002.sh` no **Git Bash**, comparando **baseline sem patch** e **Spike-001 com migração14**. Ele não instala APK, não envia arquivos nem desbloqueia backup v2. Se a compilação falhar, os logs ficam em `~/PolarisLocal/evidence/issue002-...` (e nunca são sobrescritos).

O resultado esperado, **se** a compilação terminar com sucesso, é:

- `evidence/.../apks/baseline/*.apk`
- `evidence/.../apks/spike001/*.apk`
- `evidence/.../build-status.txt`
- `evidence/.../unit-test-comparison.json`
- logs `baseline-build.log`, `patched-build.log` e `*.log`.

Não marque A01/B01–B05 como aprovados apenas porque um APK foi gerado.

## Provar a leitura multisource em Android

Use **um telefone de testes** ou emulador (não sua instalação diária: o pacote de debug pode alterar o banco do app). Para testar em aparelho físico, ative Opções do desenvolvedor → Depuração USB; conecte e autorize o computador. Confirme no PowerShell:

```powershell
adb devices
```

Siga exatamente o arquivo [ISSUE002_DEVICE_RUNBOOK.md](ISSUE002_DEVICE_RUNBOOK.md). Instale os dois APKs **em sequência de teste** (baseline e então Spike-001) e adicione a mesma obra em **duas extensões/fontes compatíveis**, com capítulos carregados. O hook de debug pode identificar os IDs reais, criar o mangá virtual e remover uma referência. Os testes obrigatórios são: B01 (lista agregada), B02A/B02B (capítulo de cada fonte), B03 (preservação após remoção), B04 (atualização), B05 (regressões/DB). Faça capturas e logs usando `scripts/r001/capture_issue002_device_evidence.py`, revendo quaisquer nomes, URLs ou screenshots antes de compartilhar.

Se tiver de escolher **uma ação agora**, instale Android Studio e execute o comando `check`. A saída `[FALTA]` nos dirá com precisão o que ainda falta configurar. Não é necessário aumentar o plano do GitHub.

## Segurança e limite da prova

- Este script verifica **Spike-001 e o build da base Yomotsu**, não compila automaticamente as mais recentes implementações staging do restaurador v2, que ainda exigem integração real do SQLDelight e ProtoBuf.
- A migração 15 não é aplicada. O restaurador v2 continua propositalmente fail-closed. O PR #1 segue Draft, issue #2 e #11 abertas.
- Os testes SQLite/Kotlin do repositório continuam disponíveis para desenvolvimento sem Actions; uma compilação local é evidência mais útil agora do que disparar workflows sem cota.
- O script se recusa a alterar checkout Yomotsu já existente se estiver sujo ou em commit divergente. Evidências são sempre criadas em pasta nova.
- A fonte de verdade é o GitHub branch `r001/multisource-foundation`. Nenhum commit na branch principal é necessário.
