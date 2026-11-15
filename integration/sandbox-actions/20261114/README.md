# Ações locais da sandbox — P20261114.3

Continuação da beta.11 no mesmo PR12 em rascunho. Ações de Preference padrão, selecionável e com chave/listener podem ser confirmadas na interface e executadas no worker. Sem Intent/fragment/custom view, sem HTTP nessa operação, com conferência de estado/token/hierarquia e de alterações fora da própria fonte. Retorno true síncrono é exigido; falha/false não produz snapshot de sucesso. Não há tentativa automática adicional.

## Validação

Dois casos positivos foram rejeitados pelo contrato anterior, antes de habilitar o novo descritor. O contrato final executou **919 testes do app, todos aprovados**, incluindo 15 novos. Mais 85 casos de domain antes aprovados ficaram UP-TO-DATE: **1004/1004** nos relatórios, sem falhas/skips. Comparação contra 989 casos arquivados da .2: nenhum ausente e 15 novos aprovados; a base não foi reexecutada.

Os casos JVM exercitam o contrato puro: seleção entre grupos, chaves/flags inválidas, ancestrais indisponíveis, descritor antigo, campos não acionáveis, escopo, retorno falso, erro, invocação única por chamada, recusa HTTP e subárvore não declarada. Não instanciam AndroidX nem executam a extensão real.

App e instrumentação compilaram, BUILD SUCCESSFUL 2min30s. A expectativa antiga de um callback sintético que lança erro foi atualizada para o novo tipo de ação e a instrumentação final foi recompilada com sucesso (1min23s); nenhuma fonte de aplicação mudou depois da rodada de testes JVM. Quatro testes completos de overlay/idempotência e 16 de empacotamento passaram.

A fixture DEX foi realmente compilada da fonte auditável em fixture/ e mantém todas as classes anteriores. São 42.964 bytes, hash registrado em fixture/provenance.json. Cinco fontes novas cobrem sucesso, false, erro, HTTP e tentativa de alterar outra fonte. Seis novos cenários Android de serviço/proxy foram compilados: UID isolado/reload sem repetir, false/erro sem commit, alvos indisponíveis, token antigo, HTTP sem capacidade e escopo entre duas fontes. **Nenhum foi executado nesta rodada.** Confirmação visual, fontes reais e runtime Android/ARM ficam para a consolidação final, conforme pedido do usuário.

## Limites

Somente listener padrão com contrato síncrono. Intents, telas personalizadas, OAuth/Cloudflare, HTTP/POST, ações assíncronas e novels continuam pendentes. O corpo de um listener pode tentar capacidades indisponíveis e então falhar. Não há detecção geral de tarefas em segundo plano nem espera por elas; somente o snapshot devolvido entra no resultado. A inicialização OPEN mantém registro/defaults anteriores, sem transação global ou promessa de exatamente uma vez após morte de processo/tentativa manual. Classes/listeners da extensão não vão para a interface do host e não há fallback automático para compatibilidade.

Resultados públicos são JSON legível com identidades/resultados/asserts/hashes, sem logs brutos/ZIP/configuração de ambiente/traces locais. Sem mudança de dependências, SQL ou Protobuf. Conta/login Google/nuvem permanecem adiados. Sem novo APK do app ou Release: o interno disponível continua P20261113.3, sem as revisões posteriores. [Escopo](../../../docs/SANDBOX_ACOES_LOCAIS_P20261114_3.md) · [Checklist](../../../docs/BETA11_CHECKLIST.md).
