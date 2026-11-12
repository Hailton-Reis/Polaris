# Revisão da biblioteca — P20261110.2

Revisão posterior à P20261110.1, na beta.11/código 112 em desenvolvimento. A beta.10 pública, main e os APKs publicados continuam intactos.

## Achados e correções

| Achado confirmado | Efeito e correção |
| --- | --- |
| A associação formada validava metadados, mas não consultava novamente a numeração | A lista, o fluxo de capítulos, a projeção da biblioteca, as ações por obra e a escolha da raiz do leitor conferem os capítulos nativos atuais. Se ficarem incompatíveis, as entradas reaparecem separadas. A associação é conservada e pode voltar a funcionar quando as sequências forem compatíveis. |
| O plano podia ficar obsoleto entre a leitura dos capítulos e a gravação do vínculo | A transação de associação confere a numeração real antes de gravar os memos, mesmo se a quantidade de linhas e os metadados da obra não mudarem. |
| Números consecutivos podiam passar pela comparação apesar de pertencerem a temporadas, volumes ou partes diferentes | A comparação de faixas adjacentes exige os mesmos valores de temporada, volume e parte. Também exige identidade de catálogo suportada e corroborada; um ID de catálogo não suportado ou malformado não autoriza complementar faixas separadas. |
| Permitir novamente ou separar uma associação podia ignorar a entrada principal fora dos favoritos | A operação inclui explicitamente a entrada solicitada. Não adiciona a obra aos favoritos, conserva notas/glossário e permite que a escolha tenha efeito quando a pessoa a adicionar novamente. |
| A montagem dos capítulos decodificava os mesmos memos da obra para cada capítulo | Esses dados são preparados uma vez por edição. As chaves de numeração também são preparadas uma vez por edição para comparar o grupo; capítulos sem origem adicional evitam provocar uma exceção para descobrir que esse campo não existe. |

A regra de numeração agora é compartilhada entre descoberta, confirmação no banco e leitura. Isso evita que cada caminho use um critério diferente. A prova com duas edições de 10 mil capítulos verifica os 20 mil IDs e seus donos de armazenamento, além dos 10 mil capítulos lógicos; não constitui benchmark em ARM.

## Preservação e filtros

Nenhum registro nativo é transferido ou excluído pela revalidação. As posições parciais continuam na edição original. Durante uma incompatibilidade, o Polaris mantém os favoritos e seus dados, preservando a opção de separar manualmente.

A compatibilidade é verificada com os capítulos completos de cada edição, antes do filtro de scanlators. Ocultar um grupo de tradução da lista não muda a identidade da numeração. O fluxo reage a alterações das linhas de capítulos mesmo quando os metadados da obra e a quantidade de linhas continuam iguais.

Backups mantêm os campos e vínculos portáveis da revisão anterior. Não há alteração no esquema SQL, formato obrigatório de backup, bibliotecas ou modelos OCR.

## Validação e limites

[Resultados e evidências desta revisão](../integration/library-review/20261110/README.md).

A numeração continua sendo uma heurística baseada nos metadados disponíveis. A conferência não deduz equivalência entre páginas nem identifica toda renumeração semanticamente incorreta quando os rótulos ainda parecem compatíveis. O trecho já carregado no leitor não é uma migração em tempo real. Faltam o fluxo completo com backup pessoal e provedores reais, aceite da interface, ida/volta em leitores externos e desempenho em A12/ARM32 e S20 FE/ARM64.

O caminho sem filtro reaproveita as listas nativas que já seriam carregadas pela consulta. O caminho com filtro precisa conferir as listas completas e buscar as linhas visíveis; seu custo real deve ser medido. A redução de trabalho repetido no código não certifica fluidez em aparelhos modestos.
