# Revisão interna: leitura e tradução em faixa longa

Esta revisão permanece em desenvolvimento. Não há nova Release publicada. O caso relatado é manhwa em faixa longa: frases incompletas e texto fora de balões que não aparece traduzido. Ainda precisamos capturar um exemplo real para identificar e validar a correção.

## Leitura sem ferramentas de edição sobrepostas

Em **Configurações → Tradução → Avançado**, a opção **Edição avançada das traduções** começa desligada, inclusive em instalações anteriores que ainda não têm essa preferência. Nesse estado, os blocos traduzidos não recebem o gesto de edição; os gestos normais de leitura continuam disponíveis.

Ative a opção para corrigir ou retraduzir um bloco individual e para adicionar uma tradução manual pelo menu da página. Ao desligar, qualquer editor de bloco aberto é fechado. Esse controle não altera traduções ou correções já salvas.

## ML Kit e Gemini

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
2. Com o emulador aberto, escolha **13 — Tela FHD** para aplicar 1080 × 1920 e 420 dpi. A opção **14** restaura os valores anteriores, inclusive eventuais ajustes que você já tinha feito. Aumentar a resolução não aumenta o detalhe de uma imagem original pequena; maximizar ou ampliar a janela do Android Studio também pode ajudar a ler.
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
