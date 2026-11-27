# Alternativas conforme a visibilidade do app · P20261117.6

Revisão de desenvolvimento para a próxima versão. Sem APK ou Release novo.

A atualização de catálogos alternativos e a descoberta de fontes passam a compartilhar até **quatro operações** enquanto o app está visível e **uma** quando está em segundo plano. O processo começa com uma vaga; os callbacks existentes de início/parada do ciclo de vida do aplicativo atualizam o limite. Um serviço com notificação, sem tela visível, continua no limite de segundo plano.

O limite é compartilhado entre obras e instâncias do catálogo neste processo. Uma operação inclui atualização/pesquisa, detalhes/capítulos e amostra de leitura quando necessária. A fonte original continua fora desse limite; ele não limita todas as requisições HTTP do app ou aquelas disparadas internamente por extensões. A busca geral textual mantém seu pool anterior de cinco tarefas.

Ao sair da tela, operações já admitidas terminam normalmente, preservando os resultados; enquanto sobra mais de uma em andamento, nenhuma outra recebe vaga. Quando o lote anterior esvazia, prossegue uma por vez. Voltar ao app libera as vagas adicionais imediatamente para quem já aguarda, sem nova pesquisa ou temporizador. A notificação de segundo plano depende dos callbacks do ciclo de vida do Android, que podem ter um pequeno atraso.

A fila mantém a ordem de chegada e não reserva uma obra inteira. Cancelamento na espera, após concessão e antes da retomada, durante a operação ou em lote devolve as vagas. Erros também liberam capacidade. A admissão aguarda por corrotina; não mantém uma thread bloqueada esperando vaga.

Continuam os limites de tempo, cache diário/tentativa incompleta, reaproveitamento de consultas, associação/numeração, idiomas, fonte fixa, filtro +18 por obra e proteção dos dados. O buffer de resultados prontos passa a quatro; o pico de memória não foi medido. Em segundo plano, a fila mais lenta pode deixar mais fontes para uma tentativa futura quando esgota o orçamento; não há promessa de varrer todas em um ciclo.

## Atualização periódica existente

O agendamento da biblioteca já existente permanece em **Configurações → Biblioteca → Atualizações automáticas**. A preferência começa desativada e oferece intervalos de 12/24/48/72/168 horas, respeitando as restrições de rede/carga/bateria e o Android. Esta revisão não ativa, muda ou cria outro trabalho periódico.

Quando esse trabalho atualiza alternativas já confirmadas, vale o limite de uma operação com o app em segundo plano. A atualização saudável comum continua sem pesquisar todas as extensões. A descoberta ampla continua dependendo das solicitações anteriores do app/recuperação de fontes; elegibilidade após tentativa incompleta não é um relógio para executar outra busca. Android/Doze pode adiar o trabalho.

## Validação e limites

Os [controles](../integration/adaptive-source-discovery/20261117/README.md) verificam concorrência, FIFO, troca de visibilidade, duas obras/instâncias e cancelamento, com catálogo real e provedores simulados. Os tempos virtuais são provas de controle, não medições de fontes reais, rede, bateria ou aparelhos. Não se promete ganho proporcional ao número de vagas. Sandbox, conta/nuvem e análise de imagens continuam fora desta revisão.
