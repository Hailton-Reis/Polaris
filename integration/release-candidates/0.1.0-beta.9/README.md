# Polaris beta.9 — publicação conferida

**0.1.0-beta.9 / P20261104.4 / código 110**, publicada como [pré-lançamento público](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.9) em **05/11/2026, 03:34:10 UTC**. O mantenedor autorizou a publicação com as pendências de aceite registradas. Não é um lançamento estável.

O código compilado é o commit `efc2543487f02ff15c3bc51f3ef0a25723809527`, apontado pela tag. Os sete anexos são os APKs completos ARM32/ARM64, manifesto, SHA-256, roteiro, notas e validação. A revisão .2 do rascunho foi substituída antes da publicação; seu registro histórico está em `history/P20261104.2`. A beta.8 e seus anexos foram preservados.

## Distribuição verificada

Os oito testes do publicador passaram. A recomposição local e a do GitHub Actions conferiram os sete arquivos; todos os tamanhos/digests remotos correspondem ao plano. Os APKs preservam o identificador e a assinatura da beta.8. O [job](https://github.com/Hailton-Reis/Polaris/actions/runs/41962326095/job/127031338793) concluiu com sucesso; o ref temporário de transporte foi removido após a conferência.

Os **sete arquivos foram baixados integralmente por HTTP sem Authorization enviado pelo cliente**, com SHA-256 e tamanho conferidos. Quatro pedidos de intervalo aos APKs retornaram 206 e bytes iguais aos originais. A listagem pública, a tag e o manifesto de atualização foram conferidos. No app, é necessário ativar **Receber atualizações experimentais**. Isso não substitui atualização/instalação no Android.

- [Notas públicas](RELEASE_NOTES.md) e [primeiro teste](PRIMEIRO_TESTE.md)
- [Manifesto](manifest.json), [hashes](SHA256SUMS.txt) e [plano de arquivos](release-plan.json)
- [Registro da publicação](PUBLICATION.json) e [verificação pública](public-verification.json)
- [Validação anexada](VALIDACAO.json), [assistente](../../source-preparation/20261104/README.md) e [backups](../../backup-interop/20261104/README.md)
- [Pendências antigas de CI](CI_DIAGNOSTICO.md)

## Aceite ainda pendente

A comparação final teve **707 testes JVM: 690 aprovações e as mesmas 17 falhas preexistentes**, sem regressões novas. Dezesseis controles Android de tipografia e quatro de segurança passaram em componentes isolados. A abertura completa, assistente com fontes reais, celulares ARM/Android14+, notificações, retomada entre redes e atualização preservando dados continuam pendentes.

O formato de backup não mudou; seis testes de codec e dois leitores independentes aprovaram campos comuns de exemplos sintéticos. Restauração/mescla real e ida/volta pela interface do Mihon/Tachiyomi ainda exigem aceite; `nextUpdate` não é preservado, APKs de extensões privadas não integram o backup e não há garantia universal para todos os forks. Guarde o backup original antes de migrar.
