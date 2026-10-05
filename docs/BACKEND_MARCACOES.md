# Backend de capítulos e marcações

Incremento implementado em 04/10/2026, após catálogo e reprodução local. A página `/videos/<id>/capitulos/` passa a consultar e gravar marcações reais quando `UI_DEMO=False`.

## Dados e regras

`app.annotations.MarcacaoTemporal` pertence a um vídeo, possui título obrigatório, início e fim opcional, tags, pessoas, autor de criação, último autor de edição e datas. Capítulos usam esse mesmo modelo, sem duplicar o domínio.

- Os tempos são inteiros em milissegundos. A interface aceita `MM:SS`, `HH:MM:SS` e frações de até três dígitos com ponto ou vírgula; exibe `HH:MM:SS.mmm`.
- Fim vazio representa um ponto; fim preenchido representa um intervalo. Fim igual ao início é permitido. Tempos negativos, fim anterior ao início e valores além da duração conhecida são rejeitados.
- Intervalos sobrepostos são permitidos e aparecem em faixas separadas na linha do tempo. A lista usa início e identificador para ordenar.
- Tags e pessoas são associações próprias do trecho. Alterá-las não altera as associações do vídeo inteiro nem exclui cadastros globais.
- Se a duração é desconhecida, a validação não presume um limite. Arquivo ausente ou local inativo não impede editar as informações da marcação.
- Reduzir a duração abaixo de uma marcação existente é bloqueado, inclusive ao trocar a referência ou aplicar nova inspeção automática. Corrija as marcações antes de aplicar essa alteração.

## Interface

A tela reúne player real, lista cronológica, formulário e linha do tempo. Os botões **Usar posição atual** preenchem início/fim com a posição real do player, em milissegundos. Selecionar uma marcação posiciona o vídeo no início; o controle de tempo acompanha a reprodução. Capturar ou preencher campos exige salvar para persistir.

Edição carrega os valores existentes. Erros preservam o que foi digitado. A remoção exige uma página de confirmação e POST; remove somente a marcação e suas associações. O vídeo, seu arquivo, tags e pessoas globais são preservados.

## Rotas e gravação

Todas as rotas exigem login. Todos os usuários autenticados têm os mesmos direitos de edição previstos no MVP. As operações verificam se a marcação pertence ao vídeo da URL; gravações usam POST e CSRF. `UI_DEMO=True` não permite alterar marcações reais.

| Rota relativa a `/videos/<id>/` | Método | Operação |
| --- | --- | --- |
| `capitulos/` | GET | Player, lista e formulário de criação |
| `marcacoes/nova/` | POST | Criar |
| `marcacoes/<marcacao>/editar/` | GET | Formulário de edição |
| `marcacoes/<marcacao>/salvar/` | POST | Atualizar |
| `marcacoes/<marcacao>/confirmar-remocao/` | GET | Confirmar sem alterar dados |
| `marcacoes/<marcacao>/remover/` | POST | Remover |

Serviços transacionais gravam a marcação, suas associações e a atualização de autor/data do vídeo. A duração é conferida novamente dentro da transação, com bloqueio do vídeo nos bancos que suportam `select_for_update`; SQLite serializa gravações. Restrições no banco impedem tempos negativos e intervalos invertidos. O Admin expõe marcações apenas para consulta.

## Verificação e limites

A suíte completa tem 64 testes: 63 passaram e um foi ignorado por exigir criação real de symlink no Windows. Os testes cobrem limites temporais, sobreposição, relacionamentos, rollback, autenticação, CSRF, remoção, vínculo com o vídeo e proteção contra duração extraída menor.

No navegador, um WebM sintético de 3,008 segundos validou criação, recarga, edição, associações, seek em 1,125 segundo e captura do mesmo instante. Não foi usado o acervo do usuário. Evidência visual: `artifacts/marcacoes-reais.png`. Checks Django, migrações, sintaxe JavaScript e build CSS passaram.

No encerramento desta etapa, SRT ficou para o incremento seguinte, agora registrado em [BACKEND_SRT.md](BACKEND_SRT.md). Não há colaboração em tempo real nem auditoria completa. O acesso e a compatibilidade dos arquivos reais continuam sujeitos às condições documentadas em [BACKEND_MIDIA.md](BACKEND_MIDIA.md).
