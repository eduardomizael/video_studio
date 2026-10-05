# Primeiro incremento do backend: catálogo

Este documento registra o primeiro incremento. A integração posterior de reprodução e inspeção está documentada em [BACKEND_MIDIA.md](BACKEND_MIDIA.md).

Data: 04/10/2026. Escopo executado: modelos do catálogo, cadastro/edição de referências locais, biblioteca persistida e associações. O MVP completo ainda não está concluído.

## Implementado

- App `app/catalog`, migração inicial e modelos `LocalMidia`, `Video`, `Tag` e `Pessoa`.
- Referência única por local de mídia e caminho normalizado, com normalização de caixa compatível com Windows.
- Tags com chave Unicode/caixa/espaços normalizada e única no banco. Homônimos de pessoas são permitidos e identificados pelo ID.
- Cadastro por modal e edição de título, descrição, local/caminho, tags e pessoas no formulário Django. Criação de tags e de uma pessoa durante a associação.
- Gravação atômica do vídeo e relações, autor/data de criação e última edição. Remoção de associação preserva os cadastros globais.
- Biblioteca por consulta ao SQLite: busca por título/descrição, múltiplas tags/pessoas, ordenação estável e paginação de 12 registros. OR dentro de cada filtro, AND entre texto/tags/pessoas.
- Respostas HTMX de resultados e inspetor. O JSON do inspetor contém somente a página atual; é atualizado após filtros/paginação.
- Identidade autenticada no cabeçalho e conta; administração dos locais e usuários restrita ao Django Admin. Vídeos não possuem ação de exclusão pela interface ou Admin.
- Erros no servidor preservam os campos digitados. POST exige autenticação/CSRF; GET não grava os formulários.
- `UI_DEMO=False` como padrão. A prévia antiga pode ser ativada explicitamente, mas seus endpoints de cadastro/salvamento não gravam dados reais.

## Segurança e arquivos

A raiz é absoluta e administrada no servidor. O caminho enviado pelo usuário é relativo, com barras normalizadas; resolve-se o destino canônico e verifica-se sua contenção na raiz ativa. São rejeitados caminhos absolutos/UNC/drives, segmentos `..`, pastas, dois-pontos/fluxos alternativos e destinos resolvidos fora da raiz, inclusive por links simbólicos.

Cadastro e salvamento conferem disponibilidade por leitura de um byte: disponível, não encontrado ou sem acesso. Um arquivo ausente pode ter seus metadados cadastrados/editados. Não existe monitoramento automático; o estado apresentado corresponde ao último salvamento. Nenhum arquivo de vídeo é modificado, enviado ou removido.

## Rotas entregues

| Método/rota | Função |
| --- | --- |
| `GET /` | Biblioteca real ou demonstrativa, conforme configuração |
| `POST /videos/novo/` | Cadastro autenticado |
| `GET /videos/<id>/` | Editor real ou demonstrativo |
| `POST /videos/<id>/salvar/` | Salvamento autenticado e transacional |
| `GET /perfil/` | Identidade real; preferências demonstrativas somente em UI_DEMO |
| `/admin/` | Configuração de locais e administração das contas |

Sem endpoint de exclusão de vídeos. Tags/pessoas existentes são pesquisáveis nos seletores do editor; a busca visual não altera suas associações até o salvamento.

## Como usar

1. Execute `uv run python manage.py migrate`.
2. Crie sua conta com `uv run python manage.py createsuperuser`, definindo as credenciais no terminal.
3. Mantenha `UI_DEMO=False` e inicie o servidor.
4. Cadastre no Admin um local de mídia com a raiz absoluta da pasta do servidor.
5. Cadastre um vídeo pelo modal e edite seus metadados. Recarregar e buscar devem recuperar os valores salvos.

O primeiro local deve ser escolhido por quem administra o acervo; nenhuma pasta privada do computador foi cadastrada automaticamente. A validação visual usa conta, registros e SQLite temporários, separados do banco da aplicação.

## Verificação

- Suíte Django: 30 testes executados, 29 aprovados e 1 ignorado porque o ambiente Windows não permitiu criar um link simbólico real. Os outros testes de contenção, caminhos absolutos, traversal, normalização, duplicação, transações e autorização passaram.
- `manage.py check` sem problemas; `makemigrations --check --dry-run` sem alterações pendentes.
- Build CSS concluído e sintaxe JavaScript validada.
- Navegador: login, cadastro pelo modal, edição de descrição/tags/pessoas, recarga com valores persistidos, busca e filtros combinados por HTMX, paginação, atualização do inspetor, rejeição de caminho externo e descarte retornando aos valores gravados.
- Nenhum erro JavaScript observado na sessão de validação. Captura local: `artifacts/editor-catalogo-real.png`, com dados descartáveis.

## Próximo incremento

Endpoint autenticado de mídia com seek, extração de duração/miniatura e fallback manual; depois marcações e SRT. Nesta entrega, o player real e os dados técnicos ainda estão explicitamente indisponíveis. Perfil editável, notificações, lote, classificações adicionais e integrações não foram implementados.
