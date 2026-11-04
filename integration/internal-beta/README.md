# Polaris 0.1.0-beta.9 — candidato interno para teste

Revisão: **P20261104.3**. Android mínimo: **8.0 / API 26**. Este candidato ainda não foi publicado como Release. A beta.8 continua sendo a prévia pública. A conferência nos celulares ainda está pendente.

## Proteção de extensões e backups

A revisão P20261104.3 prepara e valida a extensão privada antes de substituir seu arquivo anterior. Falha ou cancelamento durante a preparação preserva a extensão funcional. Downloads simultâneos e novas tentativas têm arquivos e identificadores próprios.

Backups novos são gravados, fechados e relidos antes de registrar sucesso ou remover cópias antigas. A retenção mantém quatro cópias verificadas; arquivos antigos ilegíveis ou inválidos são preservados separadamente. O destino precisa permitir leitura e, para uma pasta, renomeação. Um destino incompatível produz erro explícito. O formato de backup e as identidades das fontes foram preservados.

A validação automatizada não substitui os testes em celulares, provedores SAF e Android 14+. A beta.9 segue sem lançamento público.

## Nome e ícone corrigidos

A beta.4 aplica **Polaris** ao nome mostrado pelo instalador e pelo Android, além de um ícone próprio com estrela e livro. A abertura e a tela Sobre usam a mesma identidade. O ícone adaptativo atende Android 8+ e tem versão monocromática para os temas de ícones do Android 13+.

O identificador do aplicativo foi preservado. O pacote de nuvem usa a mesma assinatura da beta.3 distribuída, permitindo solicitar atualização sobre essa instalação. A preservação efetiva de dados e a aparência após instalar ainda precisam de conferência no aparelho. Esta correção exige instalar a beta.4: os APKs já publicados da beta.3 continuam com a identidade antiga.

## Primeira publicação

A [Release v0.1.0-beta.3](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.3) foi publicada como pré-lançamento em 01/11/2026 e agora está aberta ao público, com descrição geral e download sem login. Os seis anexos tiveram tamanhos e SHA-256 conferidos. A publicação não confirma instalação nem consumo de armazenamento nos aparelhos. [Registro de publicação](PUBLICATION_STATUS.json). O relatório de compilação registra o estado anterior à publicação.

## Instalar e atualizar

O pacote contém dois APKs. Use **arm64-v8a** primeiro nos aparelhos Android de 64 bits. Se o sistema do aparelho for de 32 bits, use **armeabi-v7a**. A12, S20 FE, S8+ e o provável A52 são a matriz inicial; o modelo comercial sozinho não confirma a arquitetura e a versão instalada do Android. O S8+ precisa estar no Android 8 ou superior.

Instale apenas um APK por aparelho. Não é necessário o APK universal nem as versões x86 do emulador. Instalações e atualizações devem vir sempre da mesma máquina/assinatura usada para esse beta. Não apague a instalação antiga para contornar um erro de assinatura: isso pode remover os dados locais. O mantenedor deve reconstruir e compartilhar o APK com a assinatura original.

O mantenedor gera o pacote com a opção **4** do CMD atualizado. Ao concluir a comparação automatizada, a pasta de evidências contém **beta/**, com APKs ARM, hashes e exemplos. A opção **9** continua sendo o fluxo local de instalação já existente. Confira **P20261104.3** em **Sobre** antes de registrar resultados. O versionCode agora é **110**; a beta.8 pública usa 109.

## Uso inicial

- Para livros já baixados no celular: **Mais → Documentos e pesquisa → Explorar e adicionar arquivo**. Escolha um arquivo, seu tipo e suas categorias; só **Adicionar à biblioteca** faz a inclusão. O original continua no celular e o Polaris guarda uma cópia. Não há varredura geral dos PDFs do aparelho.
- Para quadrinhos: use as fontes/extensões escolhidas e os downloads existentes. Ative a tradução automática por obra quando quiser traduzir ao terminar o download.
- Para tradução: comece com **ML Kit**, entrada em inglês e saída em português. O OCR de inglês já acompanha o APK. Os recursos de tradução inglês → português passam por verificação local na abertura; se faltarem, a preparação automática aguarda rede sem cobrança e a condição de armazenamento do Android. Há um cartão em Documentos e pesquisa e nas configurações, com **Preparar agora** para usar a conexão atual. Uma instalação nova ainda precisa de internet. Depois de preparados, ML Kit pode traduzir sem conexão; fontes e downloads ainda dependem da rede. Os provedores de API continuam opcionais e usam a configuração de cada pessoa.
- **Usar o idioma de OCR declarado pela fonte** escolhe EN/JA/ZH/KO quando a fonte informa esse idioma. Fonte mista, desconhecida e documentos locais usam a entrada escolhida manualmente. Isso não é detecção do conteúdo.
- A automação global de japonês/chinês/coreano é **opcional e desativada inicialmente**, pois sua qualidade ainda precisa de teste. A escolha explícita de tradução automática por obra tem prioridade. **PaddleOCR permanece apenas em inglês**; use ML Kit nos testes de outros idiomas.

## Sobre e atualizações

A tela **Sobre** apresenta o propósito do Polaris, versão e revisão, mantenedor, créditos, projeto, histórico, versões publicadas, licenças e privacidade.

Em **Configurações → Atualizações do aplicativo**, a busca automática consulta as Releases do Polaris ao abrir o app, no máximo uma tentativa por dia por canal. **Verificar atualizações** faz uma consulta imediata, mesmo com a automação desligada. O download e a instalação continuam dependendo da sua escolha.

**Receber atualizações experimentais** começa **desativado**, inclusive neste candidato beta. Ative para incluir betas e outras prévias publicadas; desligar não rebaixa a versão instalada. Rascunhos não são distribuídos. O app só oferece um APK compatível com a versão, o Android, a arquitetura e o identificador do aplicativo, com metadados de atualização e hash SHA-256. Use sempre a assinatura original.

O repositório e as Releases são públicos, permitindo download pelo navegador sem conta do GitHub. O app consulta esse repositório sem credenciais. A seleção de betas exige ativar **Receber atualizações experimentais**, desativado por padrão. Consulta, download e instalação reais ainda precisam de conferência nos aparelhos. O guia de publicação descreve o `manifest.json` exigido pelo atualizador.

## Espaço e glossário

Em **Mais → Dados e armazenamento → Armazenamento do Polaris**, confira originais baixados, cópias importadas, traduções, cache, dados internos/modelos e APKs. A medição é aproximada e abrange os arquivos do app; o original do celular mantido fora do Polaris também continua consumindo espaço.

A tradução dos quadrinhos guarda texto e coordenadas em JSON, sem duplicar todas as imagens. Sua proporção depende da quantidade de texto e dos dados geométricos. Modelos ML Kit ocupam espaço à parte; a documentação do Google descreve cerca de 30 MB por idioma, compartilhados entre capítulos. Os arquivos instalados e o custo de armazenamento do Android também contam.

O cache regenerável de documentos tem **meta de 256 MiB**, descartando primeiro os arquivos menos recentes. Arquivos em uso são protegidos e podem exceder a meta temporariamente. A meta não é um limite total do app: originais, modelos e outros caches ficam fora dela.

**Limpar cache regenerável de documentos** preserva importados, downloads, traduções salvas dos capítulos, modelos e glossário. Páginas de PDF podem ser renderizadas novamente e texto de livros pode precisar de nova tradução.

Excluir um capítulo baixado também remove seu JSON de tradução e as frases de tradução automática associadas. Glossário, nomes protegidos e correções aprendidas permanecem. Frases iguais usadas em outro capítulo podem sair desse cache compartilhado e ser recalculadas. Rebaixar o capítulo segue a configuração automática da obra; isso não ativa tradução em obras que você desativou. Limpar dados/desinstalar o app é diferente de limpar cache e pode remover o vocabulário.

O glossário por obra já fica no menu da obra. A tradução textual de documentos agora também o consulta. Evite cadastrar termos muito curtos e ambíguos: em chinês, japonês e coreano, a proteção também precisa encontrar palavras sem espaços ou com partículas anexadas.

## Testes dos quatro participantes

No pacote, os exemplos estão em **testes/documentos/** e **testes/idiomas/**. São textos e páginas originais preparados para o teste.

1. Confira a tela **Sobre** e as opções de atualização: experimental desligado por padrão, consulta manual, tratamento da falta de rede e manutenção da versão ao desligar o beta. Consulta/download/instalação reais dependem de Releases acessíveis e da mesma assinatura; ainda estão pendentes. Em instalação limpa, confira espera sem rede, preparação automática, **Preparar agora**, opção de desativar e retomada após reiniciar. Após **Pronto**, teste inglês → português offline. O estado precisa refletir recursos reais, inclusive após remover modelos. A preparação não deve alterar seus idiomas escolhidos. Cada participante registra aparelho, Android, ABI do APK e revisão. Abra um livro, ajuste a fonte, leia, feche e retome. Confira imagem, categorias e importação seletiva.
2. Com o mesmo capítulo: meça armazenamento antes do download, depois do download, depois da tradução, depois da exclusão e depois de baixar/traduzir novamente. O glossário precisa permanecer. Faça também uma exclusão enquanto há tradução na fila para conferir cancelamento e limpeza.
3. Confira a tradução no paginado e na faixa longa, incluindo zoom e **Cortar bordas**. A correção automática de alinhamento ainda exige esta conferência visual.
4. Nos exemplos CBZ locais, escolha manualmente a entrada correta: EN, JA, ZH ou KO. Teste chinês simplificado e tradicional e o trecho japonês vertical. Confira OCR antes de julgar a tradução. Cadastre o nome de cada exemplo como protegido, conforme **manifest.json** dos exemplos, e confira a consistência após excluir/rebaixar o capítulo.
5. Depois das páginas simples, teste uma página real autorizada de cada idioma, com balões, fonte estilizada, baixa resolução e leitura vertical quando aplicável. Um teste de texto, ou uma página sintética, não valida qualidade geral. A revisão por falantes desses idiomas também está pendente.

As variantes estrangeiras ainda não têm aceite de qualidade. O bom resultado em inglês não deve ser usado para marcá-las como aprovadas. PDF, EPUB, DOCX/TXT, seletor, armazenamento e instalação também precisam de evidência nos aparelhos físicos. O beta mantém as limitações de layout refluído de DOCX/EPUB.

Para relatar problemas, informe revisão, aparelho/Android, ação, resultado esperado e resultado observado. Use os exemplos originais quando possível. Não há envio automático destes relatórios, das bibliotecas ou das chaves de API pelo pacote de beta.


## Revisão interna de tradução em faixa longa

Este candidato não foi publicado como Release. A edição das traduções começa desativada; habilite-a em Tradução → Avançado somente para corrigir ou retraduzir blocos. A revisão inclui coleta local de original, tradução e registro salvo pelo CMD (opções 12–14), além de validação mais rigorosa das respostas opcionais do Gemini. O padrão continua sendo o ML Kit offline. As falhas de linhas ausentes ainda dependem da reprodução com um capítulo real; não foram declaradas corrigidas. Siga o [procedimento de comparação](../../docs/REVISAO_TRADUCAO_FAIXA_LONGA.md).


## Foco desta rodada: OCR e ML Kit

Gemini não participa desta rodada; nenhuma API é necessária. O filtro preserva caracteres isolados e falas curtas com letras grandes dentro de balões detectados. O experimento **OCR por faixas em páginas longas**, em Tradução → OCR, é opcional, começa desligado e funciona com ML Kit ou PaddleOCR em inglês, sem outro modelo. Requer nova execução da tradução do capítulo para refazer o OCR.

O emulador Polaris agora abre com Full HD automático pelas opções 9/10; a 13 é opcional. O [arquivo de controle sintético](long-strip-fixture/Polaris-faixa-longa-controle.cbz) e [a transcrição esperada](long-strip-fixture/expected.json) ajudam a conferir falas de um caractere e parágrafos nas bordas das faixas. O [benchmark controlado](../ocr-benchmark/20261102/report/RESULTADOS.md) já reconheceu esse controle pela API ML Kit em Android 8 e pelo Paddle em CPU/Linux: as faixas recuperaram as 38 linhas. Isso não representa aprovação em capítulos reais nem desempenho medido em ARM. A integração no leitor é avaliada separadamente. Veja [a pesquisa com fontes e limites](../../docs/PESQUISA_OCR_MLKIT_2026_11_02.md).


## Compatibilidade e benchmark

A distribuição inclui **ARM32/ARMv7 e ARM64, Android 8+**; o A12 é somente um dos aparelhos possíveis de teste. A meta é compatibilidade ampla entre marcas, versões do Android e capacidades. A aprovação física de cada categoria ainda está pendente. O [protocolo de benchmark](../../docs/BENCHMARK_OCR_ARM32_ARM64.md) separa OCR de tradução, o Paddle existente do Tiny pesquisado e a avaliação do motor da avaliação do processamento completo. Para o primeiro teste, use apenas ML Kit padrão no trecho que apresentou o defeito.


## Beta.7: faixas com os dois motores

A opção **Tradução → OCR → OCR por faixas em páginas longas (experimental)** agora funciona com **ML Kit e PaddleOCR**, em inglês. Ela continua desligada inicialmente. A chave de configuração foi preservada: quem já havia ativado o experimento na beta.6 mantém a escolha.

O decodificador compartilhado processa uma faixa por vez, sem carregar deliberadamente o bitmap de altura completa nesse caminho. Cada faixa tem até 2.097.152 pixels (8 MiB de pixels ARGB), até 2.048 px de altura, com sobreposição adaptada à largura. Isso **não** limita a RAM total: modelos, buffers nativos e a imagem comprimida do decodificador também consomem memória. Não há novo modelo ou API. O Tiny não foi integrado.

O modo atende JPEG/PNG/WebP altos, largura até 4.096 px e até 256 faixas. Páginas comuns ou com orientação EXIF rotacionada continuam no caminho existente. A detecção experimental DBNet impede combinar as duas experiências. Há testes do reconciliador Kotlin com saídas reais do benchmark para preservar as 38 linhas sem repetição. A leitura visual, a tradução e a medição em aparelhos físicos continuam pendentes.

Para comparar, use o **mesmo original**, inglês → português e o mesmo glossário. Registre ML Kit normal/faixas e Paddle normal/faixas, retraduzindo o capítulo a cada mudança: alterar o motor não refaz automaticamente o OCR já salvo. Letras perdidas, palavras repetidas e alinhamento devem ser avaliados separadamente da qualidade da tradução.


Para garantir uma nova leitura da imagem após mudar motor ou faixas, use a ação de remover somente a tradução salva do capítulo e depois traduza o capítulo novamente. O arquivo original baixado permanece. Retraduzir uma única frase no editor usa o texto OCR já salvo e não serve para comparar motores.

## Beta.9: leitura e download recuperável

O candidato limita legendas ao fundo medido e separa áreas de escrita sobrepostas. Faixas e DBNet passam a ser escolhas exclusivas; configurações antigas com ambos ligados conservam faixas e o OCR selecionado. A opção AOT-GAN foi retirada porque sua preferência não era usada pelo processamento. Texto ausente e balões conectados ainda exigem comparação com o original; estas correções não garantem qualidade de scan.

As opções por faixas e DBNet ficam indisponíveis quando não há entrada em inglês nem idioma automático pela fonte. DBNet também fica desativado em Android ARM32 e em outras arquiteturas que não sejam ARM64. Ao remover o requisito, o dependente é desligado; restaurar o requisito permite escolhê-lo novamente, sem ligá-lo sozinho.

Para a comparação atual em inglês: **OCR PaddleOCR**, **OCR por faixas ligado**, **DBNet desligado**, **tradutor ML Kit no dispositivo**, saída **Português (Brasil)**, efeitos sonoros e edição avançada desligados. Depois compare o **OCR ML Kit** com as demais escolhas iguais. O tradutor permanece ML Kit nos dois testes. Remova somente a tradução salva antes de refazer o OCR. As faixas só atuam quando a imagem individual é suficientemente alta; um leitor vertical pode empilhar várias imagens pequenas.

O download da atualização continua ao sair da tela. Quedas de rede têm novas tentativas automáticas e retomada do parcial quando o servidor permite, com verificação do APK completo antes de instalar. Ao terminar, a tela e a notificação oferecem abrir o instalador do Android. Cada versão continua baixando um APK completo; a retomada evita repetir a parte já recebida do mesmo arquivo.

Essa correção exige instalar a beta.9 uma vez: não modifica o atualizador da beta.8 já instalada. A distribuição deste candidato ainda está pendente. Veja [comportamento, diagnóstico e limites](../../docs/CORRECOES_LEITURA_ATUALIZACAO_P20261104_1.md).

O [ensaio real do capítulo 40](../ocr-benchmark/20261104-chapter40/README.md) compara11 recortes difíceis. Paddle teve 9 textos exatos e2 erros de caracteres; ML Kit 7 e 10, em 465 caracteres. Os controles brancos passaram nos dois. O benchmark não mede desempenho ARM nem valida tradução editorial do capítulo inteiro.

## Cedilha, fonte e encaixe em português

A Anime Ace incluída não tinha Ç/ç; o candidato complementa essas letras com a Bubble Sans já disponível, com altura compatível. A medição usa o mesmo texto estilizado do desenho, o espaço entre linhas considera os acentos, e a busca compara os espaços seguros para evitar reduzir a letra antes do necessário. Os arquivos das fontes permanecem intactos.

**Fonte das traduções** aplica a família escolhida ao texto traduzido; tamanho e quebras são automáticos para cada região. Não há identificação automática da fonte original. Reabra o leitor para conferir traduções salvas com a correção; não é necessário refazer o OCR somente por causa da fonte. Veja [diagnóstico e limites](../../docs/TIPOGRAFIA_PT_P20261104_2.md).

## Rascunho beta.9 no GitHub

O [rascunho de Release beta.9](https://github.com/Hailton-Reis/Polaris/releases/tag/untagged-e498da151b0296209fe2) contém os APKs ARM32/ARM64 e cinco anexos de metadados, roteiro, notas e validação, com tamanhos e hashes remotos conferidos. Continua sem publicação; não aparece no atualizador nem oferece download anônimo. A beta.8 permanece como prévia pública. Veja [o registro de preparação e as pendências de CI](../release-candidates/0.1.0-beta.9/README.md).
