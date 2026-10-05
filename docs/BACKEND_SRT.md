# Backend de versões e legendas SRT

Incremento implementado em 04/10/2026. A tela de capítulos oferece **Gerenciar legendas**, que abre `/videos/<id>/legendas/`. O editor de vídeo e a tela de capítulos carregam a versão ativa no player real.

## Importação e versões

Cada vídeo pode ter várias versões, com nome obrigatório, idioma opcional, origem SRT, autores e datas. A primeira importação fica ativa; as seguintes começam inativas. A seleção usa transação e bloqueio do vídeo, com restrição de unicidade no banco para impedir duas versões ativas. Alterar nome/idioma preserva o estado de ativação atual.

O formulário recebe apenas o arquivo de legenda: nenhum vídeo é enviado. O SRT é lido, validado e convertido em entradas; não é mantido como arquivo no armazenamento da aplicação. Limites: 2 MB, 5.000 entradas e 10.000 caracteres por texto. UTF-8 com ou sem BOM, CRLF/LF/CR, numeração não sequencial ou ausente, textos em várias linhas e intervalos sobrepostos são aceitos. Intervalos usam `HH:MM:SS,mmm` ou ponto antes dos milissegundos; blocos são separados por linha em branco.

Erros indicam a linha quando aplicável. Codificação inválida, texto vazio, minuto/segundo inválido, intervalo sem duração ou invertido e tempo além da duração conhecida são rejeitados. Nenhuma versão ou entrada é gravada parcialmente. A duração é conferida novamente na transação, para contemplar alterações após a validação do formulário.

## Edição e reprodução

Uma versão permite alterar nome/idioma, criar, editar e remover entradas. A lista é cronológica, paginada em 50 entradas; a ordem original resolve empates. A edição preserva o conteúdo digitado em caso de erro. Remoção requer confirmação GET e execução POST e preserva versão, vídeo e arquivo.

Tempos ficam em milissegundos inteiros. A edição aceita o mesmo formato de tempo das marcações. O fim precisa ser posterior ao início. Sobreposições são permitidas. Arquivo indisponível não impede editar as legendas. Reduzir a duração do vídeo abaixo de qualquer entrada de qualquer versão é bloqueado, inclusive após inspeção automática.

O player carrega apenas entradas da versão ativa, usando `json_script` e uma faixa nativa `TextTrack`/`VTTCue`. As legendas acompanham reprodução e seek e podem ser desligadas nos controles nativos. Texto é escapado e não interpreta HTML ou marcação de estilo do SRT. A troca de versão ou edição exige reabrir/recarregar um player já aberto; não há atualização em tempo real. A faixa nativa oferece apresentação em tela cheia, cuja interação específica não foi testada nesta entrega.

## Acesso e rotas

As telas exigem login. Todas as gravações usam POST e CSRF. Versão e entrada são buscadas dentro do vídeo/versão da URL, bloqueando referências cruzadas. `UI_DEMO=True` bloqueia os novos fluxos. As regras de permissões permanecem as do MVP: usuários autenticados podem editar.

Sob `/videos/<id>/legendas/`: listagem GET; `importar/` POST; `<versao>/` GET; `<versao>/ativar/` e `<versao>/salvar/` POST. Entradas usam `<versao>/entradas/nova/` POST e `<versao>/entradas/<entrada>/editar/`, `salvar/`, `confirmar-remocao/` e `remover/`, com GET somente para leitura/confirmar.

Modelos e migração estão em `app/annotations/`; parser, formulários, serviços e views ficam nos módulos `srt.py` e `subtitle_*`. Serviços atualizam o autor/data da versão e do vídeo sem modificar mídia. Não há exportação SRT, exclusão de versão, histórico completo ou tradução automática.

## Verificação

A suíte completa possui 75 testes: 74 passaram e um foi ignorado por exigir criação real de symlink no Windows. Foram cobertos parser, importação sem gravação parcial, versão ativa única, edição/remoção, validação temporal, proteção de duração, CSRF, login, relações pela URL e conteúdo seguro da faixa ativa. Django check, migrações, sintaxe JavaScript e build CSS passaram.

No navegador, em banco temporário com vídeo e SRT sintéticos: importação de duas entradas, edição de texto e apresentação da legenda revisada em aproximadamente 903 ms após seek. Nenhum erro JavaScript observado. Evidências: `artifacts/legendas-reais.png` e `artifacts/player-legendas.png`. Não foi usado o acervo do usuário nem gravados dados de QA no SQLite da aplicação.

A próxima etapa é a consolidação de qualidade e entrega prevista na fase 7 do plano, incluindo validação com acervo real e ambiente de produção. O MVP ainda não deve ser declarado validado em produção.
