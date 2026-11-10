# 🎮 Pokédex do Treinador (versão simplificada)

Aplicação Django que consome a [PokéAPI](https://pokeapi.co/). **Qualquer visitante pode buscar Pokémon**; para **salvar** na coleção é preciso entrar na conta.

## Funcionalidades

| Tela | Rota | Acesso |
|---|---|---|
| Buscar Pokémon na API | `/buscar_dados_pokemon/` | Livre |
| Dashboard | `/` | Logado (visitante vai para a busca) |
| Minha coleção (listar) | `/listar_pokemons/` | Logado |
| Salvar (botão na busca, `POST`) | `/salvar_pokemon/` | Logado |
| Detalhes / Editar / Remover | `/<id>/detalhes_pokemon/` · `editar_pokemon/` · `remover_pokemon/` | Logado, só o dono |
| Consultas com filtros | `/consultas/` | Logado |
| Relatório + CSV | `/relatorio/` · `/relatorio/exportar/` | Logado |
| Login / Cadastro | `/login/` · `/cadastrar/` | Livre |
| Perfil / Editar perfil | `/perfil/` · `/perfil/editar/` | Logado |

Fluxo: o visitante busca → clica em **Entrar para salvar** → faz login → volta ao resultado → **Adicionar à minha coleção**. Pokémon de outro treinador retornam **404**.

## Models

- `Regiao` — nome, número inicial/final (9 regiões criadas pela migração `0002`)
- `Treinador` — 1:1 com `User`; nome, cidade natal, data de cadastro
- `Habilidade` — nome
- `Pokemon` — nome, id_pokemon, treinador (FK), regiao (FK), tipos, altura, peso, habilidades (N:N), hp, ataque, defesa, velocidade, sprite_url, observacoes, favorito, capturado, data_captura
- `PokemonHabilidade` — tabela `through` (campo `oculta`)

Nenhum model possui métodos; a região é definida na view ao salvar.

## Executar

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Testes

```bash
python manage.py test
```
