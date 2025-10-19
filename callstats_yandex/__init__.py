from db import Session
from .entities import *
from .models import *
from typing import List, Union
from uuid import uuid4
import callstats.beeline
import callstats.leadback
import datetime
import bitrix
import utils
import traceback
import avito_old
import json
import callstats_yandex.gtable


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
        if call['abonent']['extension'] not in ['239', '260']:
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
        if call['abonent']['extension'] not in ['239', '260']:
            continue
        if min_hour is not None and date.hour < min_hour:
            continue
        if max_hour is not None and date.hour >= max_hour:
            continue

        beeline_calls.append(call['phone_from'])

    call_centre_deals = list(filter(lambda order: order['CATEGORY_ID'] == '0', bitrix_deals))
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
        if 'Заявка с сайта' in lead['SOURCE_ID'] and deal['UTM_MEDIUM'] != 'cpc':
            seo += 1
    return SourceSite(seo=seo, context=context)


def get_report():
    now = datetime.datetime.now()

    beeline_calls_list = callstats.beeline.get_calls(now)
    beeline_calls_list.sort(key=lambda call: call['startDate'])
    # beeline_calls_list = []

    all_bitrix_deals = bitrix.api.get_deals_by_date(now)
    bitrix_leads = bitrix.api.get_leads_by_date(now)
    bitrix_deals = []

    g_phones = callstats_yandex.gtable.get_phones()
    source_yandex = SourceYandex()
    jivo_count = 0

    statuses = bitrix.api.get_statuses_full()

    for deal in all_bitrix_deals:
        if deal['CATEGORY_ID'] != '0':
            continue
        bitrix_deals.append(deal)

        if deal['SOURCE_DESCRIPTION'] is not None and 'Jivo' in deal['SOURCE_DESCRIPTION']:
            jivo_count += 1

        if deal['SOURCE_ID'] in g_phones:
            print(deal['ID'], statuses[deal['STAGE_ID']])
            if deal['STAGE_ID'] in ['LOSE', '3', '4', '5', '22', '28', '23', '29', '26', '33', '34']:
                source_yandex.false_calls += 1
            else:
                source_yandex.true_calls += 1


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
        unique_calls_json=unique_calls.model_dump(),
        unique_calls_8_20_json=unique_calls_8_20.model_dump(),
        source_site_json=source_site.model_dump(),
        source_yandex_json=source_yandex.model_dump(),
        jivo_count=1,
        recalls_json=[json.loads(json.dumps(recall.model_dump(), default=utils.json_serial_report)) for recall in recalls_models]
    )
    with Session() as session:
        session.add(report)
        session.commit()

    print('aga')
    report = get_report_by_token(token)
    print('send_notify')
    report.send_notify()