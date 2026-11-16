# Distribuição beta — P20261116.1

A candidata beta.11 precisa atualizar a beta.10 instalada. Seu identificador é `app.mihon.tachiyomiat.dev`; a configuração `release` genérica usa outro identificador. A variante dedicada `beta` conserva `.dev`, usa a assinatura original e aumenta o código de 111 para 112, com depuração, `testOnly` e profiling por shell desativados. Sobre identifica o canal como Beta.

A variante mantém otimização R8 e remoção de recursos desativadas para preservar o carregamento dinâmico de extensões já exercitado. Não inclui os fontes/componentes exclusivos de `src/debug`. O worker de OCR Dbnet permanece independente da sandbox arquivada; seu backend opcional continua ARM64.

## Verificação e reprodução

Com o SDK e a assinatura configurados privadamente:

```sh
./gradlew :app:testBetaUnitTest :domain:testReleaseUnitTest \
  :data:testDebugUnitTest :source-api:testDebugUnitTest \
  :app:assembleBeta -Ppolaris.universalArm=true
```

Os testes locais de app beta e domain release são explicitamente habilitados pela API `hostTests` do AGP. Data/source-api não possuem casos JVM nesta consolidação. Os relatórios de app/domain são comparados aos 986 casos anteriores usando `--patched-task app=testBetaUnitTest --patched-task domain=testReleaseUnitTest`; a ausência de qualquer conjunto selecionado torna a comparação inconclusiva, mesmo que existam relatórios debug antigos.

O exportador recebe a pasta `app/build/outputs/apk/beta`, um diretório novo de saída, a comparação concluída e obrigatoriamente `--previous-manifest integration/release-candidates/0.1.0-beta.10/manifest.json`. Ele verifica assinatura, ID, código crescente, versão, Android mínimo, revisão e marca Polaris, além das bibliotecas ARM32/ARM64.

O manifesto compilado precisa estar sem depuração, `testOnly`, profiling por shell, instrumentação e componentes de teste/sandbox. O inventário lê definições de classes de todos os DEX, inclusive multidex com números de dois dígitos; recusa classes da sandbox experimental, harnesses e bibliotecas JDBC/JUnit de testes. Strings legadas de preferências não são tratadas como classes executáveis.

A verificação não escreve a chave, senhas ou dados pessoais na saída. Nunca substitui um pacote anterior. Os dois descritores ARM no manifesto apontam para um único APK.

[Resultados e limites do pacote interno](../integration/distribution/20261116/README.md).

## Candidato verificado

Compilação final aprovada em 3min42s: 901 testes do app beta executados/aprovados e 85 de domain release já aprovados, UP-TO-DATE na retomada. Total 986 sem falhas/skips ou casos anteriores ausentes. A primeira montagem parou por limite de disco após os testes; a montagem foi retomada com os mesmos fontes. 4 testes de overlay, 27 de empacotamento e 21 do comparador aprovados.

APK universal: **259,481,310 bytes**, SHA-256 `27feeaadc4aec9f54c9a6b57760421dee601e9f3bfe7efef9866fd3ae7fa40e3`. Certificado original da beta.10; oito DEX/68.658 classes, sem executor sandbox, harnesses ou bibliotecas JVM de teste. Manifesto e identidade compilados conferidos. Guias distribuídos descrevem a beta.11 e o aviso de extensões atual, sem copiar as instruções históricas da beta.10.

## Aceite final

Mesmos ID/certificado e código crescente permitem a atualização, mas não comprovam a instalação preservando dados no aparelho. Continuam pendentes atualização beta.10→beta.11, armazenamento/SAF, SQLite/preferências/interface de backups e troca pela UI de leitores externos, leitura/tradução/inferência real, qualidade e pico de memória no A12/ARM.

O candidato permanece interno até a consolidação final. Conta Google/nuvem e sandbox de extensões continuam adiadas; a beta.10 permanece a versão pública enquanto não houver nova Release liberada.
