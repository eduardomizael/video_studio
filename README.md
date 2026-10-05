# Video Studio

Aplicação Django baseada nas telas do projeto Stitch **Video Metadata Player Interface**. O backend oferece catálogo persistido, cadastro por referência local, edição de metadados, tags/pessoas, busca, filtros e paginação, além de player autenticado com seek e extração de duração/miniatura. O modo demonstrativo das cinco telas continua disponível separadamente.

## Executar localmente

Pré-requisitos: UV e Node/npm. FFprobe e FFmpeg são opcionais para a extração automática; o cadastro e a correção manual continuam disponíveis sem eles.

```powershell
uv sync
npm ci
npm run build:css
uv run python manage.py migrate
uv run python manage.py runserver 127.0.0.1:8000
```

Abra http://127.0.0.1:8000/. O padrão é `UI_DEMO=False`, com login obrigatório e dados reais no SQLite. Para ajustes de ambiente, copie `.env.example` para `.env`. O banco `db.sqlite3` é local e não deve ser versionado.

### Primeiro uso do catálogo

1. Crie sua conta administrativa com `uv run python manage.py createsuperuser`; informe e-mail e senha no terminal.
2. Entre em `/admin/` e cadastre um **Local de mídia**, com nome, raiz absoluta de uma pasta acessível ao servidor e estado ativo.
3. Abra a biblioteca e use **Cadastrar vídeo**, informando título, local e caminho relativo, por exemplo `entrevistas/episodio-08.mp4`.
4. Edite descrição, selecione tags/pessoas existentes ou cadastre novas pelo formulário e salve. Os dados permanecem após recarregar.

Um arquivo ausente pode ser catalogado e será identificado como `Arquivo não encontrado`. A disponibilidade é conferida no cadastro, salvamento e abertura do editor, além da tentativa de leitura pelo player; não há monitoramento em segundo plano. O arquivo de vídeo não é enviado, modificado ou excluído pela aplicação. Contas e locais são administrados pelo Django Admin; todos os usuários autenticados podem editar o catálogo.

Ao cadastrar ou trocar a referência de mídia, o sistema tenta extrair duração, codec, resolução, tamanho e um frame de miniatura. Use **Reinspecionar arquivo** se o conteúdo mudar mantendo o mesmo caminho. A duração pode ser corrigida em milissegundos; a miniatura manual usa o caminho relativo de uma imagem existente no mesmo local de mídia. Limpar a duração permite retornar à extração automática. Miniaturas geradas ficam em `private_media/`, fora dos estáticos e do Git, e exigem login para leitura.

Para revisar a prévia anterior, configure `UI_DEMO=True` com `DEBUG=True` e reinicie o servidor. Essa prévia usa apenas exemplos e não aceita gravações no catálogo. Ao usar o backend real, mantenha `UI_DEMO=False`.

Durante desenvolvimento, `npm run watch:css` acompanha alterações. O CSS compilado, HTMX, fontes e imagens são servidos localmente; a interface não depende de CDN.

## Telas

| URL | Conteúdo |
| --- | --- |
| `/` | Biblioteca real: busca, filtros, grade/lista, paginação e inspetor |
| `/videos/<id>/` | Editor real: informações, referência local, tags e pessoas |
| `/videos/<id>/capitulos/` | Player, capítulos e marcações persistidas |
| `/videos/<id>/legendas/` | Importação SRT, versões e edição de entradas |
| `/perfil/` | Identidade autenticada; prévia de preferências em UI_DEMO |
| `/componentes/` | Aviso de etapa pendente; referência de menus em UI_DEMO |
| `/conta/entrar/` | Login Django por e-mail |
| `/admin/` | Administração Django |

## Limite desta entrega

- No modo real, a biblioteca consulta o banco, permite múltiplas tags/pessoas por filtro e pagina os resultados em grupos de 12. HTMX atualiza resultados e inspetor; somente os dados da página atual são enviados ao navegador.
- Título, descrição, referência local e associações são persistidos em transação, com autor e datas. Erros preservam os campos digitados. Remover uma associação não apaga a tag/pessoa global.
- Caminhos absolutos, traversal, referências a pastas, fluxos alternativos e resolução fora da raiz autorizada são bloqueados. A mesma referência local não pode gerar dois vídeos. Tags são normalizadas por Unicode, espaços e caixa; pessoas homônimas permanecem distintas.
- O player real usa os controles nativos do navegador e mídia autenticada, com GET/HEAD e intervalos HTTP. Duração e miniatura possuem extração automática e fallback manual. Formatos/codecs que o navegador não reproduz recebem mensagem; não há conversão automática.
- Marcações pontuais e intervalos possuem criação, edição e remoção com confirmação, tags/pessoas próprias, autor e datas. A linha do tempo posiciona o player e permite capturar a posição atual em milissegundos. Tempos inválidos e reduções de duração que invalidem trechos existentes são bloqueados.
- SRT possui importação UTF-8 validada, versões com nome/idioma, uma versão ativa, edição de entradas e reprodução sincronizada por faixa nativa. O limite é 2 MB e 5.000 entradas por versão; o arquivo SRT não é armazenado. Os protótipos continuam disponíveis em UI_DEMO.
- Perfil editável, notificações, integrações, lote, áudio/imagens e categorias adicionais continuam fora deste incremento. A identidade do usuário autenticado já aparece no cabeçalho e em Minha conta.
- No modo demonstrativo, os comportamentos antigos continuam temporários no navegador e o player simula uma linha do tempo sobre imagem de referência.
- `UI_DEMO=True` exige `DEBUG=True`. Esta configuração é para revisão local, não para publicação.
- O foco visual é desktop, conforme os requisitos do MVP. Há adaptação para janelas menores, sem declarar suporte mobile completo.

## Estrutura

- `config/`: configurações, URLs e WSGI.
- `app/accounts/`: usuário customizado e administração.
- `app/catalog/`: modelos, migração inicial, formulários, validação de caminhos, serviços transacionais, consultas e testes do catálogo real.
- `app/annotations/`: marcações temporais, formulários, serviços transacionais, validação de tempos e testes.
- `app/studio/`: views, contexto compartilhado e dados demonstrativos.
- `templates/base.html`: layout comum.
- `templates/components/`: navegação, cabeçalho, menus, cards, inspetor, campos, player, tags, marcações, legendas, toggles e modais.
- `templates/studio/`: páginas e fragmento HTMX da biblioteca.
- `static/src/studio.css`: tokens visuais e estilos, compilados por Tailwind 4.
- `static/js/studio.js`: comportamentos da interface.
- `docs/stitch/`: imagens originais consultadas pelo MCP.

Os arquivos HTML do Stitch redirecionaram para autenticação Google. As páginas foram reconstruídas a partir das imagens de referência e do design system obtidos pelo MCP. Miniaturas e imagem do player utilizam recortes por CSS das referências originais, provisoriamente; substituir por ativos individuais ao conectar o catálogo. O projeto remoto não foi modificado.

## Verificações

```powershell
uv run python manage.py check
uv run python manage.py test
uv run python manage.py makemigrations --check --dry-run
node --check static/js/studio.js
npm run build:css
```

As decisões do produto estão em `docs/REQUISITOS.md`; o plano do MVP permanece em `docs/PLANO_IMPLEMENTACAO.md`. Os incrementos e verificações estão em [BACKEND_CATALOGO.md](docs/BACKEND_CATALOGO.md), [BACKEND_MIDIA.md](docs/BACKEND_MIDIA.md), [BACKEND_MARCACOES.md](docs/BACKEND_MARCACOES.md) e [BACKEND_SRT.md](docs/BACKEND_SRT.md). A consolidação de qualidade e entrega é a próxima etapa.

O [levantamento do backend a partir das telas](docs/LEVANTAMENTO_BACKEND.md) mapeia dados, regras, serviços e rotas necessários para substituir a demonstração, incluindo as extensões visuais além do MVP.
