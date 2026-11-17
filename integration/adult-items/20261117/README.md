# Filtrar obras mantendo fontes mistas — P20261117.5

Revisão de desenvolvimento para a próxima versão. **Sem novo APK/Release.**

O usuário esclareceu que quer consultar extensões mistas e filtrar as obras adultas, com opção de liberar após aviso. Foi removido o bloqueio por IDs de fonte e a leitura da marcação adulta da extensão pelo novo filtro. Permanecem os controles independentes de carregamento/idiomas/fontes habilitadas, a biblioteca e a leitura original/fixa existente.

- `RESULT.json`: escopo, confirmação no aplicativo e validação. 977 testes app beta executados/aprovados + 87 domain release anteriores/UP-TO-DATE = 1.064 casos; nenhum caso falhou ou foi pulado. Overlay4/empacotamento27/comparador21 aprovados.
- `policy-tests.json`: sete testes da política anterior substituídos por sete da política pedida. Inclui os nomes antigos/novos; nenhum aumento líquido do total. Não se afirma que todos os nomes da baseline foram preservados.
- `unit-comparison.json`: mantém o resultado bruto da comparação e lista as substituições esperadas. Não há casos anteriores ausentes além desses sete, nem novas falhas/skips. A baseline P20261117.4 foi preservada sem alteração.
- `focused-results.json`: os 86 controles focados passaram no código final antes da suíte completa.
- `unit-test-results.json`: todos os casos e suas variantes reais beta/release.
- `source-provenance.json`: hashes dos originais, fontes/testes/scripts atuais e overlay validado.

Os controles percorrem a política e os serviços/modelo reais: resultados comuns e adultos na mesma fonte, fontes diferentes consultadas, aliases sem reinserir obras adultas, alternativas sem rótulo disponíveis e troca da opção com busca em andamento. Provedores são simulados, sem HTTP real. A preferência reativa e o pool real de cinco tarefas são usados no teste do modelo de busca.

O diálogo foi compilado e revisado no código: tentar desligar retorna falso antes de gravar, Cancelar/voltar/dismiss não altera a preferência, e somente o botão de confirmação grava falso. Não houve execução da interface em aparelho nem teste automatizado de clique no diálogo nesta revisão. Religar é imediato e a preferência é persistida pelo mecanismo existente.

Conteúdo sem marcação ou identificado tardiamente pode aparecer; não há análise de imagens ou garantia de controle parental. Sem modelo, dependência ou consulta extra para classificar. Concorrência e agendamento periódico não mudaram. [Configuração e limites](../../../docs/FONTES_MISTAS_P20261117_5.md).
