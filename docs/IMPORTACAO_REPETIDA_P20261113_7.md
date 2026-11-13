# Importação repetida e retomada — P20261113.7

Desenvolvimento da beta.11/código 112. Conta do Polaris, login Google e sincronização em nuvem ficam adiados por decisão do usuário. O foco desta etapa é o armazenamento local; o backup existente continua disponível.

## Comportamento

Novas importações com os mesmos bytes e formato passam a reutilizar a publicação já verificada na pasta local selecionada. A identificação usa SHA-256 completo e contagem real de bytes, calculados durante a cópia temporária. Nome/título não define igualdade: outro conteúdo com o mesmo nome continua separado, e renomear o título no formulário não cria outra cópia de bytes idênticos.

Os nomes de pasta mantêm um prefixo legível e um sufixo de formato/hash. A detecção enumera os nomes apenas na pasta local configurada, sem varrer o celular. Mais de um candidato para o mesmo conteúdo exige revisão, sem escolher arbitrariamente uma entrada. Uma publicação existente só é reutilizada após conferir o marcador e reler os bytes: dados editados, corrompidos ou incompatíveis ficam preservados e a operação falha.

A publicação usa pasta temporária vazia e própria, verifica por releitura o conteúdo e os metadados antes do rename, resolve novamente o destino e confere o que ficou publicado. Os nomes e o conteúdo de arquivos existentes não são substituídos para contornar erros. Se o rename pode ter ocorrido, ou se o banco/categorias falham depois, a cópia completa é conservada. Repetir a inclusão com o mesmo conteúdo pode terminar o registro sem publicar outro arquivo.

Quando já existe favorito para a URL publicada, a entrada é aberta com o mesmo ID, preservando título, categorias, data e estado de leitura. As novas opções do formulário não substituem a organização anterior; ajustes podem ser feitos na entrada existente. Uma linha ainda não favorita é retomada sem recriar sua identidade ou apagar suas notas/flags. Categorias são atribuídas antes da confirmação de favorito.

O marcador `.polaris-import` não usa extensão JSON: o leitor local trata um JSON na pasta como metadados legados e pode convertê-lo em ComicInfo.xml. A reutilização aceita essa conversão e conserva metadados/capas extras. Não há mudança no esquema SQL ou formato do backup.

## Limites

- Deduplicação automática vale para publicações criadas com este marcador, no diretório local atual e com o mesmo formato. Pastas legadas/renomeadas, aliases de formato, arquivos parecidos e duplicatas já existentes não são mesclados automaticamente.
- O fluxo ainda cria um temporário e valida o arquivo escolhido. Reutilizar evita outra cópia no destino, mas não elimina o temporário nem a materialização posterior para leitura. Novas cópias incluem releituras/hash adicionais; desempenho e pico precisam de medição no A12/ARM.
- A retomada é feita ao repetir uma inclusão; não há varredura automática para recriar o banco inteiro. Staging abandonado após morte do processo, falha de rename sem destino visível, limpeza desses resíduos e reconciliação entre volumes ainda precisam de política própria. Cópias de propriedade incerta não são apagadas.
- Provedores precisam permitir listar e reler os arquivos. Uma listagem nula não equivale a pasta vazia. Checks de espaço continuam consultivos; a API UniFile não oferece transação atômica única entre provedor e banco nem elimina corridas de agentes externos.

[Validação executada e limitações](../integration/document-import/20261113/README.md) · [Checklist](BETA11_CHECKLIST.md).
