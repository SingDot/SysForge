# SYSFORGE - MATRIZ DE RASTREAMENTO (TIMELINE)
**Status Atual:** ATIVO
**Versão Atual:** 1.1.7 (Retomada Automática do Office + Pipeline de Deploy + Higiene de Anonimato)

## DIRETRIZES GLOBAIS DE PRODUÇÃO (REGRAS ABSOLUTAS)
As regras a seguir são a lei máxima de desenvolvimento deste projeto. Elas não podem ser ignoradas ou alteradas pela IA.

1. **Higiene de Estrutura:** Mantenha a árvore de arquivos limpa. Arquivos temporários, pastas de build cache ou artefatos gerados (que não são estritamente necessários para rodar, compilar ou versionar o projeto) devem ser excluídos imediatamente após o uso.
2. **Atualização Diária Obrigatória:** Ao final de cada sessão/dia de trabalho, a IA DEVE atualizar a seção "HISTÓRICO DE INTERVENÇÕES" deste arquivo, relatando tudo o que foi implementado e ajustando o número da versão conforme a Matriz de 4 Eixos.
3. **Controle de Deploy Manual:** A IA NÃO tem autorização para compilar o executável final ou realizar `git push`/`commit` por conta própria. O processo de build e upload para o GitHub só deve ser executado quando o usuário solicitar explicitamente ("Suba para o GitHub" ou "Compile o projeto").
4. **Bloqueio de Dependências (Leveza):** O SysForge é um executável de pendrive. É ESTRITAMENTE PROIBIDO adicionar novas bibliotecas/pacotes (via `pip`) que aumentem o peso do `.exe` sem solicitar aprovação prévia do usuário. Priorize sempre APIs nativas do Windows e bibliotecas padrão do Python.
5. **Zero Código Fantasma:** O código final entregue não pode conter restos de debug (ex: `print()` soltos para testes de console), blocos de código antigo comentado, ou marcações `TODO`. O código de produção deve ser cirúrgico e finalizado.

## DIRETRIZ DE OPERAÇÃO PARA A IA (SISTEMA):
1. LER PRIMEIRO: Toda nova sessão de desenvolvimento deve começar com a leitura deste arquivo para entender o estado atual.
2. ATUALIZAR POR ÚLTIMO: Ao finalizar uma implementação solicitada, a IA DEVE registrar a mudança aqui e calcular a nova versão com base na Matriz de 4 Eixos.

## HISTÓRICO DE INTERVENÇÕES
### [Versão 1.1.7] - Data: 2026-07-06
- [Feature] Retomada automática da instalação do Office após reboot. Novo módulo `gear/resume_office.py`: quando Esterilização + Instalar Office são selecionados juntos, o Office antigo é removido, a retomada é armada (copia o exe para `%ProgramData%\SysForge` — funciona no Host e no Portable sem depender do pendrive — e registra um gatilho RunOnce autolimpante) e o app pede reinício. No boot, o SysForge inicia com `--resume-office`, abre uma janela mínima e conclui a instalação/ativação sozinho, limpando o estado.
- [Correção de bug latente] Antes, marcar Esterilização + Office instalava o Office na MESMA sessão, logo após deletar o serviço C2R (que fica pendente de exclusão até o reboot) — o que corrompia/falhava a instalação. Agora o reboot obrigatório entre remoção e reinstalação garante instalação limpa.
- [Robustez] Guarda de tentativas (máx. 2) e RunOnce single-shot eliminam risco de loop de boot. Em modo dev (.py não compilado) o `arm_resume` é no-op seguro e cai para instalação inline.
- [Correção/Deploy] `deploy.bat` (e `bump.bat`/`reset_history.bat`) estavam com quebras de linha LF (gerados por ferramenta), o que quebrava o cmd.exe ("abre e fecha"). Convertidos para CRLF. Além disso o `deploy.bat` foi reescrito com estrutura `goto` (em vez de blocos gigantes `if (...)`) e extração de ID via arquivo (em vez de `for /f`), eliminando o erro de parsing ": foi inesperado" causado por parênteses/JSON dentro de blocos.
- [Deploy/Publicado] v1.1.7 publicada no GitHub (commit `5e38dc1`, Release v1.1.7 com Portable + Setup). OTA validado no endpoint `releases/latest`.

### [Versão 1.1.6] - Data: 2026-07-05
- [Correção/Software] `install_software` reescrito: resolve o caminho real do `winget.exe` (o alias em WindowsApps some do PATH quando o app roda elevado — causa provável de "conclui mas não instala"), captura a saída e reporta status honesto por app (instalado / já instalado / não encontrado / falha com detalhe). Removida a dependência do `window_enforcer`.
- [Correção/Software] `thread_manager` passou a reportar resumo real da instalação (`X/Y instalado(s)`) em vez do genérico "Operação concluída com sucesso" que aparecia mesmo sem instalar nada.
- [Correção/Limpeza] `executar_limpeza` reescrito: remoção robusta (chmod + `del /f` como fallback para arquivos travados), contagem de itens e bytes liberados, e retorno `(bytes, itens)`. O `cleaner_view` agora exibe "LIBERADO: X MB (N itens)" em vez de resetar para "0.00 MB" sem feedback.
- [Correção/Ativação] `activate_windows` agora **verifica o status real da licença** (`LicenseStatus=1` via CIM, independe de idioma) antes e depois de rodar o MAS, capturando a saída e reportando honestamente — não declara mais sucesso falso pelo código de retorno.
- [Correção/Reparos] `repair_sfc_dism` passou a dar feedback de cada fase (DISM 10-20 min, depois SFC) e a reportar o resultado real, resolvendo a sensação de "não sei se está funcionando".
- [Correção/Software] Auditoria completa dos 43 IDs do winget: 8 estavam desatualizados (causa da falha do AnyDesk relatada). Corrigidos: AnyDesk (`AnyDesk.AnyDesk`), WhatsApp (msstore `9NKSQGP7F2NH`), Insomnia (`Insomnia.Insomnia`), Eclipse (`EclipseFoundation.Eclipse.Java`), DBeaver (`DBeaver.DBeaver.Community`), PostgreSQL (`PostgreSQL.PostgreSQL.17`), RedisInsight (`RedisInsight.RedisInsight`). Removido VMware Workstation Player (descontinuado do winget pela Broadcom). Perfis atualizados.
- [Robustez] `run_uninstall` (app_manager) ganhou timeout de 300s + kill, evitando travar o worker caso um desinstalador abra UI.
- [Revisão Sênior] Auditoria de todos os módulos gear/gui/worker: nenhum código morto (todos referenciados), lógica dos motores restantes (config, uwp, office_checker, startup, triage) validada sem bugs.
- [Higiene] Limpeza geral: removidos todos os `__pycache__` e a pasta `logs/` vazia. Árvore no estado limpo (0 artefatos de junk).
- [Build] Build de teste v1.1.6 (Portable + Host + instalador) recompilada COM todos os fixes. NÃO publicada — aguarda validação em máquina real (admin) antes do release.

### [Versão 1.1.5] - Data: 2026-07-05
- [Higiene/Regra 5] Remoção do código de debug residual no `worker/thread_manager.py` que escrevia `sysforge_debug_worker.txt` na Área de Trabalho do cliente a cada execução de worker e a cada exceção. O traceback de erro agora é roteado para o `LogManager` interno (`LOG.add`), sem gerar arquivos soltos no sistema do usuário.
- [Correção] Cabeçalho de exportação de logs corrigido de "SysForge 2.0" (string incorreta) para a versão dinâmica real via `CURRENT_VERSION`.
- [Segurança/Anonimato] Exclusão de dois snapshots de auditoria vazados em `logs/` (gerados pelo blackbox), cujos nomes de arquivo expunham o hostname real da máquina e a marca antiga. Padrão `*-snapshot.json` agora ignorado pelo versionamento.
- [Segurança/Anonimato] `.gitignore` reforçado para ignorar `logs/`, `*-snapshot.json` e `sysforge_debug_worker.txt`, impedindo que artefatos de telemetria com hostname/IP local voltem a ser versionados.
- [Segurança/Anonimato] Centralização das rotas do GitHub em constantes únicas (`GITHUB_OWNER`/`GITHUB_REPO`) no `updater.py`, apontando para a nova conta de marca `SingDot`. Removidas as 3 URLs hardcoded que expunham o handle derivado do nome real. Remoto git local repontado para `SingDot/SysForge`.
- [Segurança/Anonimato] Substituição do e-mail pessoal de contato na tela "Sobre" por canal neutro da marca (`github.com/SingDot`).
- [Identidade] Rodapé do `DOCUMENTATION.md` realinhado ao ecossistema Singularity Dot (removida a assinatura fora de marca "protocolo do Antigravity").
- [Deploy] Criado `deploy.bat`: pipeline único que limpa artefatos, compila Portable e Host, gera o instalador via Inno Setup (`/DMyAppVersion` sincronizado com `CURRENT_VERSION`), faz commit/push do código e publica a Release com os binários (Portable + Setup) via API do GitHub, ativando o OTA. Campo de token no topo; arquivo mantido fora do versionamento (`.gitignore`) por conter segredo.
- [Deploy] `setup_script.iss` ajustado para aceitar a versão injetada externamente (`#ifndef MyAppVersion`), com fallback para compilação manual. Identificador de arquitetura atualizado de `x64` (deprecado no Inno Setup 7) para `x64compatible`.
- [Deploy] Criado `bump.bat`: incrementa o patch automaticamente (ou aceita versão exata como argumento) atualizando `CURRENT_VERSION` na fonte única.
- [Deploy] Criado `reset_history.bat`: migração one-time para histórico git limpo na conta `SingDot` (remove os vazamentos do histórico antigo).
- [Build] Bump para v1.1.5 aplicado. Binários compilados e validados: Portable, Host (PyInstaller) e instalador via Inno Setup, todos rotulados v1.1.5. Artefatos 1.1.4 antigos removidos de `dist/`/`Output/`.
- [Deploy/Concluído] Migração para a conta `SingDot` publicada: histórico git novo e limpo (commit `4b6d52f`, autor anônimo `SingDot` via e-mail noreply), código enviado e Release v1.1.5 criada com os binários Portable + Setup. OTA validado no endpoint `releases/latest`.
- [Correção] `reset_history.bat` passou a configurar a identidade anônima do git (`user.name`/`user.email` noreply) logo após o `git init`, corrigindo a falha "unable to auto-detect email address" que ainda usaria o hostname com o nome real.
- [Pendente/Segurança] Rotacionar o token: gerar um novo com escopo mínimo (`repo`) e revogar o atual (criado com escopo excessivo e exposto em sessão).

### [Versão 1.1.4] - Data: 2026-06-23
- [Arquitetura/Sistema] Redesign do motor de implantação do Office (`office_deploy.py`), removendo a flag `CREATE_NO_WINDOW` que impedia o setup oficial da Microsoft de instanciar sua interface de download.
- [Arquitetura/Sistema] Implementação de monitoramento de timeout (1 hora) e captura de logs na fase de ativação (MAS Ohook) via `subprocess.run(capture_output=True)`.
- [Interface] Substituição da barra de progresso no Dashboard do modo indeterminado (`.start()`) para o modo determinístico (`.set()`), integrando um `progress_callback` com propagação real na árvore do `GenericWorker`.
- [Deploy] Refatoração do script de compilação (`builder.py`) para embutir nativamente o diretório `OfficeInstall` nos artefatos executáveis usando a flag `--add-data` do PyInstaller.
- [Deploy] Injeção dinâmica de metadados avançados (VSVersionInfo, ProductName, Copyright) nos binários Python e no instalador final do Inno Setup.
- [Deploy] Versões Portable e Host compiladas e empacotadas com o pacote Office.

### [Versão 1.0.4] - Data: 2026-06-22
- [Arquitetura/Sistema] Refatoração total do motor de threads (Thread-Safe UI), substituindo as chamadas de `.after()` por `queue.Queue` nas classes `GenericWorker` para sanar RuntimeErrors no Tkinter.
- [Deploy] Alteração do fluxo de implantação do Office LTSC forçando flag `Display Level="Full"` no `config.xml` para garantir feedback visual nativo no Windows ao invés de rodar invisível.
- [Feature/Core] Implementação do Módulo de Esterilização Profunda (`debloater.py`), focado na remoção completa e segura de rastros prévios do Microsoft Office e de Bloatwares UWP Nativos do Windows.
- [Deploy] Versões Portable e Host compiladas e atualizadas (v1.0.4). Push autorizado no repositório remoto.
### [Versão 1.0.3] - Data: 2026-06-16
- [Identidade] Rebranding completo do projeto para o ecossistema Singularity Dot, removendo referências ao M Lab.
- [Arquitetura/Sistema] Criação do DOCUMENTATION.md, e atualização do README.
- [Deploy] Versões Portable e Host compiladas e atualizadas (v1.0.3). Push autorizado no repositório remoto.
### [Versão 1.0.1] - Data: 2026-06-03
- [Deploy] Implementação de Dynamic Naming no pipeline de build. O builder.py e o Inno Setup agora carimbam o artefato final com a versão correspondente (ex: v1.0.1) de forma automatizada via extração da constante global. Limpeza de batch scripts adaptada com wildcards (`v*.exe`).
- [Arquitetura/Sistema] Bump de versão para v1.0.1. Preparação dos artefatos para o teste de validação de campo do Auto-Updater e roteamento da API.

### [Versão 1.0.0] - Data: 2026-06-03
- [Arquitetura/Sistema] Hotfix no Pipeline de Build: Transição de 'Destructive Cleanup' (`rmdir dist`) para Limpeza Seletiva (`del target.exe`) nos orquestradores batch, garantindo a coexistência dos artefatos Host e Portable.
- [Arquitetura/Interface] Refatoração Global de Fase 1 (v1.0.0): Injeção do Protocolo de Higiene Automática (.bat com `del /q *.exe`), calibração do Grid de UI (Sidebar rígida de 220px, botões 36px com raio 2, margens 20px no Dashboard/Info), e injeção de logs de batalha no motor OTA Updater (`gear/updater.py`). Re-verificado separação correta dos binários via `--name`.
- [Arquitetura/Sistema] Auditoria de Pipeline de Build concluída. Injetada ancoragem UAC (`cd /d "%~dp0"`) nos scripts batch e revisada a segurança da rotina de cleanup para proteger artefatos vitais do PyInstaller. Correção de caminho de ícone do Inno Setup restabelecida à raiz.
- [Deploy] Inno Setup modernizado (WizardStyle=modern, Compressão LZMA2 Ultra64, bloqueio x64).
- [Interface] Implementação bidirecional da Ponte Host-Portable na Sidebar.
- [Build] Scripts de compilação injetados com destruição recursiva da pasta build para higiene automatizada de cache.
