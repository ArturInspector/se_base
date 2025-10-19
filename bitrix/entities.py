import datetime
import dateutil.parser
import utils
import bitrix.utils
import bitrix.api


class BitrixDeal:
    DEP_OTHER = 0
    DEP_PHYSICAL = 1
    DEP_JUR = 2
    DEP_CALL = 3

    DEPARTMENTS = ['Остальные', 'ОП Физ.лица', 'ОП Юр.Лица', 'Колл-Центр']

    SOURCE_NONE = 0
    SOURCE_CALL = 1
    SOURCE_SITE_CALL = 2
    SOURCE_LEAD_BACK = 3
    SOURCE_EMAIL = 4
    SOURCE_AVITO = 5
    SOURCES = ['Неизвестно', 'Звонок', 'Звонок с сайта', 'LeadBack', 'Email', 'Avito']

    def __init__(self, data, status):
        self.data = data
        self.id = data['ID']
        self.title = data['TITLE']
        self.type = data['TYPE_ID']
        self.stage_id = data['STAGE_ID']
        self.lead_id = data['LEAD_ID']
        self.member_id = int(data['ASSIGNED_BY_ID'])
        self.comment = data['COMMENTS']
        self.profit = float(data['OPPORTUNITY']) if data['OPPORTUNITY'] is not None else 0

        if data.get('UF_CRM_1623928624') is not None:
            if len(data['UF_CRM_1623928624']) > 0:
                sum_job = float(str(data['UF_CRM_1623928624']).split('|')[0])
                self.profit -= sum_job

        self.begin_date = dateutil.parser.isoparse(data['BEGINDATE'])
        # self.begin_date = datetime.datetime.fromisoformat(data['BEGINDATE'])
        try:
            # self.close_date = datetime.datetime.fromisoformat(data['CLOSEDATE'])
            self.close_date = dateutil.parser.isoparse(data['CLOSEDATE'])
        except:
            self.close_date = None

        # self.create_date = datetime.datetime.fromisoformat(data['DATE_CREATE'])
        # self.modify_date = datetime.datetime.fromisoformat(data['DATE_MODIFY'])
        self.create_date = dateutil.parser.isoparse(data['DATE_CREATE'])
        self.modify_date = dateutil.parser.isoparse(data['DATE_MODIFY'])

        self.last_activity = None
        try:
            self.last_activity = dateutil.parser.isoparse(data['LAST_ACTIVITY_TIME'])
        except:
            pass

        self.opened = True
        if data['OPENED'] != "Y":
            self.opened = False

        self.closed = True
        if data['CLOSED'] != "Y":
            self.closed = False

        self.category_id = int(data['CATEGORY_ID'])
        self.source_id = data['SOURCE_ID']
        self.source_description = data['SOURCE_DESCRIPTION']

        self.source = 0
        if self.source_id == 'EMAIL':
            self.source = BitrixDeal.SOURCE_EMAIL
        if self.source_id == 'Avito':
            self.source = BitrixDeal.SOURCE_AVITO
        if self.title == 'Заявка с сайта':
            self.source = BitrixDeal.SOURCE_SITE_CALL
        if 'LeadBack' in self.title:
            self.source = BitrixDeal.SOURCE_LEAD_BACK
        if '@' in self.title:
            self.source = BitrixDeal.SOURCE_EMAIL

        if self.source_description is not None:
            if '+7' in self.source_description or 'АТС' in self.source_description:
                self.source = BitrixDeal.SOURCE_CALL

        self.source_str = BitrixDeal.SOURCES[self.source]

        self.department = 0

        if self.category_id == 4:
            self.department = 3
        if self.category_id == 8:
            self.department = 2
        if self.category_id == 10:
            self.department = 1

        self.status_type = 0
        if status['SEMANTICS'] == 'S':
            self.status_type = 1
        if status['SEMANTICS'] == 'F':
            self.status_type = -1

        self.status = status['NAME']
        self.status_obj = status
        self.department_str = BitrixDeal.DEPARTMENTS[self.department]

        if self.status == 'Спам (реклама)':
            self.status_type = -2

        self.transfer = 0
        if self.department == 3 and data['UF_CRM_1626165103409'] is not None:
            transfer = int(data['UF_CRM_1626165103409']) if len(data['UF_CRM_1626165103409']) > 0 else 0
            if transfer == 1832:
                self.transfer = BitrixDeal.DEP_PHYSICAL
                self.department = BitrixDeal.DEP_PHYSICAL
            if transfer == 1834:
                self.transfer = BitrixDeal.DEP_JUR
                self.department = BitrixDeal.DEP_JUR

        if self.department == BitrixDeal.DEP_JUR and self.status == 'В клиентском сервисе':
            self.status_type = 1

        self.check = False
        if self.close_date is not None:
            if self.department == BitrixDeal.DEP_JUR and utils.compare_date(self.create_date, self.close_date) is False:
                self.check = True

        try:
            self.services = bitrix.utils.get_services(data['UF_CRM_1623928173'])
        except:
            self.services = []

        self.complete = True
        if self.department == BitrixDeal.DEP_CALL and self.status_type >= 0:
            self.complete = False

        self.calls = []

    def __repr__(self):
        return '#{} [StatusType: {} {}₽] [Status: {}] [Department: {}] [Source: {} {} {}]  {} {}'.format(
            self.id, self.status_type, self.profit, self.status, BitrixDeal.DEPARTMENTS[self.department],
            BitrixDeal.SOURCES[self.source], self.source_str, self.source_description, self.create_date,
            self.close_date)

    def get_max_date(self):
        result = None
        for key in self.data:
            try:
                date = dateutil.parser.isoparse(self.data[key])
                if result is None:
                    result = date
                else:
                    if date > result:
                        result = date
            except Exception as e:
                continue
        return result

    def get_phone(self):
        contact = bitrix.api.get_contact_by_id(self.data['CONTACT_ID'])
        phone = ''

        for row in contact['PHONE']:
            phone += '{}, '.format(row['VALUE'])

        if len(phone) > 0:
            phone = phone[:-2]
        return phone

    def get_description(self):
        header = 'Сделка выиграна' if self.status_type == 1 else 'Сделка проиграна'

        contact = bitrix.api.get_contact_by_id(self.data['CONTACT_ID'])
        name = contact.get('NAME', 'Не указано')
        phone = ''

        try:
            for row in contact['PHONE']:
                phone += '{}, '.format(row['VALUE'])
        except:
            pass

        if len(phone) > 0:
            phone = phone[:-2]

        message = f"""{header} #{self.id}

{self.title}
Статус: {self.status}
Источник: {self.source_description}
Услуги: {self.services}
Комментарий: {self.comment}

Сделка:
https://standartexpress.bitrix24.ru/crm/deal/details/{self.id}/

Контакт:
Имя: {name}
Телефон: {phone}
"""
        return message


class Call:
    def __init__(self, date, link):
        self.date = date
        self.link = link

    def __repr__(self):
        return 'Звонок от {}\n{}'.format(self.date.strftime('%d.%M.%Y %H:%M'), self.link)