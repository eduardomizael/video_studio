# Video Studio

Aplicação Django baseada nas telas do projeto Stitch **Video Metadata Player Interface**. O primeiro incremento do backend oferece catálogo persistido, cadastro por referência local, edição de título/descrição, tags e pessoas, busca, filtros combinados e paginação. O modo demonstrativo das cinco telas continua disponível separadamente.

## Executar localmente

Pré-requisitos: UV e Node/npm.

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

Um arquivo ausente pode ser catalogado e será identificado como `Arquivo não encontrado`. A disponibilidade é conferida no cadastro e salvamento; nesta etapa ainda não há monitoramento automático. O arquivo de vídeo não é enviado, modificado ou excluído pela aplicação. Contas e locais são administrados pelo Django Admin; todos os usuários autenticados podem editar o catálogo.

Para revisar a prévia anterior, configure `UI_DEMO=True` com `DEBUG=True` e reinicie o servidor. Essa prévia usa apenas exemplos e não aceita gravações no catálogo. Ao usar o backend real, mantenha `UI_DEMO=False`.

Durante desenvolvimento, `npm run watch:css` acompanha alterações. O CSS compilado, HTMX, fontes e imagens são servidos localmente; a interface não depende de CDN.

## Telas

| URL | Conteúdo |
| --- | --- |
| `/` | Biblioteca real: busca, filtros, grade/lista, paginação e inspetor |
| `/videos/<id>/` | Editor real: informações, referência local, tags e pessoas |
| `/videos/<id>/capitulos/` | Aviso de etapa pendente; prévia de capítulos/SRT em UI_DEMO |
| `/perfil/` | Identidade autenticada; prévia de preferências em UI_DEMO |
| `/componentes/` | Aviso de etapa pendente; referência de menus em UI_DEMO |
| `/conta/entrar/` | Login Django por e-mail |
| `/admin/` | Administração Django |

## Limite desta entrega

- No modo real, a biblioteca consulta o banco, permite múltiplas tags/pessoas por filtro e pagina os resultados em grupos de 12. HTMX atualiza resultados e inspetor; somente os dados da página atual são enviados ao navegador.
- Título, descrição, referência local e associações são persistidos em transação, com autor e datas. Erros preservam os campos digitados. Remover uma associação não apaga a tag/pessoa global.
- Caminhos absolutos, traversal, referências a pastas, fluxos alternativos e resolução fora da raiz autorizada são bloqueados. A mesma referência local não pode gerar dois vídeos. Tags são normalizadas por Unicode, espaços e caixa; pessoas homônimas permanecem distintas.
- O player real, extração de duração/miniatura, marcações e importação/edição SRT ainda não foram implementados. O modo real mostra essa limitação sem reutilizar dados fictícios.
- Perfil editável, notificações, integrações, lote, áudio/imagens e categorias adicionais continuam fora deste incremento. A identidade do usuário autenticado já aparece no cabeçalho e em Minha conta.
- No modo demonstrativo, os comportamentos antigos continuam temporários no navegador e o player simula uma linha do tempo sobre imagem de referência.
- `UI_DEMO=True` exige `DEBUG=True`. Esta configuração é para revisão local, não para publicação.
- O foco visual é desktop, conforme os requisitos do MVP. Há adaptação para janelas menores, sem declarar suporte mobile completo.

## Estrutura

- `config/`: configurações, URLs e WSGI.
- `app/accounts/`: usuário customizado e administração.
- `app/catalog/`: modelos, migração inicial, formulários, validação de caminhos, serviços transacionais, consultas e testes do catálogo real.
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

As decisões do produto estão em `docs/REQUISITOS.md`; o plano do MVP permanece em `docs/PLANO_IMPLEMENTACAO.md`. O estado deste primeiro incremento e suas verificações estão em [BACKEND_CATALOGO.md](docs/BACKEND_CATALOGO.md). As etapas de mídia, anotações e SRT continuam pendentes.

O [levantamento do backend a partir das telas](docs/LEVANTAMENTO_BACKEND.md) mapeia dados, regras, serviços e rotas necessários para substituir a demonstração, incluindo as extensões visuais além do MVP.
