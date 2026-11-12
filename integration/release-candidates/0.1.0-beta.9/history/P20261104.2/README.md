# Polaris beta.9 — rascunho conferido

**0.1.0-beta.9 / P20261104.2 / código 110**, compilada a partir dos arquivos verificados do commit `e6bab4bc4fade68e3aa74e2677500ea762d34d29`.

O [rascunho de Release](https://github.com/Hailton-Reis/Polaris/releases/tag/untagged-e498da151b0296209fe2) contém sete anexos: APKs ARM64 e ARM32, manifesto do atualizador, hashes, roteiro, notas e relatório de validação. Todos os tamanhos e SHA-256 remotos correspondem ao plano revisado. Os dois APKs conservam a assinatura distribuída. A beta.8 pública e seus anexos foram preservados.

**Continua em rascunho:** não está disponível para download anônimo e não aparece no atualizador do aplicativo. O rascunho pode ser revisado pela conta mantenedora no GitHub. Esta preparação não publica uma nova versão nem confirma a instalação no celular.

- [Notas destinadas ao público](RELEASE_NOTES.md)
- [Roteiro de teste](PRIMEIRO_TESTE.md)
- [Identidade e arquivos do atualizador](manifest.json)
- [Plano com hashes de arquivos e partes de transporte](release-plan.json)
- [Conferência remota dos sete anexos](DRAFT_STATUS.json)
- [Pendências dos checks GitHub](CI_DIAGNOSTICO.md)

## Conferência de distribuição

Os oito testes do fluxo de upload passaram, e a recomposição local conferiu todos os bytes. O [job de upload](https://github.com/Hailton-Reis/Polaris/actions/runs/41878102194/job/126743075786) registra a conclusão do envio e a verificação dos sete anexos. A consulta do status do job permaneceu mostrando fila após a conclusão; a evidência usa o log e os hashes remotos, sem depender desse estado desatualizado. O ref temporário dos binários foi removido depois da conferência.

Também foram feitos quatro pedidos HTTP sem Authorization enviado pelo cliente aos APKs públicos da beta.8: bytes 0–1023 e 1048576–1049599 para cada arquitetura. Todos receberam **206**, faixa e tamanho corretos, com suporte `Accept-Ranges: bytes`. Veja [respostas medidas](public-range-check.json). Isso verifica o servidor; não substitui o teste Android de queda de conexão, WorkManager, notificações e instalação.

A biblioteca Android não foi alterada nesta preparação: permanecem os 635 testes JVM com 618 aprovações e as mesmas 17 falhas, os 16 controles Android aprovados e os limites descritos na [validação do código](../../document-reader/TEST_RESULTS.json). Os dois checks antigos de CI ainda têm as pendências registradas, e a aceitação física permanece pendente.
