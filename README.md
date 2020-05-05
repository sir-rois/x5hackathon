# Проект для хакатона X5 (Бесконтактная среда в мегаполисе)
## Описание задачи
1. Изучить диаграмму переходов между экранами и подумать, где будет уместно голосовое управление
2. Написать сервис, который преобразует команды голоса в команды из протокола взаимодействия с КСО (см. приложение)
3. Произвести демонстрацию, в ходе которой будет формироваться сообщение, которое будет падать либо в файл, либо на очередь rabbitmq (по желанию участников)
## Описание решения
Полностью бесконтактное решение для управления КСО с помощью команд пользователя на естесственном языке (на текущий момент русский, но легко добавляются другие).
Примеры команд:
* Добавить товар номер 123456
* Взвесь томаты азербайджанские розовые
* Оплати
* Добавь карту лояльности 87654321
* Оплати 500 рублей баллами
## Установка
В каталоге проекта:
```
docker run -v$(pwd):/workspace/src --name testx5 -it roisdev/x5hack /bin/bash
```

В терминале докера:
```
cd src
mkdir input
pipenv --python 3.7
pipenv install
pipenv run server
```

Далее в каталоге `input` ожидается появление звуковых файлов в формате `wav` mono PCM

Для тестирования можно воспользоваться скриптом `recorder.py`. Для его запуска потребуются установленные на хост машине `pyenv` и `pipenv`:
```
pipenv --python 3.7
pipenv install
pipenv shell
python recorder.py input
```
