# Revisão interna: leitura e tradução em faixa longa

Esta revisão permanece em desenvolvimento. Não há nova Release publicada. O caso relatado é manhwa em faixa longa: frases incompletas e texto fora de balões que não aparece traduzido. Ainda precisamos capturar um exemplo real para identificar e validar a correção.

## Leitura sem ferramentas de edição sobrepostas

Em **Configurações → Tradução → Avançado**, a opção **Edição avançada das traduções** começa desligada, inclusive em instalações anteriores que ainda não têm essa preferência. Nesse estado, os blocos traduzidos não recebem o gesto de edição; os gestos normais de leitura continuam disponíveis.

Ative a opção para corrigir ou retraduzir um bloco individual e para adicionar uma tradução manual pelo menu da página. Ao desligar, qualquer editor de bloco aberto é fechado. Esse controle não altera traduções ou correções já salvas.

## Prioridade atual: ML Kit e OCR offline

Gemini fica fora da rodada de testes por decisão do usuário. Não é necessário configurar conta, chave de API ou serviço online para testar estas melhorias. O provedor opcional existente permanece disponível para uso futuro; não foi feito novo trabalho de integração com ele nesta rodada.

## ML Kit e Gemini (referência opcional)

O padrão é o ML Kit do Google: reconhecimento e tradução no aparelho, com o download inicial dos recursos de idioma. Não é o Gemini. Nenhum modelo generativo grande foi adicionado ao APK nesta revisão.

O caminho opcional do Gemini já existia. Foi revisado para usar lotes de até 16 frases e aproximadamente 6.000 caracteres, exigir todas as frases na resposta e rejeitar respostas interrompidas. Um texto isolado maior que esse orçamento ocupa seu próprio lote. A tradução Gemini não reutiliza o cache de frases de máquina compartilhado com o tradutor offline. O arquivo de tradução do capítulo continua disponível para leitura offline depois de salvo.

Para experimentar:

1. Nas configurações de Tradução, selecione **Gemini** e informe sua chave da Gemini API no próprio aplicativo. Não inclua a chave em capturas, ZIPs ou mensagens.
2. Confira o identificador do modelo. Para configurações novas, o padrão é `gemini-3.5-flash-lite`, listado na [documentação oficial de modelos](https://ai.google.dev/gemini-api/docs/models), consultada em 02/11/2026. Uma escolha antiga salva pelo usuário é preservada; revise-a se o modelo tiver sido descontinuado.
3. Use a ação de retradução para testar um bloco ou capítulo já traduzido. Apenas trocar o provedor não substitui o arquivo de tradução que já está salvo. Para corrigir um bloco, ative primeiro a edição avançada.
4. Compare o mesmo trecho com o ML Kit. O Gemini depende de conexão, disponibilidade e limites da conta; pode haver cobrança do provedor.

Nesta implementação, o Gemini recebe **texto do OCR**, não a imagem da página. Pode melhorar a formulação e o contexto da tradução, mas não recupera uma linha que não chegou ao OCR ou foi descartada antes da tradução. Não houve teste de API real nesta revisão por ausência de uma chave configurada para o teste. Não foram utilizadas chaves de outros projetos.

## Coleta no PC pelo CMD atualizado

Estas opções atuam somente no AVD Polaris criado pelo próprio assistente. Não selecionam o A12, outros celulares ou o AVD de comparação Yomotsu. Preserve o CMD antigo se desejar; baixe a cópia atualizada para obter os novos menus.

1. Execute **4 — Compilar** para gerar o build de diagnóstico atualizado. Depois use **9 — Emular Polaris** para instalar esse build no emulador existente. Não use Wipe Data.
2. As opções **9** e **10** já preparam o Polaris em **1080 × 1920 e 420 dpi** automaticamente, antes de abrir o aplicativo. Na partida de um AVD fechado, o tamanho da tela é selecionado no comando de inicialização; se o AVD já estiver aberto, o ajuste é aplicado à instância existente. A opção **13** fica apenas para reaplicar manualmente. A **14** restaura os overrides de tamanho/densidade salvos; uma nova abertura pelo CMD volta a preparar Full HD. O AVD original Yomotsu permanece com sua configuração. Aumentar a resolução não aumenta o detalhe de uma imagem original pequena; maximizar a janela do Android Studio também ajuda a ler.
3. Abra o mesmo capítulo em **faixa longa**, traduza normalmente e posicione a leitura um pouco antes do defeito. Espere a página terminar de carregar. O coletor não busca capítulos, não inicia OCR e não chama o Gemini.
4. Escolha **12 — Comparar tradução**. Não toque no leitor durante a coleta. Ele alterna a exibição da tradução, captura as duas telas e avança com sobreposição. O limite padrão é de 60 posições e 512 MiB por coleta. A posição de leitura avança; a visibilidade original das traduções é restaurada ao terminar ou falhar.
5. Abra o relatório local `PolarisDev/relatorios/traducao-.../comparacao.html`. Ao terminar, informe o número do quadro com defeito para gerar um ZIP desse caso. Os arquivos ficam no PC e não são enviados automaticamente. Você pode compartilhar somente esse ZIP para análise.

O relatório diferencia fim do leitor, mudança de capítulo, limite atingido e erro. A coleta começa na posição atual, portanto não certifica que o capítulo inteiro foi examinado. Uma coleta concluída também não representa aprovação da qualidade da tradução.

Para alterar o limite sem o menu, no terminal do checkout de engenharia:

```powershell
python tools/local-android/polaris_translation_capture.py capture --workspace "$env:USERPROFILE/PolarisDev" --consent --interactive --max-frames 120
```

## Como distinguir os defeitos

Cada quadro contém as telas original/traduzida, o original integral da página ativa e `record.json`, com os textos, traduções e coordenadas já salvos. Uma tela pode mostrar também partes das páginas vizinhas; o original exportado é o da página ativa.

| Evidência | Próxima investigação |
| --- | --- |
| A linha aparece na imagem, mas falta no texto salvo | OCR ou filtragem anterior ao salvamento; será necessário repetir o reconhecimento do original |
| O texto está salvo, mas a tradução está vazia | Elegibilidade de posicionamento, filtros ou tradução |
| A tradução salva está completa, mas a última linha não aparece na tela | Encaixe, tamanho de fonte e recorte da camada visual |
| Original e tradução estão completos, mas a frase está ruim | Qualidade do provedor, contexto, glossário ou correção manual |

O registro contém o OCR **depois dos filtros existentes**, não o resultado bruto de uma nova execução. A preferência de provedor exportada é a configuração atual e não comprova qual provedor produziu uma tradução antiga. O diagnóstico não exporta chaves, preferências completas ou logs gerais do aparelho. As cópias temporárias no cache do aplicativo são removidas após cada transferência; os originais e relatórios do PC permanecem até você os excluir.

Japonês, chinês e coreano ainda precisam de casos reais. Esta revisão não declara resolvidas as falhas de captura nem equivalência com tradução humana de uma scan.


## Melhorias de OCR — P20261102.3

O filtro inicial passa a preservar textos de um único caractere, incluindo falas curtas e caracteres CJK. Letras grandes dentro de um balão detectado não são removidas apenas pelo tamanho como se fossem onomatopeias. O filtro existente para efeitos fora dos balões permanece. Isso não significa que todos os textos fora de balões já possam receber sobreposição automática: o posicionamento ainda exige evidência de fundo seguro.

Em **Tradução → OCR**, a opção **OCR por faixas em páginas longas (experimental)** começa desligada. Usa o mesmo ML Kit em inglês, sem baixar outro modelo. Nas páginas JPEG/PNG/WebP altas e com orientação EXIF normal, lê faixas sobrepostas sequencialmente, preservando os pixels e as coordenadas da página; reconcilia repetições apenas onde a geometria se sobrepõe. Cada faixa tem até 2.097.152 pixels ARGB, cerca de 8 MiB de pixels; esse valor não representa a memória total do aplicativo, do decodificador ou do ML Kit.

O experimento não atua com DBNet habilitado, nem altera o caminho atual para japonês, chinês e coreano. Páginas normais, formatos não suportados e imagens rotacionadas continuam no caminho anterior. Há limite de 256 faixas. Para comparar, use o mesmo capítulo sem o experimento e depois com ele; remova apenas a tradução salva pelo menu de tradução do capítulo e traduza novamente, mantendo o original baixado. Retraduzir só uma frase não executa novamente o OCR. Não exclua dados do aplicativo ou o capítulo original.

Os testes unitários verificam cobertura, sobreposição, orçamento de pixels e reconciliação das faixas; não medem a precisão do modelo Android. O capítulo real com defeito continua necessário. Consulte a [pesquisa e as decisões técnicas](PESQUISA_OCR_MLKIT_2026_11_02.md).
