# Entrega Semana 4 — Autenticação

## Checklist
- [x] Login funcional (`/login/`) com redirecionamento para a página pedida
- [x] Cadastro de usuário (`/cadastrar/`) que cria o perfil de treinador (1:1 com `User`)
- [x] Logout (POST) pelo menu lateral
- [x] Área restrita: todas as telas exigem login
- [x] Perfil do usuário logado (`/perfil/`): ver, editar dados e alterar senha
- [x] Permissões por usuário: Pokémon de outro treinador -> 403 (ver, editar e remover)
- [x] Dono do Pokémon sempre = usuário logado (POST forjado é ignorado)
- [x] Nada anterior quebrou: os 69 testes das semanas 1-3 continuam passando
- [x] 32 testes novos (101 no total)

## Para rodar
```
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Tag
```
git add .
git commit -m "Semana 4: autenticação, área restrita e permissões por usuário"
git tag semana-4 -m "Entrega semana 4"
git push && git push --tags
```
