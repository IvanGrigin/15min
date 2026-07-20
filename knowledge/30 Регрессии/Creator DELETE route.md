# Creator DELETE route

Симптом: кнопка «Удалить» в automatic Template Creator получала 404, хотя
frontend отправлял корректный `DELETE /api/template-creator/{draft_id}`.

Причина: ветка Creator по ошибке находилась в `do_PATCH`, а не в `do_DELETE`
HTTP-handler сайта.

Фикс: перенести dispatch в `WorksheetSiteHandler.do_DELETE`; `PATCH` теперь
остался только для редактирования draft Template Studio.

Защита: route и modal-элемент входят в регрессионный набор Creator; service-тест
проверяет подтверждённое удаление draft и сохранность active-шаблона.
