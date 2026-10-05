# Validação da interface demonstrativa

Data: 04/10/2026. Ambiente local Windows, Django 5.2.17, Python 3.13.14, Tailwind 4.3.0 e HTMX 2.0.4.

## Validação automatizada

- `manage.py check`: sem problemas reportados.
- `manage.py makemigrations --check --dry-run`: sem alterações pendentes.
- `manage.py migrate`: migrações aplicadas, incluindo o usuário customizado na migração inicial.
- `manage.py test`: 9 testes aprovados, cobrindo renderização das páginas, filtros combinados, catálogo vazio, resposta HTMX parcial, todos os exemplos no editor, vídeo inexistente, bloqueio de POST nos previews, acesso autenticado fora do modo demonstração e login/logout por e-mail.
- `node --check static/js/studio.js`: sintaxe válida.
- `npm run build:css`: CSS compilado.
- Auditoria npm após correção das dependências transitivas: 0 vulnerabilidades reportadas.

## Validação no navegador integrado do Codex

- Biblioteca: busca por entrevista retornou somente a entrevista de Beatriz via HTMX, com query string atualizada.
- Seleção de card: barra de seleção mostrou um item; inspetor mudou nome, codec, duração, tamanho, estado, tags e links para o ativo selecionado.
- Grade/lista: alternância aplicada ao catálogo.
- Editor: tag “Pesquisa” adicionada por Enter; marcação temporal com fim anterior ao início foi rejeitada; intervalo 14:30–14:40 foi aceito e apareceu na lista.
- Capítulos: selecionar o capítulo de 02:30 reposicionou os controles e a agulha da linha do tempo para 02:30.
- Legendas: nova entrada adicionada com campo de texto e tempos próprios.
- Perfil: aba Preferências de Edição mostrou seu painel; menu do usuário abriu; alternância de tema alterou o estilo.
- Notificações: menu abriu e a ação “Marcar todas como lidas” atualizou o estado visual.
- As cinco telas foram inspecionadas visualmente. Foram corrigidos o recorte da imagem do player, a exibição das miniaturas e os nomes acessíveis da navegação recolhida.
- Não foram observados erros JavaScript nas verificações de console realizadas.

## Limites

Não foram validados vídeo/áudio reais, parser SRT, persistência de metadados, integrações externas nem ambiente de produção. Login/logout foram verificados por testes Django; não foi criada conta real. Imagens de mídia são recortes CSS das referências Stitch. A demonstração não implementa todos os critérios de aceite do MVP.
