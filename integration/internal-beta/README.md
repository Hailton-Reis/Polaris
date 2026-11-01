# Polaris 0.1.0-beta.1 — beta interno candidato

Revisão: **P20261101.1**. Android mínimo: **8.0 / API 26**. Esta é uma versão privada para experimentar e registrar problemas; a conferência nos celulares ainda está pendente.

## Instalar e atualizar

O pacote contém dois APKs. Use **arm64-v8a** primeiro nos aparelhos Android de 64 bits. Se o sistema do aparelho for de 32 bits, use **armeabi-v7a**. A12, S20 FE, S8+ e o provável A52 são a matriz inicial; o modelo comercial sozinho não confirma a arquitetura e a versão instalada do Android. O S8+ precisa estar no Android 8 ou superior.

Instale apenas um APK por aparelho. Não é necessário o APK universal nem as versões x86 do emulador. Instalações e atualizações devem vir sempre da mesma máquina/assinatura usada para esse beta. Não apague a instalação antiga para contornar um erro de assinatura: isso pode remover os dados locais. O mantenedor deve reconstruir e compartilhar o APK com a assinatura original.

O mantenedor gera o pacote com a opção **4** do CMD atualizado. Ao concluir a comparação automatizada, a pasta de evidências contém **beta/**, com APKs ARM, hashes e exemplos. A opção **9** continua sendo o fluxo local de instalação já existente. Confira **P20261101.1** em **Sobre** antes de registrar resultados. O versionCode agora é **102**; a instalação anterior usava 101.

## Uso inicial

- Para livros já baixados no celular: **Mais → Documentos e pesquisa → Explorar e adicionar arquivo**. Escolha um arquivo, seu tipo e suas categorias; só **Adicionar à biblioteca** faz a inclusão. O original continua no celular e o Polaris guarda uma cópia. Não há varredura geral dos PDFs do aparelho.
- Para quadrinhos: use as fontes/extensões escolhidas e os downloads existentes. Ative a tradução automática por obra quando quiser traduzir ao terminar o download.
- Para tradução: comece com **ML Kit**, entrada em inglês e saída em português. Os modelos de idioma precisam ser baixados no primeiro uso. Depois de instalados, ML Kit pode traduzir sem conexão; fontes e downloads ainda dependem da rede. Os provedores de API continuam opcionais e usam a configuração de cada pessoa.
- **Usar o idioma de OCR declarado pela fonte** escolhe EN/JA/ZH/KO quando a fonte informa esse idioma. Fonte mista, desconhecida e documentos locais usam a entrada escolhida manualmente. Isso não é detecção do conteúdo.
- A automação global de japonês/chinês/coreano é **opcional e desativada inicialmente**, pois sua qualidade ainda precisa de teste. A escolha explícita de tradução automática por obra tem prioridade. **PaddleOCR permanece apenas em inglês**; use ML Kit nos testes de outros idiomas.

## Espaço e glossário

Em **Mais → Dados e armazenamento → Armazenamento do Polaris**, confira originais baixados, cópias importadas, traduções, cache, dados internos/modelos e APKs. A medição é aproximada e abrange os arquivos do app; o original do celular mantido fora do Polaris também continua consumindo espaço.

A tradução dos quadrinhos guarda texto e coordenadas em JSON, sem duplicar todas as imagens. Sua proporção depende da quantidade de texto e dos dados geométricos. Modelos ML Kit ocupam espaço à parte; a documentação do Google descreve cerca de 30 MB por idioma, compartilhados entre capítulos. Os arquivos instalados e o custo de armazenamento do Android também contam.

O cache regenerável de documentos tem **meta de 256 MiB**, descartando primeiro os arquivos menos recentes. Arquivos em uso são protegidos e podem exceder a meta temporariamente. A meta não é um limite total do app: originais, modelos e outros caches ficam fora dela.

**Limpar cache regenerável de documentos** preserva importados, downloads, traduções salvas dos capítulos, modelos e glossário. Páginas de PDF podem ser renderizadas novamente e texto de livros pode precisar de nova tradução.

Excluir um capítulo baixado também remove seu JSON de tradução e as frases de tradução automática associadas. Glossário, nomes protegidos e correções aprendidas permanecem. Frases iguais usadas em outro capítulo podem sair desse cache compartilhado e ser recalculadas. Rebaixar o capítulo segue a configuração automática da obra; isso não ativa tradução em obras que você desativou. Limpar dados/desinstalar o app é diferente de limpar cache e pode remover o vocabulário.

O glossário por obra já fica no menu da obra. A tradução textual de documentos agora também o consulta. Evite cadastrar termos muito curtos e ambíguos: em chinês, japonês e coreano, a proteção também precisa encontrar palavras sem espaços ou com partículas anexadas.

## Testes dos quatro participantes

No pacote, os exemplos estão em **testes/documentos/** e **testes/idiomas/**. São textos e páginas originais preparados para o teste.

1. Cada participante registra aparelho, Android, ABI do APK e revisão. Abra um livro, ajuste a fonte, leia, feche e retome. Confira imagem, categorias e importação seletiva.
2. Com o mesmo capítulo: meça armazenamento antes do download, depois do download, depois da tradução, depois da exclusão e depois de baixar/traduzir novamente. O glossário precisa permanecer. Faça também uma exclusão enquanto há tradução na fila para conferir cancelamento e limpeza.
3. Confira a tradução no paginado e na faixa longa, incluindo zoom e **Cortar bordas**. A correção automática de alinhamento ainda exige esta conferência visual.
4. Nos exemplos CBZ locais, escolha manualmente a entrada correta: EN, JA, ZH ou KO. Teste chinês simplificado e tradicional e o trecho japonês vertical. Confira OCR antes de julgar a tradução. Cadastre o nome de cada exemplo como protegido, conforme **manifest.json** dos exemplos, e confira a consistência após excluir/rebaixar o capítulo.
5. Depois das páginas simples, teste uma página real autorizada de cada idioma, com balões, fonte estilizada, baixa resolução e leitura vertical quando aplicável. Um teste de texto, ou uma página sintética, não valida qualidade geral. A revisão por falantes desses idiomas também está pendente.

As variantes estrangeiras ainda não têm aceite de qualidade. O bom resultado em inglês não deve ser usado para marcá-las como aprovadas. PDF, EPUB, DOCX/TXT, seletor, armazenamento e instalação também precisam de evidência nos aparelhos físicos. O beta mantém as limitações de layout refluído de DOCX/EPUB.

Para relatar problemas, informe revisão, aparelho/Android, ação, resultado esperado e resultado observado. Use os exemplos originais quando possível. Não há envio automático destes relatórios, das bibliotecas ou das chaves de API pelo pacote de beta.
