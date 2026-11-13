# Beta.11 — checklist de consolidação

Base pública: beta.10/código111. Base de engenharia: P20261112.1, commit 6952e5e.
Este checklist acompanha o trabalho autorizado em 13/11. Não é uma declaração de lançamento.

| Frente | Estado |
| --- | --- |
| Jornada, XP, conquistas e grimórios | Implementados no checkpoint anterior |
| Login de fontes isoladas | Integração compilada; cookies por caminho/host e snapshots corrigidos P20261113.6. Login real pendente |
| Sandbox: controles dinâmicos, provedores externos/OAuth e novels | Controle numérico e listas dinâmicas síncronas implementados P20261113.4/.5; ações personalizadas/assíncronas, OAuth e novels pendentes |
| Biblioteca, fontes reais e backups entre leitores | Limpeza e gravação de backups verificadas em JVM; ida/volta e aceite completo pendentes |
| Leitura, OCR e tradução nos aparelhos | Pendente, incluindo diagnóstico do A12 |
| Armazenamento | Proteção de espaço na importação implementada nesta candidata; deduplicação/recuperação e medição física pendentes |
| Atualização beta.10 → beta.11 e distribuição não depurável | APK interno gerado com assinatura original; atualização no aparelho e variante não depurável pendentes |

Ordem: autenticação/sandbox → biblioteca/backups → armazenamento/leitura → teste ARM → pacote.
Não repetir funcionalidades já entregues com base nos documentos históricos. Não transformar
resultado de teste de componentes em aprovação da próxima beta inteira.

A [primeira revisão](LOGIN_E_ARMAZENAMENTO_P20261113_1.md) e a [proteção de backups P20261113.2](../integration/backup-safety/20261113/README.md) registram código, testes e limites.
A publicação não foi iniciada; a beta.10 continua sendo a versão pública.

O APK interno P20261113.3 foi gerado com a assinatura original recuperada e verificado como ARM32/ARM64; não é uma Release pública. A atualização em aparelho continua pendente. [Evidência do pacote](../integration/signing-recovery/20261113/README.md).

A continuação P20261113.4 acrescenta [controles numéricos isolados](SANDBOX_CONTROLES_P20261113_4.md), sem gerar outro APK nesta etapa. Validação da candidata não encerra os aceites reais listados acima.

P20261113.4: app e instrumentação compilados; 833 testes do app aprovados (12 novos), mais 85 de domain já aprovados e UP-TO-DATE. Nenhum caso anterior ausente. Três cenários Android aguardam execução em dispositivo. [Evidência](../integration/sandbox-numeric/20261113/README.md).

P20261113.5: [listas dinâmicas síncronas](SANDBOX_DINAMICO_P20261113_5.md), GET/HEAD na preparação e opções reconferidas ao salvar. App/instrumentação compilados, 845 testes do app aprovados (12 novos); seis cenários Android aguardam dispositivo. Sem outro APK nesta etapa.

P20261113.6: [cookies por caminho no login](LOGIN_COOKIES_P20261113_6.md), com cópia restrita ao host e snapshots consistentes. App/instrumentação compilados; 861 testes do app (16 novos) e 63 focados aprovados. Três cenários Android aguardam execução em aparelho/WebView.
