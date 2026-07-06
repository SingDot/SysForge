# [SD-02] SYSFORGE
> STATE: PUBLISHED & STABLE
> VERSION: 1.1.7 · AWAITING FIELD VALIDATION

## Último Ponto de Execução (The Dot)
- [x] Migração para a conta de marca **SingDot** com histórico git limpo (anonimato total — sem nome real em código, docs ou histórico).
- [x] Correção dos IDs do winget (AnyDesk e outros 7) — instalação de software funcional.
- [x] Feedback honesto em todos os subsistemas (instalação, limpeza, ativação, reparos).
- [x] **Feature 1.1.7:** retomada automática da instalação do Office após reboot (RunOnce + `gear/resume_office.py`), corrigindo o bug latente de reinstalar por cima do serviço C2R pendente.
- [x] Pipeline de deploy consolidado: `bump.bat` → `deploy.bat` (build Portable + Host + Inno Setup + push + Release/OTA). Scripts em CRLF, estrutura `goto` robusta.
- [x] **v1.1.7 publicada** no GitHub (Release com Portable + Setup, OTA validado).

## Próximo Ciclo
- [ ] Validar em campo (máquina real, admin): instalação de software, limpeza, ativação e a retomada do Office pós-reboot.
- [ ] Segurança: rotacionar o token do GitHub para escopo mínimo (`repo`) e revogar o atual.
