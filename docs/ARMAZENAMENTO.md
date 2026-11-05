# Armazenamento: análise crítica

**Revisão analisada:** `P20261101.1` / `0.1.0-beta.1`, código de 01/11/2026. Esta análise revisa a implementação e as evidências existentes; não substitui uma medição no celular e não gera nova versão do aplicativo.

**Conclusão:** a tradução em texto não parece ser a principal parcela no exemplo sintético, mas ainda não há evidência suficiente para declarar baixo consumo total. Instalação, modelos, duplicação de documentos, temporários e páginas de PDF precisam entrar na avaliação antes de recomendar uma distribuição mais ampla.

## O que foi efetivamente medido

| Medição | Resultado | Limite da evidência |
| --- | ---: | --- |
| Arquivo APK ARM64 | 201.397.112 bytes — 201,4 MB / 192,1 MiB | Pacote de instalação, não tamanho total instalado |
| Arquivo APK ARM32 | 161.599.289 bytes — 161,6 MB / 154,1 MiB | Pacote de instalação, não tamanho total instalado |
| JSON sintético, inglês | 47.772 bytes | 20 páginas / 200 blocos, campos básicos |
| JSON sintético, japonês | 51.172 bytes | Serialização de texto, sem executar OCR |
| JSON sintético, chinês simplificado/tradicional | 48.172 bytes | Serialização de texto, sem executar OCR |
| JSON sintético, coreano | 53.172 bytes | Serialização de texto, sem executar OCR |

Os JSONs foram gerados e relidos pelas classes de produção. O ensaio não inclui todas as combinações de agrupamento, regiões de limpeza/layout, máscaras opcionais, frases em cache ou a variação de um capítulo real. **Não permite afirmar que toda tradução custa 50 kB nem calcular uma porcentagem fixa sobre o original.**

O Google descreve os [modelos de tradução ML Kit](https://developers.google.com/ml-kit/language/translation/android) como tendo aproximadamente 30 MB por idioma. Isso é referência do fornecedor, não medição dos modelos instalados nos aparelhos deste projeto.

## As parcelas do consumo

```text
Instalação e bibliotecas
+ modelos e dados internos
+ originais baixados / cópias importadas
+ traduções salvas e vocabulário
+ caches e temporários
+ custos do sistema de arquivos e do Android
```

A tradução dos quadrinhos guarda texto e coordenadas em JSON. O pipeline não persiste uma segunda coleção completa de imagens já traduzidas. Isso não elimina as outras parcelas: PDFs são renderizados em páginas PNG para leitura, e documentos podem ser materializados em cache.

O glossário e as correções aprendidas ficam separados das traduções salvas dos capítulos e do cache de frases automáticas. A exclusão pelo fluxo de downloads do app preserva esse vocabulário. Remover uma entrada da biblioteca, excluir um arquivo pelo gerenciador do celular, limpar dados e desinstalar são operações diferentes; não devem ser tratadas como o mesmo ciclo de limpeza.

<a id="revisao-critica"></a>

## Revisão crítica

### 1. Importação pode manter mais de uma cópia

O arquivo escolhido permanece no celular. O importador faz uma cópia temporária e outra na pasta local do Polaris; a preparação para leitura pode materializar novamente o documento no cache privado.

Para um arquivo local de tamanho **F**, as etapas podem chegar a:

| Etapa | Parcelas do arquivo, antes de imagens renderizadas e demais dados |
| --- | --- |
| Durante a importação | Original no celular + temporário + cópia no destino: até aproximadamente **3 × F** |
| Importação concluída | Original no celular + cópia gerenciada: aproximadamente **2 × F** |
| Preparação da leitura | Original + cópia gerenciada + materialização em cache: até aproximadamente **3 × F** |

A tabela descreve etapas do fluxo, não uma promessa de alocação exata. Elas podem usar volumes diferentes: por exemplo, biblioteca no cartão SD e cache no armazenamento interno. Um arquivo de 100 MB pode representar cerca de 300 MB nessas parcelas durante uma etapa, além das páginas renderizadas. Download por URL não tem necessariamente o primeiro original externo, mas também usa temporário e cópia no destino.

**Prioridade:** medir o pico nos aparelhos e avaliar reaproveitamento de arquivos/preparação para leitura, ou referência persistente ao documento quando apropriado. Preservar a leitura caso o usuário mova, revogue acesso ou apague o original continua sendo um requisito.

### 2. O limite de 256 MiB é uma meta parcial

A meta cobre somente `document-files`, `pdf-pages` e `document-translations`. Arquivos com uso ativo são protegidos e podem ultrapassá-la temporariamente. Não limita downloads, importados, modelos, glossário, cache de frases ou os outros caches herdados da base.

**Prioridade:** verificar o comportamento com documentos grandes, várias leituras abertas e pouco espaço livre. Considerar contagem de arquivos e custo do sistema de arquivos, além da soma dos comprimentos dos arquivos.

### 3. O limite por arquivo não garante espaço livre

O importador limita o tamanho do arquivo e limpa temporários no fluxo normal. Isso é diferente de verificar capacidade disponível para temporário, destino, modelos e renderização. A revisão não identificou uma reserva de espaço para o pico completo antes dessas operações.

**Prioridade:** tratamento e testes de espaço insuficiente em cada volume, interrupção e falha do provedor Android. Uma falha deve conservar os arquivos do usuário e explicar o que foi ou não incluído.

### 4. Repetir a importação pode multiplicar documentos

Cada importação recebe um diretório próprio; não há deduplicação por conteúdo. Se ocorrer falha depois de publicar a pasta e antes de concluir banco/categorias/favorito, a cópia publicada pode permanecer. Repetir a inclusão pode criar outra cópia.

**Prioridade:** detectar ou reconciliar inclusões repetidas e recuperar uma inclusão incompleta. Evitar apagar automaticamente um arquivo válido para disfarçar uma falha de indexação.

### 5. Cache de frases e modelos precisam de avaliação própria

O cache de frases tem limite de 4.000 entradas por obra/par de idiomas, e não um orçamento global em bytes. Excluir capítulos pelo app remove frases relacionadas, mas o comportamento com muitas obras e grandes blocos ainda precisa ser medido. O vocabulário persistente é intencionalmente separado.

Os modelos são reutilizados, mas somam espaço. O painel lista idiomas e agrega os modelos nos dados internos; não mostra uma medição exata em bytes de cada modelo individual. O glossário atual usa o título da obra como parte de sua identificação; títulos iguais merecem revisão para evitar misturar contextos.

**Prioridade:** medir o crescimento com uso prolongado e oferecer gerenciamento que distinga cache descartável, modelos e vocabulário que o usuário deseja manter.

### 6. O painel oferece estimativa, não auditoria exata do disco

O painel soma tamanhos de arquivos do app e das pastas configuradas. Pode parar por limite de tempo/entradas e marca medições incompletas com `+`. Não inclui todos os originais fora do Polaris nem todo o custo de instalação/otimização do Android. Alocação em blocos e metadados do sistema de arquivos também podem diferir do comprimento dos arquivos.

**Prioridade:** comparar os números com os dados de armazenamento do Android e registrar separadamente o que não foi possível medir. Não somar valores incompletos como se fossem um total preciso.

### 7. Excluir e baixar de novo ainda precisa de teste físico

A implementação cancela e aguarda o tradutor antes de excluir arquivos pelo fluxo do app, remove a tradução/cache correspondente e conserva glossário/correções. Os testes cobrem ordem, falha e preservação do vocabulário. Isso ainda não comprova o ciclo inteiro em um provedor de arquivos Android real, com o app em segundo plano ou durante falta de espaço.

**Prioridade:** registrar tamanho antes/depois, tentar excluir durante processamento e verificar os resíduos. Conferir também as diferenças entre remover favorito, apagar download e apagar externamente um arquivo.

## Armazenamento e memória RAM são avaliações distintas

Uma página de PDF de 4 milhões de pixels em ARGB pode precisar de cerca de 16 MB apenas para seu bitmap, além de decodificação, OCR e outras estruturas. A fila mais conservadora e o limite de pixels ajudam, mas não garantem um limite total de RAM ou desempenho no A12/S8+.

Não deduzir consumo de RAM a partir da meta de cache em disco. Velocidade, aquecimento, interrupção em segundo plano e estabilidade ainda precisam de teste físico.

## Próxima medição nos celulares

A matriz inicial inclui A12, S20 FE, S8+ e provável A52, conforme os aparelhos informados. Android, ABI e capacidade disponível de cada unidade ainda não foram registrados.

| Momento | Registrar |
| --- | --- |
| Instalação inicial | Tamanho indicado pelo Android, sem biblioteca/modelos adicionais |
| Após modelos | Idiomas instalados e diferença de armazenamento |
| Após download/importação | Tamanho e tipo do original, cópias e temporários |
| Após leitura/tradução | Traduções, cache e pico observado durante a operação |
| Após fechar leituras e limpar cache | O que foi recuperado e o que permaneceu |
| Após excluir/rebaixar capítulo | Limpeza da tradução, retenção do glossário e funcionamento da automação |
| Pouco espaço/interrupção | Resultado, recuperação e eventuais cópias remanescentes |

Usar inicialmente os exemplos originais e depois arquivos autorizados representativos: livro textual, PDF com imagens, capítulo curto e capítulo longo. Não usar o resultado em inglês para aprovar OCR japonês/chinês/coreano.

## Evidências e implementação revisadas

- [Resultados automatizados e medições da candidata](https://github.com/Hailton-Reis/Polaris/blob/617aa0b992cc5b5966a6069d6e39eb3ebd50c4e7/integration/internal-beta/TEST_RESULTS.json).
- [Implementação integrada nesta revisão](https://github.com/Hailton-Reis/Polaris/blob/617aa0b992cc5b5966a6069d6e39eb3ebd50c4e7/integration/document-reader/document-reader.patch): `DocumentImporter`, `DocumentFiles`, `PdfPageReader`, `DocumentCacheBudget`, `PolarisStorageUsage`, `TranslationCache` e fluxo de exclusão.
- [Detalhamento anterior de armazenamento e ciclo de tradução](https://github.com/Hailton-Reis/Polaris/blob/617aa0b992cc5b5966a6069d6e39eb3ebd50c4e7/integration/internal-beta/STORAGE_AND_LIFECYCLE.md).

Esta atualização registra os pontos encontrados. Não declara os ajustes acima como implementados nem promove o candidato a versão estável.

## Atualização: preparação prioritária do inglês

O candidato P20261101.2 acrescenta uma verificação local e, quando necessário, preparação automática de inglês → português. Isso pode antecipar o armazenamento dos recursos de tradução para a primeira conexão adequada, antes de o usuário traduzir um capítulo. A opção pode ser desativada; o reconhecimento latino já estava incluído no APK.

A condição de armazenamento do Android usada pelo agendamento não reserva um número preciso de bytes. Ela não resolve, por si, os pontos sobre importação, temporários e consumo total identificados nesta análise. Veja [o fluxo e suas limitações](INGLES_E_TRADUCAO.md).


## Beta.8: pacote e catálogos de fontes

Os APKs publicados da beta.8 têm **194.508.943 bytes em ARM64** e **154.711.120 bytes em ARM32**. O acréscimo em relação à beta.7 é de **1.676.188 bytes por APK (1,60 MiB)**. Assets e bibliotecas nativas comparados permanecem idênticos; nenhum modelo novo foi incluído. Esses são tamanhos de download, não a ocupação instalada no Android.

A descoberta automática consulta metadados de catálogos; não baixa imagens de todos os provedores. Até quatro catálogos ficam ativos por obra, mas edições já vistas permanecem no banco para preservar histórico e downloads. Isso não representa uma quota de tamanho do banco. Um cenário artificial de mil capítulos nas mesmas quatro fontes soma cerca de 0,85 MiB apenas em JSON de origem e acréscimo de URLs; campos das edições, páginas/índices/WAL do SQLite e metadados específicos da extensão ficam fora dessa estimativa.

Traduções de edições alternativas usam identidades separadas para evitar aplicar texto/coordenadas de uma fonte em outra imagem. A exclusão do download pela lista remove suas edições e traduções, preservando o vocabulário. O fluxo completo continua dependendo de medição física.

[Análise da beta.8](https://github.com/Hailton-Reis/Polaris/blob/v0.1.0-beta.8/docs/SEQUENCIA_E_FONTES_P20261103_1.md) · [Parâmetros da estimativa](https://github.com/Hailton-Reis/Polaris/blob/v0.1.0-beta.8/integration/document-reader/source-storage-estimate_P20261103_1.json).

## Beta.9 / P20261104.4 — distribuição de 05/11/2026 UTC

Os APKs completos têm **199.132.104 bytes em ARM64** e **159.334.281 bytes em ARM32**. Isso mede o download, não a instalação. O assistente também baixa APKs de extensões, guardados internamente; a quantidade e o espaço dependem da seleção. A fila possui dois downloads simultâneos, mas não é uma quota de armazenamento. Os modelos, fontes e bibliotecas nativas permanecem iguais à revisão interna anterior; acrescentou-se a biblioteca Java de verificação de assinatura. [Notas e limites](versoes/0.1.0-beta.9.md).
