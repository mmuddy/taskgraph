# Taskgraph

### Overview
Web-app for popular task trackers, which provides an overview of task list as an oriented graph

### Инструкция по установке и конфигурации проекта taskgraph в debian-like linux.

Получить репозиторий можно при помощи git или через интерфейс github.
Запуск скриптов install и configure может потребовать изменений прав доступа к ним, что можно осуществить при помощи команды `chmod` или через gui.

```bash
git clone https://github.com/mmuddy/taskgraph # Получить репозиторий

cd taskgraph/

chmod 777 install apache/configure run # опционально

# sudo ./install - Установить зависимости
# sudo ./apache/configure - сгенерировать настройки для apache, 
                            первый параметр - путь к настройкам apache, по умолчанию: /etc/apache2
                            второй параметр - имя конфигурационного файла, по умолчанию apache2.conf
# sudo service apache2 restart - перезапустить apache
sudo ./install && sudo ./apache/configure && sudo service apache2 restart
```