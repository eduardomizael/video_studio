# Interface demonstrativa — integração com o backend

**Atualização em 04/10/2026:** o primeiro incremento do catálogo real está implementado. Com `UI_DEMO=False`, a biblioteca e o editor usam `app/catalog`, formulários POST autenticados e dados persistidos. A descrição abaixo documenta a prévia original; o estado atual e as próximas integrações estão em [BACKEND_CATALOGO.md](BACKEND_CATALOGO.md).

## Referências

Fonte: Stitch MCP, projeto `projects/10933097738787237741`, consultado em 04/10/2026. As cinco telas são Biblioteca de Mídia, Editor de Metadados & Vídeo, Capítulos e Legendas, Perfil do Usuário e Configurações e Menus Suspensos de Usuário & Notificações. Logo e avatar também vêm do mesmo projeto.

O HTML disponível nos links do MCP exigiu sessão Google, e o navegador exibiu novos termos de serviço. Não foram aceitos termos nem alterado o projeto remoto. A interface foi reconstruída pelos screenshots originais e pelo sistema visual Studio Obsidian: Inter, JetBrains Mono, superfícies escuras, destaque violeta, estados verdes e bordas discretas. O escopo de domínio segue os requisitos locais: cadastro por referência local, sem upload de mídia nem exclusão de vídeos.

## Componentes

`base.html` define a estrutura geral. Use `extends` nas páginas e `include` para os componentes existentes. `field.html`, `badge.html`, `toggle.html` e `icon.html` recebem parâmetros explícitos. Listas de vídeos, capítulos, legendas e notificações são renderizadas por loops e dados vindos das views.

`library_results.html` é a fronteira da atualização HTMX. Busca, filtros e ordenação já chegam por query string; substituir a filtragem de `demo.VIDEOS` por consultas paginadas ao modelo de catálogo, mantendo os parâmetros da view. O inspetor recebe o conjunto de exemplos por `json_script`, sem interpolação de dados em JavaScript executável.

## Próxima integração

1. Implementar os modelos de catálogo/anotações definidos nos requisitos.
2. Trocar o contexto `app/studio/demo.py` por consultas e formulários Django, preservando os contratos dos templates.
3. Converter ações temporárias em POSTs autenticados com CSRF, validação no servidor e respostas parciais.
4. Substituir o player de imagem por vídeo servido pelo endpoint autenticado, com validação da raiz de mídia; ligar a linha do tempo ao `currentTime` do player real.
5. Implementar parser/importação SRT, versões, entradas e sincronização real. A validação JavaScript da prévia não substitui as regras no servidor.
6. Remover os avisos demonstrativos somente quando houver persistência e comportamento real correspondentes.

Perfil, notificações e conexões são representações visuais solicitadas para esta entrega. Não ampliam automaticamente o escopo funcional do MVP. Autenticação está preparada com um usuário customizado desde a primeira migração.

## Recursos e manutenção

- CSS compilado: `npm run build:css`; fontes e scripts ficam locais.
- Tailwind 4.3.0 com versões fixadas e lockfile; HTMX 2.0.4 local.
- As imagens completas do Stitch são usadas provisoriamente como sprites CSS. Preservar as referências para comparação; miniaturas reais devem substituir esses recortes na integração.
- `scripts/fetch_stitch.py` e `scripts/fetch_fonts.py` são ferramentas de obtenção de referências, não são necessárias para executar a aplicação. `screens.json`, gerado pelo MCP, não é versionado porque contém URLs temporárias.
- Fontes Inter e JetBrains Mono: SIL Open Font License em `static/fonts/`. HTMX: licença local em `static/vendor/`.
