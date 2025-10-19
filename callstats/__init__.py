from db import Session
from .entities import *
from .models import *
from typing import List, Union
from uuid import uuid4
import callstats.beeline
import callstats.leadback
import callstats_yandex
import datetime
import bitrix
import utils
import traceback
import avito_old
import json


def get_report_by_id(report_id) -> Union[Report, None]:
    with Session() as session:
        report = session.query(Report).get(report_id)
    return report


def get_report_by_token(token) -> Union[Report, None]:
    with Session() as session:
        report = session.query(Report).filter(Report.token == token).first()
    return report


def get_reports() -> List[Report]:
    with Session() as session:
        reports_list = session.query(Report).all()
    return reports_list


def get_recalls(calls_list, bitrix_deals) -> List[RecallModel]:
    recalls_list: List[RecallModel] = []
    bitrix_statuses = bitrix.api.get_statuses_full()

    user_phones = []

    for i in range(len(calls_list)):
        call = calls_list[i]
        if call['direction'] != 'INBOUND':
            continue
        if call['status'] != 'MISSED':
            continue
        if call['abonent']['extension'] not in ['217', '233', '238', '240']:
            continue
        try:
            phone = call['phone_from']
        except:
            continue

        if phone in user_phones:
            continue

        call_date = datetime.datetime.fromtimestamp(call['startDate'] / 1000)
        recall = get_recall(phone, calls_list[i + 1:])
        bitrix_deal = get_bitrix_deal_by_phone(phone, bitrix_deals)

        recall_obj = RecallModel(phone=phone, call_time=call_date)

        if recall is not None:
            recall_time = datetime.datetime.fromtimestamp(recall['startDate'] / 1000)
            recall_obj.recall_time = recall_time
            recall_obj.recall_minutes = (recall_time.timestamp() - call_date.timestamp()) // 60

        if bitrix_deal is not None:
            status = bitrix_statuses[bitrix_deal['STAGE_ID']]
            bitrix_deal['status'] = status
            recall_obj.bitrix_deal = bitrix_deal
            if status['SEMANTICS'] in ['S', None]:
                recall_obj.is_success = True

        user_phones.append(phone)
        recalls_list.append(recall_obj)
    return recalls_list



def get_recall(phone, calls_list):
    for call in calls_list:
        if call['direction'] != 'OUTBOUND':
            continue
        if call['phone_to'] != phone:
            continue
        return call
    return None


def get_bitrix_deal_by_phone(phone, bitrix_deals):
    phone = utils.telephone(phone)
    for deal in bitrix_deals:
        deal_phone = utils.telephone(deal['TITLE'])
        if deal_phone == phone:
            return deal
    return None


def get_unique_calls(calls_list, bitrix_deals, min_hour=None, max_hour=None) -> UniqueCalls:
    beeline_calls = []
    for call in calls_list:
        date = datetime.datetime.fromtimestamp(call['startDate'] / 1000)
        if call['direction'] != 'INBOUND':
            continue
        try:
            if call['phone_from'] in beeline_calls:
                continue
        except:
            continue
        if call['abonent']['extension'] not in ['217', '233', '238', '240']:
            continue
        if min_hour is not None and date.hour < min_hour:
            continue
        if max_hour is not None and date.hour >= max_hour:
            continue

        beeline_calls.append(call['phone_from'])

    call_centre_deals = list(filter(lambda order: order['CATEGORY_ID'] == '4' and order['STAGE_ID'] != 'C4:57', bitrix_deals))
    if min_hour is not None and max_hour is not None:
        result = []
        for deal in call_centre_deals:
            date = datetime.datetime.fromisoformat(deal['DATE_CREATE'][:-6])
            if date.hour >= min_hour and date.hour < max_hour:
                result.append(deal)
        call_centre_deals = result
    return UniqueCalls(beeline_calls=len(beeline_calls), bitrix_calls=len(call_centre_deals))


def get_source_site(bitrix_deals) -> SourceSite:
    seo = 0
    context = 0

    for deal in bitrix_deals:
        if deal['UTM_SOURCE'] == 'yandex' and deal['UTM_MEDIUM'] == 'cpc':
            context += 1
        lead = deal['LEAD']
        if lead is None:
            continue
        if lead['SOURCE_ID'] == 'Заявка с сайта' and deal['UTM_MEDIUM'] != 'cpc':
            seo += 1
    return SourceSite(seo=seo, context=context)


def get_source_leadback(leadback_calls) -> SourceLeadBack:
    seo = 0
    context = 0

    for call in leadback_calls:
        if call['visit_source'] == 'direct':
            seo += 1
        elif call['visit_source'] == 'cpc':
            context += 1

    return SourceLeadBack(seo=seo, context=context)


def get_report():
    now = datetime.datetime.now()

    beeline_calls_list = callstats.beeline.get_calls(now)
    beeline_calls_list.sort(key=lambda call: call['startDate'])
    # beeline_calls_list = []

    leadback_calls = callstats.leadback.get_calls(now)
    source_leadback = get_source_leadback(leadback_calls)

    bitrix_deals = bitrix.api.get_deals_by_date(now)
    bitrix_leads = bitrix.api.get_leads_by_date(now)

    source_yandex = SourceYandex()
    g_phones = callstats_yandex.gtable.get_phones()

    statuses = bitrix.api.get_statuses_full()

    for deal in bitrix_deals:
        if deal['SOURCE_ID'] in g_phones:
            print(deal['ID'], deal['STAGE_ID'], statuses[deal['STAGE_ID']]['NAME'])
            if deal['STAGE_ID'] in ['LOSE', '3', '4', '5', '22', '28', '23', '29', '26', '33', '34', 'C4:LOSE', 'C4:4', 'C4:5', 'C4:6', 'C4:56', 'C4:57', 'C4:59']:
                source_yandex.false_calls += 1
            else:
                source_yandex.true_calls += 1

    avito_calls = avito_old.api.get_calls_by_date(now)
    avito_chats = avito_old.api.get_today_messages()

    source_avito = SourceAvito(calls=len(avito_calls), chats=len(avito_chats))

    for deal in bitrix_deals:
        deal['LEAD'] = utils.get_entity_by_key('ID', deal['LEAD_ID'], bitrix_leads)

    unique_calls = get_unique_calls(calls_list=beeline_calls_list, bitrix_deals=bitrix_deals)
    unique_calls_8_20 = get_unique_calls(calls_list=beeline_calls_list, bitrix_deals=bitrix_deals, min_hour=8, max_hour=20)

    sources = {}
    for deal in bitrix_deals:
        lead = deal['LEAD']
        if lead is None:
            continue
        key = lead['SOURCE_ID']
        if key is None:
            continue

        if sources.get(key) is None:
            sources[key] = 1
        else:
            sources[key] += 1

    source_site = get_source_site(bitrix_deals)

    recalls_models = get_recalls(beeline_calls_list, bitrix_deals)

    token = str(uuid4())

    report = Report(
        token=token,
        unique_calls_json=unique_calls.dict(),
        unique_calls_8_20_json=unique_calls_8_20.dict(),
        source_site_json=source_site.dict(),
        source_leadback_json=source_leadback.dict(),
        source_avito_json=source_avito.dict(),
        source_yandex_json=source_yandex.dict(),
        recalls_json=[json.loads(json.dumps(recall.dict(), default=utils.json_serial_report)) for recall in recalls_models]
    )
    with Session() as session:
        session.add(report)
        session.commit()

    report = get_report_by_token(token)
    print('send_notify')
    report.send_notify()