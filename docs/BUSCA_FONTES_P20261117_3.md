# Busca entre fontes — P20261117.3

17/11/2026, America/Fortaleza. Desenvolvimento para a próxima versão; sem novo APK ou Release. A beta.11 instalada permanece P20261116.1/código 112.

## Comportamento observado no código

A tela atualiza primeiro a fonte original e pode iniciar uma descoberta complementar em `viewModelScope.launchIO`. Assim, a lista pode crescer depois da primeira atualização. Isso é compatível com uma obra inicialmente mostrar poucos capítulos, mas não identifica a causa de um caso específico sem registros do aparelho. A operação está associada à tela; não é uma busca persistente independente do processo do app.

A descoberta já consultava duas fontes por vez. Entretanto, atualizações de alternativas confirmadas eram sequenciais; a checagem de páginas/imagens ficava no coletor serial; um mutex reservava a descoberta inteira de uma obra antes de permitir outra. A busca também repetia consultas em fontes cujo catálogo já tinha sido atualizado. Quando o orçamento de descoberta acabava, a tentativa parcial recebia o mesmo cache de 24 horas de uma tentativa completa.

## Mudança

- Catálogos confirmados passam a ser atualizados em pares. Busca, catálogo e checagem de imagens de uma alternativa compartilham uma vaga; a coleta apenas aplica os resultados, sem aguardar imagens.
- Um semáforo compartilhado permite até **duas operações de fontes alternativas deste serviço**, entre obras diferentes. A vaga é devolvida por operação, em vez de uma obra reservar a fila até terminar. A fonte original continua fora desse semáforo. Não é um limite global de todas as requisições HTTP do app: uma extensão pode fazer várias requisições dentro da própria operação.
- A fila de catálogos prontos fica limitada a dois resultados, evitando produção antecipada de dezenas de catálogos enquanto o coletor os compara. Isso não estabelece um teto de RAM para a obra ou seus capítulos.
- Catálogos confirmados, atuais e sem falha de amostra são reutilizados, sem outra pesquisa na mesma fonte. Um URL já tentado também é reconhecido antes de repetir a consulta de detalhes.
- Reutilizar uma checagem de imagem preserva a data em que ela realmente ocorreu. As tentativas mais frequentes não renovam indefinidamente uma amostra antiga; ao expirar, ela volta a ser conferida.
- Tentativas interrompidas pelos limites de tempo são marcadas como incompletas. Após um minuto do término, ficam elegíveis para nova tentativa; buscas concluídas conservam o cache normal de 24 horas. Não foi criado temporizador: a tentativa acontece quando o app volta a solicitá-la. Instalação de fontes, invalidação explícita e outras condições existentes continuam podendo antecipar a descoberta.
- Timeout na atualização de um catálogo já confirmado também mantém essa possibilidade de nova tentativa, mesmo quando a atualização comum não está autorizada a pesquisar fontes novas. Ela continua sem disparar pesquisas extras naquele momento.
- O painel de fontes avisa quando a busca fica incompleta e mantém o botão de busca existente. A mensagem aparece somente no modo automático, sem mudar a fonte fixada.

O campo opcional `discoveryIncomplete`, com padrão falso, fica no memo existente `polaris.work.sources.v1`. Dados antigos continuam legíveis; não há migração SQL, mudança Protobuf ou novo formato de backup. Não é possível identificar retroativamente quais caches antigos vieram de uma tentativa incompleta.

Somente o coletor altera as listas de catálogos e vínculos; os trabalhadores devolvem resultados separados. O bloqueio por obra e a releitura do registro dentro dele, em `UpdateMangaFromRemote`, permanecem. Os critérios de título/autoria/identidade, numeração compatível, preferência de idioma, fonte fixa, fontes desabilitadas, limite de capítulos e retenção das origens existentes não foram relaxados.

## Limites de tempo

Permanecem 30 segundos para carregar um catálogo e 30 segundos para pesquisa/detalhes/catálogo de uma fonte descoberta. A operação alternativa inteira tem orçamento de 60 segundos incluindo espera por vaga e checagem; a fase de descoberta tem orçamento de 60 segundos incluindo essa fila. Carregamento original, identificação e atualização dos vínculos confirmados acontecem antes dessa fase: não é uma promessa de 60 segundos para toda a atualização da tela.

Os limites dependem de cancelamento cooperativo. Chamadas bloqueantes de uma extensão podem demorar a responder. Resultados já coletados são preservados quando termina o orçamento; cancelamento do chamador continua sendo cancelamento e não é convertido em sucesso parcial. Essa revisão não publica cada catálogo separadamente no banco enquanto os demais ainda estão sendo pesquisados.

## Validação

Quatro regressões foram reproduzidas no código anterior inalterado, sem parâmetro de teste ou implementação alternativa. Os testes usam o catálogo, associação, ordenação, retenção e memo reais com provedores simulados e `kotlinx.coroutines.test`; não fazem consultas a fontes reais.

| Cenário controlado | Antes | Depois |
| --- | ---: | ---: |
| Três alternativas com atraso de 1 segundo cada | 3 segundos virtuais | 2 segundos virtuais |
| Quatro checagens de imagem de 1 segundo | 4 segundos virtuais | 2 segundos virtuais; pico de duas checagens |
| Pesquisa repetida na fonte confirmada já atualizada | 1 | 0 |
| Nova elegibilidade após tentativa incompleta, envelhecida 65 segundos | Não | Sim |

São provas de sobreposição e política, **não benchmarks de rede, A12 ou ganho garantido no aparelho**. Controles adicionais verificam outra obra avançando antes de uma busca lenta terminar, cancelamento devolvendo todas as vagas, manutenção do catálogo rápido no limite de tempo, retorno ao cache diário após conclusão, timeout individual e respeito à fonte fixa. Dois testes de domain conferem memo antigo e persistência/limpeza do indicador sem perder outros campos.

Quinze casos novos: treze do app e dois de domain. A rodada focada passou; a suíte completa também inclui os controles adicionais de timeout num catálogo confirmado e validade das amostras reutilizadas/expiradas. A validação final `BUILD SUCCESSFUL` em 2min19s executou/aprovou **952 testes do app beta**, mais **87 de domain release anteriormente aprovados e UP-TO-DATE**: 1.039 relatórios sem falhas/skips ou casos anteriores ausentes contra a base de 1.024. Overlay4/empacotamento27/comparador21 aprovados. Interface e recursos compilados; sem nova instrumentação Android, fonte real ou medição de rede/RAM nesta etapa.

As [evidências filtradas](../integration/source-discovery/20261117/README.md) registram os casos e hashes. Alterações anteriores de backups, OpenCV e limpeza OCR continuam incluídas. Sandbox e conta/nuvem seguem adiadas. Antes de distribuir, aumentar versão/código acima de beta.11/112 e validar o novo pacote.
