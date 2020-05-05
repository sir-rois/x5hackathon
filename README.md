# Проект для хакатона X5 (Бесконтактная среда в мегаполисе)
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
