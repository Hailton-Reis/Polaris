# Privacidade e serviços usados

O Polaris é uma adaptação de Yomotsu / Mihon em desenvolvimento. Esta página descreve os principais fluxos desta implementação; não substitui as políticas dos serviços escolhidos nem representa uma auditoria completa de todos os componentes herdados.

## Leitura e tradução

Arquivos locais escolhidos são copiados para o armazenamento gerenciado do app. Biblioteca, posição de leitura, traduções salvas e vocabulário usam armazenamento local. A inclusão seletiva não faz uma varredura geral de todos os documentos do celular.

O ML Kit reconhece texto e traduz no aparelho com os recursos necessários disponíveis. A preparação de modelos usa serviços do Google e precisa de rede inicialmente. Consulte também os [termos e informações do ML Kit](https://developers.google.com/ml-kit/terms).

Se você escolher um provedor de tradução por API, o texto enviado para tradução é transmitido ao serviço configurado. As condições de uso, retenção e cobrança desse provedor se aplicam. Chaves pessoais e textos sensíveis não devem ser incluídos em relatos públicos.

## Conexões solicitadas pelos recursos

- Fontes e extensões: seus servidores recebem as requisições de pesquisa, leitura e download necessárias ao uso.
- Pesquisa de documentos: termos consultados são enviados aos provedores selecionados, como Crossref, Europe PMC, Gutendex e Open Library. Sites de pesquisa e links abertos seguem seus próprios serviços.
- Atualizações do aplicativo: a consulta usa a API e os arquivos do GitHub. Isso transmite os dados usuais de uma conexão de rede, como endereço IP e informações da requisição. A busca automática pode ser desligada em **Atualizações do aplicativo**.
- Integrações opcionais, como rastreadores e sincronização: dependem da configuração e das permissões concedidas a cada serviço.

Credenciais do ambiente de desenvolvimento não são inseridas no APK. O pacote de teste não envia automaticamente os relatos de problemas preparados pelos participantes. Antes de compartilhar registros, revise possíveis nomes de arquivos, endereços, textos e informações pessoais.

## Controle do armazenamento

Limpar o cache regenerável de documentos preserva os arquivos importados, modelos e vocabulário, mas pode exigir preparar páginas e texto novamente. Excluir downloads, remover modelos, limpar dados do Android e desinstalar são ações diferentes, com efeitos diferentes. Consulte a [análise de armazenamento](ARMAZENAMENTO.md).

## Base e contato

A base mantém componentes e integrações de terceiros. A [política da base Yomotsu](https://yomotsu-app.github.io/privacy.html) é uma referência adicional; ela não descreve, sozinha, todas as alterações do Polaris.

Para relatar uma questão ao mantenedor, use o [repositório do Polaris](https://github.com/Hailton-Reis/Polaris/issues). Evite anexar documentos pessoais, chaves de API ou registros sem revisão.
