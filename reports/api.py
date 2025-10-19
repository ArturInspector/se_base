import avito
import cities
import members


def get_city_by_avito_id(ad_id):
    data = avito.api.get_ad_by_id(ad_id)
    print(data)
    city_name = data['url'].split('/')[3]
    result = cities.api.get_address_by_dadata(city_name)
    city = cities.api.get_city_by_fias(result['fias_id'])
    return city


def get_avito_report_by_ad(item_id, date_from, date_to, load_members=False):
    data = avito.api.get_stats([item_id], date_from, date_to)

    if load_members is False:
        return {'data': data, 'wmembers': None}

    members_list = members.api.get_members_by_avito_chat_id(item_id)
    members_list = list(filter(
        lambda member: member.create_date >= date_from and member.create_date <= date_to, members_list
    ))

    return {'data': data, 'wmembers': members_list}


def get_avito_report(date_from, date_to):
    ads = {}
    ad_ids = []
    cnt = 0
    for ad in avito.api.get_ads(111, 'active,removed,old,rejected,blocked'):
        ads[ad['id']] = {
            'id': ad['id'],
            'title': ad['title'],
            'url': ad['url'],
        }
        ad_ids.append(ad['id'])

    data = []
    for i in range(0, len(ad_ids), 100):
        data.extend(avito.api.get_stats(ad_ids[i: i + 100], date_from, date_to)['result']['items'])

    result_method = []

    cities_list = cities.api.get_cities()

    for item in data:
        if len(item['stats']) == 0:
            continue
        print(item['itemId'])
        ad = ads[item['itemId']]
        city_name = ad['url'].split('/')[3]

        city_name = city_name.replace('_', ' ')

        if city_name == 'lyubertsy':
            city_name = 'Люберцы'
        if city_name == 'schelkovo':
            city_name = 'Щёлково'
        if city_name == 'balashov':
            city_name = 'Балашов'
        if city_name == 'volginskiy':
            city_name = 'Вольгинский'
        if city_name == 'moskovskaya_oblast_moskovskiy':
            city_name = 'Московская область Московский'
        if city_name == 'osinovo':
            city_name = 'Осиново'
        if city_name == 'sankt-peterburg_kolpino':
            city_name = 'Санкт-Петербург Колпино'
        if city_name == 'sankt-peterburg_pushkin':
            city_name = 'Санкт-Петербург Пушкин'
        if city_name == 'podolsk':
            city_name = 'Подольск'
        if city_name == 'moskva_zelenograd':
            city_name = 'Зеленоград'
        if city_name == 'moskovskaya_oblast_krasnogorsk':
            city_name = 'Красногорск'
        if city_name == 'ulyanovsk':
            city_name = 'Ульяновск'
        if city_name == 'ryazan':
            city_name = 'Рязань'
        if city_name == 'irkutsk':
            city_name = 'Иркутск'
        if city_name == 'norilsk':
            city_name = 'Норильск'
        if city_name == 'egorevsk':
            city_name = 'Егорьевск'
        if city_name == 'tyumen':
            city_name = 'Тюмень'
        if city_name == 'zelenodolsk':
            city_name = 'Зеленодольск'
        if city_name == 'fryazino':
            city_name = 'Фрязино'
        if city_name == 'dolgoprudnyy':
            city_name = 'Долгопрудный'
        if city_name == 'mozhaysk':
            city_name = 'Можайск'
        if city_name == 'elektrostal':
            city_name = 'Электросталь'
        if city_name == 'lobnya':
            city_name = 'Лобня'
        if city_name == 'yaroslavl':
            city_name = 'Ярославль'
        if city_name == 'moskovskaya_oblast_chehov':
            city_name = 'Чехов'
        if city_name == 'mytischi':
            city_name = 'Мытищи'
        if city_name == 'moskovskaya_oblast_dubna':
            city_name = 'Дубна'
        if city_name == 'tolyatti':
            city_name = 'Тольятти'
        if city_name == 'bataysk':
            city_name = 'Батайск'
        if city_name == 'mineralnye_vody':
            city_name = 'Минеральные воды'
        if city_name == 'velikiy_novgorod':
            city_name = 'Великий новгород'
        if city_name == 'nalchik':
            city_name = 'Нальчик'
        if city_name == 'almetevsk':
            city_name = 'Альметьевск'
        if city_name == 'zhukovskiy':
            city_name = 'Жуковский'
        if city_name == 'salsk':
            city_name = 'Сальск'
        if city_name == 'novyy_urengoy':
            city_name = 'Новый уренгой'
        if city_name == 'pyatigorsk':
            city_name = 'Пятигорск'
        if city_name == 'nizhniy_tagil':
            city_name = 'Нижний тагил'
        if city_name == 'novoaltaysk':
            city_name = 'Новоалтайск'
        if city_name == 'novorossiysk':
            city_name = 'Новороссийск'
        if city_name == 'bryansk':
            city_name = 'Брянск'
        if city_name == 'naberezhnye_chelny':
            city_name = 'Набережные челны'
        if city_name == 'noyabrsk':
            city_name = 'Ноябрьск'
        if city_name == 'krasnoyarsk':
            city_name = 'Красноярск'
        if city_name == 'kirovskaya_oblast_kirov':
            city_name = 'Киров'
        if city_name == 'elista':
            city_name = 'Элиста'
        if city_name == 'nizhniy_novgorod':
            city_name = 'Нижний новгород'
        if city_name == 'yaroslavl':
            city_name = 'Ярославль'
        if city_name == 'orel':
            city_name = 'Орёл'
        if city_name == 'gryazi':
            city_name = 'Грязи'
        if city_name == 'chelyabinsk':
            city_name = 'Челябинск'
        if city_name == 'fryazino':
            city_name = 'Фрязино'
        if city_name == 'bryansk':
            city_name = 'Брянск'
        if city_name == 'bryansk':
            city_name = 'Брянск'
        city = cities.api.get_city(city_name, cities_list, True)
        if city is None:
            print(city_name, 'continue')
            continue
        # wmembers = DBManager.get_wmembers_by_data(item['itemId'], date_from, date_to)
        members_list = members.api.get_members_by_city_id(city.id)
        members_list = list(filter(
            lambda member: member.create_date >= date_from and member.create_date <= date_to, members_list
        ))
        ad['stats'] = item['stats']
        ad['city'] = city
        ad['wmembers'] = members_list
        result_method.append(ad)

    res = []
    cities_list = {}

    for ad in result_method:
        key = str(ad['city'].id)
        if cities_list.get(key) is None:
            cities_list[key] = []
        cities_list[key].append(ad)

    for city_id in cities_list:
        cities_list[city_id].sort(key=lambda ad: len(ad['stats']), reverse=True)
        res.append(cities_list[city_id][0])

    for ad in res:
        print(ad)
    return res