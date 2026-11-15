# Sandbox pausada e aviso único — P20261114.4

Decisão do usuário: pausar toda a sandbox e focar armazenamento, backups, leitura e distribuição. Código preservado, política de ativação desligada, seletor oculto, ViewModel recusa ativar, serviço/tela experimental desabilitados no manifesto. Três classes Android exclusivas do executor estão explicitamente ignoradas durante a pausa. Seus contratos JVM preservados continuam passando. A sandbox deixa de ser bloqueio desta beta.

## Aviso implementado

Aviso único local antes de instalação/atualização iniciada no app, com caixas **Estou ciente** e **Terei cuidado, relaxa**. Ambas obrigatórias para Continuar; back/toque fora não confirma nem fecha. O aceite só é gravado no botão e é compartilhado entre APKs manuais/atualizações/todas, preparação/repetição em lote e novels. Os gerentes também bloqueiam iniciar instalações sem o aceite; tarefas em segundo plano não mostram diálogo nem instalam código até a primeira confirmação manual. Instalação externa ao Polaris não pode ser interceptada por esse fluxo.

O aceite é appState local: a exportação não o inclui e a importação ignora um valor fabricado. Não concede confiança automática a repositório, assinatura ou achados de quarentena. Seleção experimental antiga aguarda aceite antes de executar no processo normal; o aviso também pode aparecer ao abrir as telas de extensões/preparação/detalhes nessa migração. Após revisão, seleções antigas são retiradas e extensões recarregadas; banco/cookies experimentais são preservados sem distribuir credenciais automaticamente.

## Verificação

Gradle final BUILD SUCCESSFUL em 2min04s: **931 testes do app executados e aprovados**, incluindo 12 novos. Mais 85 casos de domain antes aprovados ficaram UP-TO-DATE: **1016/1016** nos relatórios, sem falhas/skips JVM. Comparação contra 1004 casos arquivados da .3: nenhum ausente e 12 novos aprovados; a base não foi reexecutada.

Os novos casos verificam combinação das caixas, decisão persistida antes da ação, recusa sem aceite, reconstrução do controlador, falha/gravação ignorada, limpar dados, chave real de SourcePreferences, criador/restaurador reais de backup e política de execução durante a pausa. O teste de backup inclui dados comuns preservados e um aceite fabricado recusado. Não há instância do instalador de sistema ou interface Compose nesses testes JVM.

App e instrumentação Kotlin compilados. Dois cenários Android de preferência nativa/componentes foram compilados, não executados. Três classes de instrumentação da sandbox ficam ignoradas porque seus componentes estão desativados; isso não é contagem de aprovação em Android. Os manifestos mesclados main e universal foram inspecionados: ambos componentes enabled=false. Quatro testes completos do overlay (incluindo flags no manifesto aplicado) e 16 de empacotamento passaram. Testes pessoais e aceites visuais/instalação ficam para consolidação final, como pedido.

## Tamanho e limites

A referência local existente P20261113.3 foi lida como ZIP: APK de 272.970.356 bytes, dos quais 192.659.644 bytes compactados em bibliotecas nativas (70,6%). Não é um pacote atualizado e não mede contribuição da sandbox. Desativar preservando código não comprova redução de bytes; comparar pacotes equivalentes na distribuição. Não foi gerado novo APK do app nem Release.

O aviso informa riscos e não oferece barreira equivalente ao isolamento. Extensão em compatibilidade continua executando com acesso do app. Os guardas de consentimento não certificam código de terceiros nem substituem verificações de assinatura/integridade mantidas. Não houve mudança de dependências, SQL ou formato Protobuf. Conta/nuvem permanecem adiados.

Resultados públicos contêm apenas JSON legível com identidades/resultados/hashes e esta documentação; sem logs brutos, ZIP, proxy ou traces locais. [Decisão e escopo](../../../docs/PAUSA_SANDBOX_E_AVISO_P20261114_4.md) · [Quatro prioridades](../../../docs/BETA11_CHECKLIST.md).
