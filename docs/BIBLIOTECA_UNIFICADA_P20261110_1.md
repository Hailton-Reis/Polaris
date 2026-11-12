# Biblioteca unificada — P20261110.1

Revisão de desenvolvimento da beta.11/código 112. A beta.10 pública, seus APKs e a branch main permanecem inalterados.

## Comportamento

Ao abrir a biblioteca, o Polaris pode associar edições favoritas já existentes da mesma obra e apresentar uma entrada. O agrupamento exige metadados corroborados e numeração compatível; nomes traduzidos precisam de identidade de catálogo já confirmada. Homônimos, sequências, novelas, conteúdo local, metadados insuficientes e fontes fixadas em conflito ficam separados.

A sequência reúne os capítulos das edições associadas. Para versões do mesmo número, uma fonte fixada tem precedência sobre a preferência automática de idioma. Sem ela, prefere português brasileiro, depois português e inglês, respeitando o capítulo aberto, a retomada e os demais critérios de seleção. A contagem de lidos e marcados considera cada capítulo lógico uma vez; categorias e a leitura mais recente são reunidas para apresentação. Alterar as categorias, remover a obra da biblioteca ou alternar a tradução automática pela entrada principal alcança as edições vinculadas. A posição parcial continua no capítulo nativo: a página 17 de uma edição não é copiada para a página 17 de outra.

Em configurações dos capítulos, **Edições vinculadas** permite abrir os registros originais e **Separar edições**. A separação impede nova associação automática; **Permitir associação automática** remove essa preferência e exige nova validação.

## Preservação dos dados

A associação grava somente uma referência recíproca no memo dos favoritos originais, dentro de uma transação. Não apaga favoritos, não transfere capítulos, histórico, notas, glossário, rastreadores ou fontes fixadas e não muda a estrutura do banco. Uma mudança concorrente ou falha na segunda gravação cancela a transação inteira.

O grupo usa fonte e URL, não IDs locais, para poder ser restaurado em outro banco. Uma associação incompleta, obsoleta, incompatível ou explicitamente separada não oculta suas edições. A lista agregada só substitui as entradas após conseguir ler os capítulos de todos os membros.

Downloads e traduções continuam nas pastas de suas edições originais. O leitor, a fila de download, a verificação de arquivos, a tradução manual e a exclusão por capítulo encaminham cada operação para o dono nativo. Um indicador de armazenamento é criado pelo aplicativo em memória e removido nas fronteiras de persistência e de extensão. Nenhuma página é copiada por esta associação.

As consultas de atualização por fonte, restauração, cálculo de intervalo e migração explícita continuam limitadas ao registro nativo. Esse limite evita que URLs iguais em fontes distintas sobrescrevam capítulos de outra edição.

## Backup e interoperabilidade

O backup continua exportando os registros nativos favoritos, seus capítulos e dados pessoais. A associação é informação adicional no memo, sem novo formato obrigatório. Um leitor que ignore o memo pode mostrar as edições separadas; isso preserva os registros em vez de depender do agrupamento do Polaris. Não há promessa de manter o agrupamento em leitores que descartem esse campo.

A prova automatizada usa o criador/restaurador de backup de produção, Protobuf e dois bancos Android com IDs diferentes. O aceite completo de ida e volta pela interface e pelo banco de Mihon/Tachiyomi externos continua pendente. Preserve o backup original.

## Limites e próxima validação

Esta etapa associa edições que já estão na biblioteca; não instala novas extensões nem faz uma busca ilimitada na internet. Reutiliza a identificação entre fontes da revisão anterior. Processa lotes limitados de grupos e mantém casos ambíguos visíveis. Na P20261110.1, a numeração era conferida antes da associação. A [revisão posterior P20261110.2](REVISAO_BIBLIOTECA_P20261110_2.md) acrescenta revalidação nas consultas e na transação, incluindo mudanças que mantêm a mesma quantidade de capítulos. Metadados incompatíveis ou vínculos incompletos fazem as edições reaparecer separadas, e a separação manual continua disponível.

As provas locais usam dados sintéticos e componentes reais de armazenamento. Falta validar biblioteca restaurada, pastas de download reais, abertura/leitura e atualização com provedores reais, além de memória e tempo em ARM32/ARM64. A projeção de grupos consulta suas listas de capítulos; desempenho em bibliotecas grandes precisa ser medido antes de prometer melhora.

[Resultados e escopo das evidências](../integration/library-consolidation/20261110/README.md).
