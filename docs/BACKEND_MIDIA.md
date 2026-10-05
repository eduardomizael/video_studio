# Segundo incremento: reprodução e inspeção de mídia

Data: 04/10/2026. Implementado sobre o catálogo real, sem upload/conversão de vídeo e sem ampliar o escopo para mídias externas.

## Entregue

- Player HTML5 real no editor, com controles nativos de reprodução, volume, posição e tela cheia. Erros de arquivo/codec são apresentados sem impedir edição dos metadados.
- `GET/HEAD /videos/<id>/midia/`: autenticação, resolução segura da raiz ativa e leitura local. Intervalos únicos `bytes=início-fim`, abertos e por sufixo recebem 206; intervalos inválidos recebem 416. `If-Range`, ETag e Last-Modified permitem conferir o arquivo. A entrega usa blocos de até 64 KiB para intervalos, sem ler todo o vídeo na memória no fluxo WSGI.
- `GET/HEAD /videos/<id>/miniatura/`: imagem autenticada, gerada em cache privado ou indicada manualmente sob a mesma raiz local. Não existe uma URL pública da árvore de mídia.
- `POST /videos/<id>/inspecionar/`: reinspeção autenticada com CSRF, usada também para referências antigas e arquivos alterados no mesmo caminho.
- FFprobe extrai duração em milissegundos, codec e dimensões; o sistema registra tamanho, data e estado da inspeção. FFmpeg gera um frame JPG de até 640 pixels de largura, mantendo proporção.
- A inspeção usa argumentos estruturados, sem shell, timeout de 10 segundos por processo e entradas limitadas a formatos de vídeo locais. Protocolos de rede e playlists não fazem parte da extração.
- A falta das ferramentas, erro do arquivo ou timeout não impede o cadastro/edição. Mensagens não expõem caminhos absolutos ou stderr da ferramenta.
- Duração manual tem prioridade sobre reinspeções. Limpar o campo habilita novamente a extração. Miniatura manual aceita JPG/PNG/WebP/GIF já existentes no mesmo local; SVG e referências externas não são aceitos.
- Trocar a referência invalida os dados técnicos e a miniatura extraída anteriores; uma duração manual diferente explicitamente informada pode ser aplicada à nova referência.
- Biblioteca e inspetor mostram miniaturas reais. A disponibilidade no editor é verificada ao abrir, sem apagar registros quando o arquivo desaparecer.

## Arquivos e configurações

Implementação: `app/catalog/media.py`, `inspection.py`, serviços e migração `0002`; componente `real_media_panel.html` e tratamento de erro em `static/js/media-player.js`.

`FFPROBE_BINARY` e `FFMPEG_BINARY` podem ser definidos no ambiente como nome no PATH ou caminho completo. O cache padrão é `private_media/`, excluído do Git e separado dos estáticos. O servidor precisa poder ler as raízes configuradas e escrever nesse cache.

As inspeções são síncronas e executadas antes da transação de gravação do catálogo. Uma inspeção pode consumir até dois timeouts sucessivos. Não existe fila de processamento ou monitoramento contínuo. Cache antigo não é removido automaticamente; uma política de limpeza pode ser acrescentada sem apagar os vídeos originais.

## Verificação realizada

- Suíte: 46 testes executados; 45 aprovados e 1 ignorado pela restrição Windows de criação de link simbólico real já registrada no primeiro incremento.
- Testes cobrem corpo completo e HEAD, intervalos fechados/abertos/sufixos, limites, arquivo vazio, 416, If-Range, login, locais inativos, referência adulterada, bloqueio de conteúdo HTML inline, miniaturas privadas/manual, inspeção, falhas/timeouts, preservação manual e invalidação por troca de caminho.
- `manage.py check` sem problemas; migrações sem alterações pendentes; sintaxe dos dois scripts JavaScript válida e CSS compilado.
- FFmpeg/FFprobe detectados no computador. Gerado vídeo sintético WebM com VP8/Opus para teste, sem uso de arquivos privados do acervo.
- Inspeção real: 3008 ms, 320 × 180, codec VP8; miniatura JPG gerada e decodificada no navegador em 640 × 360.
- Browser: vídeo carregado com `readyState=4`, reprodução avançando, seek por controle nativo e nenhum erro de mídia. Duração manual alterada, salva e preservada após reinspeção; retorno à extração após limpar o campo.
- Biblioteca/inspetor: imagens reais carregadas após filtragem HTMX. Nenhum erro JavaScript observado. Captura: `artifacts/player-real.png`, em banco temporário separado do catálogo.
- Migração aplicada ao SQLite local. Não houve criação de usuário administrativo ou configuração de pastas privadas no banco da aplicação.

## Limites e próxima entrega

O navegador determina quais codecs consegue reproduzir; o teste realizado confirma WebM/VP8 no browser usado, sem declarar todos os formatos compatíveis. A entrega parcial foi verificada no servidor local Django; desempenho/seek no servidor de produção ainda precisam ser validados com sua configuração WSGI/proxy. Não foi implementada entrega ASGI específica nem delegação ao proxy.

No encerramento deste incremento, capítulos, marcações por pessoa/tempo, versões SRT e legendas sincronizadas estavam pendentes. O incremento posterior de marcações foi implementado e verificado em [BACKEND_MARCACOES.md](BACKEND_MARCACOES.md), usando o `currentTime` real do player. SRT, preferências, notificações e integrações externas continuam pendentes.
