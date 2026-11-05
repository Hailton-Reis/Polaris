# Tipografia em português — P20261104.2

A Anime Ace incluída no aplicativo não contém os caracteres **Ç** e **ç**. O Android recorria à fonte do sistema, deixando essas letras com desenho e tamanho diferentes. As outras quatro fontes disponíveis contêm ambas as letras.

Este candidato complementa somente esses dois caracteres da Anime Ace com a Bubble Sans já incluída no APK. A altura das letras é ajustada pelas métricas das fontes; o texto continua contendo os caracteres corretos. Os arquivos das fontes permanecem intactos. A composição Unicode NFC também reúne letras e marcas de acento quando existe um caractere composto equivalente.

A mesma sequência de texto e estilos serve para medir e desenhar. O espaço entre linhas respeita as métricas da fonte, incluindo acentos e cedilhas, em vez do espaçamento fixo anterior de 0,98 vezes o tamanho. Peso e espaçamento não herdam a tipografia da interface.

O encaixe compara os espaços seguros já previstos para cada região. Antes, o primeiro espaço que aceitava o texto encerrava a busca, mesmo quando outro permitia letras maiores. Agora a escolha prioriza texto inteiro, palavras preservadas e maior tamanho que caiba, conservando a margem mais restrita em empates. As fronteiras medidas do balão ou painel continuam limitando a área de escrita.

## Escolha no leitor

**Configurações → Traduções → Fonte das traduções** escolhe a família usada nos textos traduzidos. O aplicativo ajusta tamanho e quebras para cada região; ele não identifica nem reproduz automaticamente a fonte original de cada balão. Anime Ace recebe o complemento descrito acima; as demais usam seus próprios caracteres.

Para experimentar uma alternativa que já contém cedilha, escolha **Bubble Sans**. Para conferir a correção mantendo a aparência usada anteriormente, mantenha **Anime Ace** neste candidato. Feche e reabra o leitor para redesenhar traduções salvas. Esta alteração de apresentação não exige executar novamente o OCR. Trocar o motor de OCR exige remover somente a tradução salva e traduzi-la de novo.

## Verificação e limites

O relatório em `integration/typography/20261104/` registra cobertura real das fontes e verificações de medição/desenho no Android. Os controles usam frases em português escritas para o teste. Um recorte original fornecido localmente permite conferir texto sobre arte; a imagem fica fora do repositório. Isso verifica tipografia e composição, sem atribuir uma nota à tradução automática.

O benchmark de OCR do capítulo 40 continua disponível em `integration/ocr-benchmark/20261104-chapter40/`. A qualidade editorial da tradução desse capítulo não foi medida: a preparação do modelo ML Kit excedeu o prazo no emulador. Formas decorativas, texto não reconhecido, balões conectados e desempenho em ARM ainda exigem validação. A revisão é um candidato interno, sem nova Release pública.
