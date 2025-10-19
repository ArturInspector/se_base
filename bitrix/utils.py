SERVICES_LIST = {'1714': 'ПРР', '1716': 'АУТСОРСИНГ', '1818': 'ТАКЕЛАЖ', '1820': 'ПЕРЕЕЗДЫ ОФИСОВ', '1822': 'ПЕРЕЕЗДЫ ФИЗИКИ', '1824': 'ГРУЗОПЕРЕВОЗКИ ГОРОД', '1826': 'ГРУЗОПЕРЕВОЗКИ МЕЖГОРОД', '1828': 'РАЗНОРАБОЧИЕ', '1830': 'СПЕЦТЕХНИКА', '1864': 'ВОВОЗ ТБО', '1862': 'НЕИЗВЕСТНЫЙ ЗАПРОС'}


def get_services(services_arr):
    result = ''
    for service_id in services_arr:
        service = SERVICES_LIST.get(str(service_id))
        if service is not None:
            result += '{}, '.format(service)
    if len(result) > 0:
        result = result[:-2]
    return result