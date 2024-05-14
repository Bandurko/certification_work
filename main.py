from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
from bs4 import BeautifulSoup
import time
import numpy as np
from pydantic import BaseModel
from sklearn.linear_model import LinearRegression


class Item(BaseModel):
    distr: str
    flat_area: float
    flat_rooms: int


app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h3>REST микросервис прогнозирование цены на недвижимость</h3>"

@app.get("/items/{distr}")
async def read_item(distr: str, flat_area: float, flat_rooms: int):

    # Задаем нужный район города
    # distr: str
    # Задаем площадь квартиры (кв. м)
    # flat_area: float
    # Задаем кол-во комнат в квартире
    # flat_rooms: int

    floats = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.133 Safari/537.36"
    }

    # Задаем количество страниц сайта Циан со ссылками на квартиры (ОСТОРОЖНО! Может ссработать защита от парсинга (Ошибка 429).)
    for i in range(2, 4):

        url = f'https://vladivostok.cian.ru/cat.php?currency=2&deal_type=sale&engine_version=2&offer_type=flat&p={i}&region=4701&room1=1&room2=1&room3=1&room4=1&room5=1&type=4'

        q = requests.get(url=url, headers=headers)
        result = q.text

        soup = BeautifulSoup(result, 'lxml')
        links = soup.find_all(class_='_93444fe79c--link--eoxce')

        for link in links:
            float_page_link = link.get('href')
            floats.append(float_page_link)

        time.sleep(2)  # "Защита" от определения парсинга

    sorter = []
    for link in floats:
        if link not in sorter:
            sorter.append(link)

    floats = sorter

    time.sleep(2)  # "Защита" от определения парсинга

    with open('links.txt', 'w', encoding='utf-8') as file:  # Создаем файл со ссылками на квартиры (построчно)
        for line in floats:
            file.write(f'{line}\n')


    with open('links.txt') as file:
        lines = [line.strip() for line in file.readlines()]

        count = 0

        area = []  # Задаем список площадей квартир
        rooms = []  # Задаем список кол-ва комнат квартир
        price = []  # Задаем список цен на квартиры

        for line in lines:  # Построчно считывем ссылки из файла
            print(line)
            q = requests.get(line, headers=headers)
            result = q.text

            soup = BeautifulSoup(result, 'lxml')

            print(q.status_code)  # Печатаем ответ сервера на запрос

            address = soup.find('meta', property='og:description')  # Парсим полный адрес

            words = address['content'].split()
            find_word = "р-н"
            index_word = -1
            if find_word in words:
                index_word = words.index(find_word)
            district = (words[index_word + 1][:-1:])  # Парсим район в котором находится квартира
            time.sleep(2)  # "Защита" от определения парсинга
            if district == distr:  # Определяем совпадает-ли район, где находится квартира с заданным районом

                rooms_and_area = soup.find('div', {'data-name': 'OfferTitleNew'})

                for el in rooms_and_area:
                    title = el.text.replace(" ", "")


                    if "Продается" in title:
                        idk1 = title[title.find("Продается") + 9:]
                        r = int(idk1[:idk1.find("-")])  # Определяем кол-во комнат
                        rooms.append(r)  # Добавляем кол-во комнат в список
                    else:
                        continue

                    if "квартира," in title:
                        idk2 = title[title.find("квартира,") + 9:]
                        a = float((idk2[:idk2.find("м²")]).replace(',', '.'))  # Определяем площадь квартиры
                        area.append(a)  # Добавляем площадь квартиры в список
                    else:
                        continue

                elements_with_class_example = soup.find_all('div', {'data-name': 'ObjectFactoidsItem'})

                for element in elements_with_class_example:
                    element.text.replace(" ", "")


                price_parse = (soup.find('div', {'data-testid': 'price-amount'})).text[:-2:]

                p = int("".join(price_parse.split()))  # Определяем стоимость квартиры
                price.append(p)  # Добавляем стоимость квартиры в список

                time.sleep(2)  # "Защита" от определения парсинга

            else:
                continue

            count += 1
            time.sleep(3)  # "Защита" от определения парсинга
            print(f'#{count}: {line} is done!')


            if count % 11 == 0:
                time.sleep(7)  # "Защита" от определения парсинга
            else:
                continue

    # ========== LinearRegression ============

    # Площадь квартир в квадратных метрах
    X_area = np.array(area)
    # Количество комнат в квартире
    X_rooms = np.array(rooms)
    # Цены на недвижимость
    y = np.array(price)
    # Создаем объект модели линейной регрессии
    model = LinearRegression()
    # Обучаем модель на данных
    # Объединяем два предиктора в одну матрицу
    X = np.column_stack((X_area, X_rooms))
    model.fit(X, y)
    # Теперь модель обучена и может делать прогноз
    # Давайте спрогнозируем цену для квартиры с заданной площадью и кол-вом комнат
    # Задаем площадь квартиры (задается в GET HTTP запросе)
    house_area = flat_area
    # Задаем кол-во комнат в квартире (задается в GET HTTP запросе)
    house_rooms = flat_rooms
    predic_price = model.predict(np.array([[house_area, house_rooms]]))
    predicted_price = float(f'{predic_price[0]:.2f}')

    return {"predicted_price": predicted_price}
