# Cancelamento do OCR e da tradução — P20261115.5

Continuação da beta.11/código 112, sem novo APK ou Release. Sandbox continua arquivada/retirada e conta/nuvem permanecem adiadas.

## Problema reproduzido

Cancelar uma corrotina que aguarda uma Google `Task` não interrompe necessariamente o processamento iniciado pelo ML Kit. O caminho de OCR de página inteira usava `Task.await()` cancelável: o coordenador podia liberar seu mutex e fechar/trocar o motor enquanto a tarefa anterior continuava pendente. Os tradutores também podiam sair pelo cancelamento e fechar o cliente antes do término da inferência.

Três controles com `TaskCompletionSource` real, coordenador `OcrEngineManager` de produção e inferência substituída por tarefas controladas reproduziram fechamento/troca/liberação prematuros. A reprodução primeiro centralizou o `await` existente sem mudar sua semântica; os três cenários falharam antes da proteção. Nenhum modelo OCR/bitmap/inferência nativa foi executado nessa reprodução.

## Correção

`awaitMlKitProcessing` confere o cancelamento antes de iniciar uma operação, aguarda a tarefa de processamento já iniciada em contexto não cancelável e reconfere o chamador antes de entregar resultado ou erro. O mutex e a limpeza do cliente permanecem com o fluxo chamador até a Task chegar a um estado terminal. Um resultado que chega após o cancelamento não deve virar tradução publicada.

O limite é compartilhado pelo OCR ML Kit de página inteira e por faixas, pela tradução de quadrinhos e pela tradução de documentos. A proteção regional anterior foi centralizada; o bitmap da faixa continua sendo reciclado depois de a Task terminar.

Os caminhos contextual/individual de tradução passam a propagar `CancellationException`, sem tratá-la como motivo para tentar outra inferência. Há checkpoints também antes de percorrer/aplicar resultados de cache. Preparação/download de modelos mantém seu `await` cancelável: não é incluído nessa espera de processamento.

Não foram acrescentados modelos, dependências, processos, opções de interface ou mudanças no formato de tradução. O padrão de OCR, as faixas experimentais e a política de carga por memória/ABI continuam como estavam.

## Validação e limites

Os testes JVM usam Google Tasks reais e o coordenador de produção com motor de controle, sem SDK de reconhecimento ou tradução executando modelos. Conferem liberação/troca após cancelamento, descarte de resultado tardio, sucesso, falhas com causa preservada, cancelamento do próprio SDK, chamador já cancelado, falha síncrona, fila cancelada, serialização e múltiplas chamadas de encerramento. A recuperação de stack trace de corrotinas pode criar outra instância da exceção; os controles conferem tipo, mensagem e retenção da causa original.

Dois controles Android exercitam Google Task/corrotina/coordenador e chamador previamente cancelado. São compilados para a rodada final; não executam modelo OCR, bitmap ou inferência nativa. A compilação desses controles não equivale a executar OCR no aparelho.

A espera não acrescenta timeout nem capacidade de interromper o processamento nativo: se o SDK não concluir a Task, o recurso permanece reservado. Isso protege a ordem de uso/liberação, sem garantir tempo de conclusão, ausência de OOM ou desempenho. Diagnóstico e medições no A12/ARM32/ARM64, qualidade, memória e fluxo real de leitura/tradução continuam pendentes na consolidação final.

## Resultado da rodada

Compilação final aprovada em 2min29s. Foram executados e aprovados 901 testes do app, incluindo 12 novos; mais 85 de domain previamente aprovados ficaram UP-TO-DATE. Total de 986 casos nos relatórios, sem falhas/skips ou casos anteriores ausentes. Quatro testes de aplicação/idempotência/CRLF/drift do overlay e 16 de empacotamento passaram. Os dois controles Android foram compilados, não executados.

[Resultados filtrados e hashes](../integration/mlkit-cancellation/20261115/README.md) · [Checklist ativo](BETA11_CHECKLIST.md).
