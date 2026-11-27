# Concorrência de alternativas conforme a visibilidade — P20261117.6

Revisão de desenvolvimento para a próxima versão. **Sem novo APK ou Release.**

As operações alternativas compartilham quatro vagas com o app visível e uma em segundo plano, entre obras e instâncias no mesmo processo. O processo começa no limite de segundo plano; callbacks existentes do ProcessLifecycleOwner atualizam a admissão. A fonte original fica fora deste limite, que não representa todas as requisições HTTP do app/extensões. A busca textual geral continua com cinco tarefas.

A mudança para segundo plano não cancela operações já admitidas: espera que terminem antes de admitir outra conforme o limite menor. Voltar à tela acorda a fila sem nova chamada de busca. A fila concede vagas na ordem de chegada. Cancelamento durante espera, após concessão antes de retomar, durante operação e em lote libera capacidade; erros também liberam as vagas.

- `RESULT.json`: política, escopo e validação. 989 testes app beta executados/aprovados e 87 domain release anteriores/UP-TO-DATE: 1.076 casos. 12 novos, nenhum erro/skip. Overlay4/empacotamento27/comparador21 aprovados.
- `focused-results.json`: 49 casos focados aprovados antes do último controle adicional com threads reais do dispatcher e da mudança do marcador. A rodada completa cobre todos os fontes/testes finais.
- `new-tests.json`: nove controles do limitador (incluindo concorrência real entre threads) e três de catálogo; um teste antigo foi renomeado para refletir quatro vagas em primeiro plano, sem removê-lo da cobertura.
- `unit-comparison.json`: mantém o resultado bruto e a única substituição esperada de nome; nenhum outro caso anterior ausente, falha ou skip novo. Baseline P20261117.5 preservada sem alteração.
- `simulated-timings.json`: atrasos virtuais em catálogo real. Três catálogos de um segundo: 2→1 segundo em primeiro plano, três segundos em segundo plano. Quatro checagens de um segundo: 2→1 segundo em primeiro plano. Duas instâncias com oito checagens: duas ondas de quatro. Não é benchmark de rede/aparelho; valores anteriores vêm dos controles da revisão precedente.
- `unit-test-results.json`: todos os casos e variantes reais beta/release.
- `source-provenance.json`: hashes dos originais, fontes/testes/scripts atuais e overlay validado.

O controle com threads reais usa 16 operações em Dispatchers.Default: confirma pico de quatro, redução para uma após esvaziar as operações já admitidas, conclusão de todas e contagem final zero. Os demais controles de tempo usam corrotinas virtuais e provedores simulados. Não houve HTTP real, medição de bateria/RAM/tempo em aparelho ou execução física dos callbacks Android. Integração de ciclo de vida compilada e revisada no código.

O agendamento opcional da biblioteca continua inalterado/desativado por padrão. Nenhum novo trabalho periódico foi criado/ativado. Atualizações saudáveis comuns continuam sem buscar todas as extensões; descoberta ampla mantém os gatilhos anteriores. Orçamentos de fila/tempo e dependência de cancelamento cooperativo permanecem: menor concorrência pode deixar mais trabalho para outra tentativa. Buffer de resultados prontos passa a quatro, sem medição de pico de memória.

[Comportamento e limites](../../../docs/CONCORRENCIA_FONTES_P20261117_6.md). Filtro +18 por obra, biblioteca, associação/numeração, fonte fixa e revisões anteriores preservados. Sandbox e conta/nuvem continuam adiadas. Sem caminhos privados, credenciais, logs brutos, dados pessoais, modelos ou bibliotecas nesta evidência.
