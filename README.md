
## Локальный запуск приложения
Все команды приведены для исполнения на машине с Ubuntu.
1) Установиь Docker (если еще не установлен)
   ```
   sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   ```

3) Склонировать git репозиторий

   ```
   git clone https://github.com/buc-a/peer-learning
   ```
4) Отредактировать переменные окружения, скопировав их из .env_example
   ```
   cp .env_example .env
   vim .env
   ```
5) Запустить приложение командой 
```
docker compose up -d
```
6) При первом запуске необходимо создать супер-пользователя
   ```
   docker compose exec -it backend sh -c "python manage.py createsuperuser"
   ```
Локальный инстанс запущен. Админка доступна по адресу `http://localhost:9000/admin/`, клиентская часть: `http://localhost:9000`


## Деплой в облако 
В настоящий момент приложение развернуто в облаке. Получить к нему доступ можно по URL `http://93.77.162.254:9000`. Тестовые данные для двух пользователей: 
- login: user1
  pass: user1_passwd
- login: user2
  pass: user2_passwd
