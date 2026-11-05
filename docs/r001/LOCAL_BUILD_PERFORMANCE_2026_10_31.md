# Compilação local com uso de CPU, memória e cache — 31/10/2026

O script anterior impunha um worker, heap Gradle de 3 GiB, ausência de cache, ausência de compilação incremental e um novo processo Gradle por chamada. Eram quatro chamadas: APK e testes da base, depois APK e testes do Polaris. O usuário compila em Ryzen 7 3700X (8 núcleos/16 threads), com 32 GB de RAM e SSD, e pediu melhor aproveitamento do computador.

## Novo padrão automático

A próxima opção 4 do CMD continua buscando a branch de engenharia e passa a usar o perfil `auto`, sem precisar editar o CMD já baixado. Os parâmetros são definidos para o processo de compilação; os arquivos globais de configuração do Gradle do usuário não são editados.

| Recurso | Antes | Perfil previsto para 3700X/32 GB |
|---|---|---|
| Workers Gradle | 1 | Até 8 |
| Heap máximo do Gradle | 3 GiB | 8 GiB |
| Paralelismo entre projetos | Desligado | Ligado |
| Cache de tarefas | Desligado | Ligado |
| Compilação incremental Kotlin | Desligada | Ligada |
| Processo Gradle | Novo em cada chamada | Daemon reutilizado |
| Chamadas Gradle por validação | 4 | 2 |

O compilador Kotlin roda no processo do Gradle para evitar um segundo heap grande e independente. O limite de workers considera tanto CPUs disponíveis quanto memória. Em Windows, a memória física é consultada por `GlobalMemoryStatusEx`; em Linux também são considerados limites de cgroup e afinidade de CPU. Se a memória não puder ser identificada, o perfil usa no máximo dois workers e heap de 3 GiB.

| RAM identificada | Teto de workers, limitado também pelas CPUs | Heap máximo |
|---|---|---|
| Menos de 7 GiB | 1 | 2 GiB |
| 7 a menos de 12 GiB | 2 | 3 GiB |
| 12 a menos de 24 GiB | 4 | 4 GiB |
| 24 a menos de 48 GiB | 8 | 8 GiB |
| A partir de 48 GiB | 12 | 10 GiB |

O número de workers é um teto para tarefas concorrentes. Etapas dependentes, especialmente a compilação de um módulo grande, continuam impondo limites ao paralelismo. Não há medição de ganho no PC Windows do usuário nem promessa de multiplicador de velocidade.

## Menos recompilação entre APK e testes

Cada variante agora monta o APK e executa os testes na mesma execução Gradle com `--continue`. Isso evita uma segunda configuração e uma nova data `BUILD_TIME` entre a montagem e os testes, que podia invalidar a compilação do app. Base e Polaris continuam sendo processados em sequência; o paralelismo ocorre entre tarefas do mesmo Gradle.

As pastas de trabalho/evidência continuam novas e isoladas. O cache local do Gradle pode restaurar tarefas elegíveis entre pastas, enquanto o incremental Kotlin depende de estado compatível disponível. Tarefas afetadas por código, data de compilação ou assinatura podem continuar rodando. O primeiro build ainda pode precisar baixar ferramentas e dependências e popular caches.

## Validação preservada

A geração de APKs não elimina os testes ou a comparação com a base. O novo verificador exige a conclusão de `:app:assembleDebug`, os APKs declarados nos metadados, o APK x86_64 e cobertura mínima de testes por módulo. Ele permite códigos de saída decorrentes de tarefas unitárias identificadas, com falhas correspondentes nos relatórios. Erros de compilação/empacotamento, queda do daemon, relatórios parciais ou APKs ausentes interrompem o processo. A comparação final decide quais falhas já existiam na base e rejeita novos testes falhos, pulados ou ausentes.

Os dois logs antigos de testes continuam disponíveis como cópias dos logs combinados. Evidências novas:

- `build-profile.json`: hardware identificado, limites e argumentos exatos.
- `gradle-options.txt`: argumentos efetivamente usados, um por linha.
- `gradle-phase-times.tsv`: tempo e código de saída das duas chamadas.
- `baseline-completion.json` e `patched-completion.json`: validação de montagem e relatórios completos.

Os checks SQL, a migração 14, a recusa de migration15, a proteção do checkout fixado e o bloqueio de backupv2 permanecem. Esta alteração não modifica o código Android nem muda a identificação **Polaris P20261031.1**.

## Diagnóstico e execução em andamento

Uma compilação já iniciada mantém os parâmetros antigos. Não é preciso interrompê-la ou recompilar o mesmo APK somente para instalar esta melhoria do processo. O perfil novo será aplicado na próxima execução da opção 4.

O perfil alternativo `conservative` mantém um worker, heap de 3 GiB e desativa cache/paralelismo/incremental/daemon. Pode ser escolhido por `--build-profile conservative` no Python ou pela variável de processo `POLARIS_BUILD_PROFILE=conservative` ao chamar o CMD. Os testes e checks finais continuam obrigatórios nos dois perfis.

Resultados e limites da verificação estão em `integration/local-build-performance/TEST_RESULTS.json`. Os testes de hardware simulado não equivalem a execução/benchmark no Windows; a verificação Android usa os recursos limitados do ambiente de engenharia.
