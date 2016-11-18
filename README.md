# taskgraph
Web-app for popular task trackers, which provides an overview of task list as an oriented graph

## Инструкция по установке и конфигурации проекта taskgraph в debian-like linux.

Получить репозиторий можно при помощи git или через интерфейс github.
Запуск скриптов install, setup, run может потребовать изменений прав доступа к ним, что можно осуществить при помощи команды `chmod` или через gui.

```bash
git clone https://github.com/mmuddy/taskgraph # Получить репозиторий

cd taskgraph/

chmod 777 install # опционально
chmod 777 setup # опционально
chmod 777 run # опционально

sudo ./install # Установить зависимости
./setup # Сконфигурировать БД
./run port # Запустить, port - опциональный параметр, значение по умолчанию - 8000
```