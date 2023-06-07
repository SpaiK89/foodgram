# Проект продуктовый помощник Foodgram

Foodgram - продуктовый помощник, позволяет публиковать рецепты,
подписываться на публикации других пользователей, добавлять понравившиеся
рецепты в «Избранное» и «Список покупок». Доступно скачивание сводного
списка продуктов в формате txt, необходимых для приготовления одного или
нескольких выбранных блюд.

## Описание проекта:
### Главная страница
На странице - cписок первых шести рецептов, отсортированных по дате публикации
(от новых к старым). Остальные рецепты доступны на следующих страницах: внизу
страницы есть пагинация.

### Страница рецепта
На странице - полное описание рецепта. Для авторизованных пользователей -
возможность добавить рецепт в избранное и в список покупок, возможность
подписаться на автора рецепта.

### Страница пользователя
На странице - имя пользователя, все рецепты, опубликованные пользователем и
возможность подписаться на пользователя.

### Подписка на авторов
Подписка на публикации доступна только авторизованному пользователю. Страница
подписок доступна только владельцу.

Сценарий поведения пользователя:
1. Пользователь переходит на страницу другого пользователя или на страницу 
   рецепта и подписывается на публикации автора кликом по кнопке «Подписаться
   на автора».
2. Пользователь переходит на страницу «Мои подписки» и просматривает
   список рецептов, опубликованных теми авторами, на которых он подписался.
   Сортировка записей - по дате публикации (от новых к старым). 
3. При необходимости пользователь может отказаться от подписки на автора:
   переходит на страницу автора или на страницу его рецепта и нажимает
   «Отписаться от автора».

### Список избранного
Список избранного может просматривать только его владелец. Сценарий поведения пользователя:
1. Пользователь отмечает один или несколько рецептов кликом по кнопке
   «Добавить в избранное».
2. Переходит на страницу «Список избранного» и просматривает
   персональный список избранных рецептов. При необходимости пользователь может 
   удалить рецепт из избранного.

### Список покупок
Список покупок может просматривать только его владелец.
Сценарий поведения пользователя:
1. Пользователь отмечает один или несколько рецептов кликом по кнопке
   «Добавить в покупки».
2. Пользователь переходит на страницу Список покупок, там доступны все
   добавленные в список рецепты. Пользователь нажимает кнопку «Скачать список»
   и получает файл с суммированным перечнем и количеством необходимых
   ингредиентов для всех рецептов, сохранённых в «Списке покупок».
3. При необходимости пользователь может удалить рецепт из списка покупок.

Список покупок скачивается в формате txt. При скачивании списка покупок
ингредиенты в результирующем списке не дублируются;
если в двух рецептах есть сахар (в одном рецепте - 5 г, в другом - 10 г),
то в списке будет один пункт: Сахар - 15 г.
В результате список покупок выглядит так:
* Фарш (баранина и говядина) - 600 г
* Сыр плавленый - 200 г
* Лук репчатый - 50 г

### Фильтрация по тегам
При нажатии на название тега выводится список рецептов, отмеченных этим тегом.
Фильтрация может проводится по нескольким тегам. При фильтрации на странице
пользователя фильтруются только рецепты выбранного пользователя. Такой же
принцип соблюдается при фильтрации списка избранного.

## Стек технологий:
* bash
* Python 3.8
* Django 3.2
* Django REST Framework
* PostgreSQL 13.0

## Набор доступных эндпоинтов для API Foodgram:
- ```api/docs/``` - подробная документация по работе API Foodgram;
- ```api/tags/``` - получение, списка тегов (GET);
- ```api/ingredients/``` - получение, списка ингредиентов (GET);
- ```api/ingredients/``` - получение ингредиента с соответствующим id (GET);
- ```api/tags/{id}``` - получение, тега с соответствующим id (GET);
- ```api/recipes/``` - получение списка с рецептами и публикация рецептов
     (GET, POST);
- ```api/recipes/{id}``` - получение, изменение, удаление рецепта с
     соответствующим id (GET, PUT, PATCH, DELETE);
- ```api/recipes/{id}/shopping_cart/``` - добавление рецепта с соответствующим
     id в список покупок и удаление из списка (GET, DELETE);
- ```api/recipes/download_shopping_cart/``` - скачать файл со списком покупок
     shopping_cart.txt (GET);
- ```api/recipes/{id}/favorite/``` - добавление рецепта с соответствующим id в
     список избранного и его удаление (GET, DELETE).

### Операции с пользователями:
- ```api/users/``` - получение информации о пользователе и регистрация новых
     пользователей (GET, POST);
- ```api/users/{id}/``` - получение информации о пользователе (GET);
- ```api/users/me/``` - получение и изменение данных своей учётной записи.
     Доступна любым авторизованными пользователям (GET);
- ```api/users/set_password/``` - изменение собственного пароля (PATCH);
- ```api/users/{id}/subscribe/``` - подписаться на пользователя с
     соответствующим id или отписаться от него (GET, DELETE);
- ```api/users/subscribe/subscriptions/``` - просмотр пользователей на которых
     подписан текущий пользователь (GET).

### Аутентификация и создание новых пользователей:
- ```api/auth/token/login/``` - получение токена (POST);
- ```api/auth/token/logout/``` - удаление токена (POST).

## Тестирование API Foodgram
Провести тестирование API Foodgram можно с помощью Postman.
Для этого необходимо [импортировать](https://learning.postman.com/docs/integrations/available-integrations/working-with-openAPI/)
коллекции с вышеперечисленными эндпоинтами из файла ```docs/openapi-schema.yml``` в Postman.

### Алгоритм регистрации пользователей
* Пользователь отправляет POST-запрос для регистрации нового пользователя 
на эндпойнт ```/api/users/```с параметрами:
```json
{
    "email": "vpupkin@yandex.ru",
    "username": "vasya.pupkin",
    "first_name": "Вася",
    "last_name": "Пупкин",
    "password": "Qwerty123"
}
```
* Пользователь отправляет POST-запрос на на эндпоинт ```/api/token/login/``` 
c данными указанными при регистрации:
```json
{
    "email": "vpupkin@yandex.ru",
    "password": "Qwerty123"
}
```
в ответе на запрос ему приходит:
```json
{
    "auth-token": "8c02a1..."
}
```
Полученный токен добавляем в ```Postman/Collections/Foodgram/Headers/api```:

```Key:```
Authorization
```Value:```
Token 8c02a1...

И далее тестируем API Foodgram согласно документации ```api/docs/redoc```.

## Автор бэкенда
[Игорь Богомолов](https://github.com/SpaiK89)
