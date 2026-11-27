# Filtro +18 — P20261117.4

Evidências filtradas da revisão para a próxima versão. **Sem novo APK ou Release.**

- `RESULT.json`: escopo, limites e validação final. 977 testes app beta executados/aprovados e 87 domain release anteriores/UP-TO-DATE: 1.064 casos. 25 novos, nenhum anterior ausente. Overlay4/empacotamento27/comparador21 aprovados.
- `red-results.json`: três falhas de comportamento reproduzidas no código de produção anterior inalterado: obra marcada nos resultados, gênero descoberto nos detalhes e alternativa adulta adotada/amostrada. Sem novo parâmetro para rotear a produção na reprodução.
- `focused-results.json`: 85 controles aprovados antes do último controle de classificação explícita no memo dos detalhes; a rodada completa cobre o código final.
- `new-tests.json`: fonte adulta sem marca individual, fonte mista, classificação tardia, acentos/separadores/caixa, casos que não são classificação adulta, opção desligada, biblioteca/favorito preservados, troca durante busca/checagem, metadados do provedor sem contaminar o memo salvo e validade do cache.
- `unit-test-results.json` e `unit-comparison.json`: todos os casos das variantes reais beta/release e comparação com P20261117.3.
- `source-provenance.json`: hashes dos arquivos de produção, testes, scripts e overlay final; hashes dos originais usados na reprodução.

Os testes usam o serviço e o modelo de busca reais com provedores simulados, sem HTTP real. A troca durante busca usa o pool real de cinco tarefas e uma preferência reativa no teste: a implementação de preferências apenas em memória do projeto não emite mudanças. Essa adaptação existe somente no teste. Não houve execução da interface no aparelho; recursos/interface foram compilados.

O filtro não apaga a biblioteca, nem desabilita a leitura original/fixa existente. Bloqueia descoberta/adopção automática conforme os metadados disponíveis. Conteúdo sem marcação ou classificado tardiamente pode aparecer; não analisa imagens nem garante controle parental. Navegação paginada pode exigir recarregar após mudança posterior de metadados.

A busca geral continua com cinco tarefas; as alternativas automáticas, com duas. Mais concorrência em primeiro plano e atualização periódica em segundo plano continuam como propostas. Nenhum trabalho periódico novo. Sem dependência nativa, modelo ou migração SQL novos. Sandbox e conta/nuvem continuam adiadas.

[Comportamento e configuração](../../../docs/FILTRO_ADULTO_P20261117_4.md). Sem logs brutos, caminhos privados, credenciais ou dados pessoais nesta evidência.
