# Automatic Template Creator

`data/template_creator/` изолирует результаты автоматического провайдерного
анализа от production-каталогов. В `drafts/` лежат только generated JSON drafts;
Пустой `active_templates.json` создаётся общим атомарным storage-классом, но
Creator его не читает и не публикует в него: публикацию выполняет проверенный
overlay `data/template_studio/active_templates.json`.

Перед добавлением в список candidate проходит строгую схему, ограниченный AST,
preview и независимую математическую проверку. Неуспешный candidate остаётся
draft и не меняет каталог модулей.
