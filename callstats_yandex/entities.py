from sqlalchemy import Column, orm
from db import Base
from .models import *
import sqlalchemy as db
import datetime
import report_bot


class Report(Base):
    unique_calls = None
    unique_calls_8_20 = None
    source_site = None
    recalls = None
    source_yandex = None
    __tablename__ = 'reports_yandex'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    token = Column(db.String(64))
    unique_calls_json = Column(db.JSON, default=None)
    unique_calls_8_20_json = Column(db.JSON, default=None)
    source_site_json = Column(db.JSON, default=None)
    recalls_json = Column(db.JSON, default=[])
    date = Column(db.DateTime, default=datetime.datetime.now)
    source_yandex_json = Column(db.JSON, default=[])
    jivo_count = Column(db.Integer, default=0)

    @orm.reconstructor
    def init_on_load(self):
        self.unique_calls = UniqueCalls.model_validate(self.unique_calls_json)
        self.unique_calls_8_20 = UniqueCalls.model_validate(self.unique_calls_8_20_json)
        self.source_site = SourceSite.model_validate(self.source_site_json)
        try:
            self.source_yandex = SourceYandex.model_validate(self.source_yandex_json)
        except:
            self.source_yandex = SourceYandex()

        self.recalls = []
        for recall_json in self.recalls_json:
            self.recalls.append(RecallModel.model_validate(recall_json))


    def send_notify(self):
        s_recalls_0_10 = list(filter(lambda
                                         recall: recall.recall_minutes is not None and recall.recall_minutes <= 10 and recall.is_success is True,
                                     self.recalls))
        f_recalls_0_10 = list(filter(lambda
                                         recall: recall.recall_minutes is not None and recall.recall_minutes <= 10 and recall.is_success is False,
                                     self.recalls))

        s_recalls_10_20 = list(filter(lambda
                                          recall: recall.recall_minutes is not None and recall.recall_minutes > 10 and recall.recall_minutes <= 20 and recall.is_success is True,
                                      self.recalls))
        f_recalls_10_20 = list(filter(lambda
                                          recall: recall.recall_minutes is not None and recall.recall_minutes > 10 and recall.recall_minutes <= 20 and recall.is_success is False,
                                      self.recalls))

        s_recalls_20_30 = list(filter(lambda
                                          recall: recall.recall_minutes is not None and recall.recall_minutes > 20 and recall.recall_minutes <= 30 and recall.is_success is True,
                                      self.recalls))
        f_recalls_20_30 = list(filter(lambda
                                          recall: recall.recall_minutes is not None and recall.recall_minutes > 20 and recall.recall_minutes <= 30 and recall.is_success is False,
                                      self.recalls))

        s_recalls_30_40 = list(filter(lambda
                                          recall: recall.recall_minutes is not None and recall.recall_minutes > 30 and recall.recall_minutes <= 40 and recall.is_success is True,
                                      self.recalls))
        f_recalls_30_40 = list(filter(lambda
                                          recall: recall.recall_minutes is not None and recall.recall_minutes > 30 and recall.recall_minutes <= 40 and recall.is_success is False,
                                      self.recalls))

        s_recalls_40_50 = list(filter(lambda
                                          recall: recall.recall_minutes is not None and recall.recall_minutes > 40 and recall.recall_minutes <= 50 and recall.is_success is True,
                                      self.recalls))
        f_recalls_40_50 = list(filter(lambda
                                          recall: recall.recall_minutes is not None and recall.recall_minutes > 40 and recall.recall_minutes <= 50 and recall.is_success is False,
                                      self.recalls))

        s_recalls_50_60 = list(filter(lambda
                                          recall: recall.recall_minutes is not None and recall.recall_minutes > 50 and recall.recall_minutes <= 60 and recall.is_success is True,
                                      self.recalls))
        f_recalls_50_60 = list(filter(lambda
                                          recall: recall.recall_minutes is not None and recall.recall_minutes > 50 and recall.recall_minutes <= 60 and recall.is_success is False,
                                      self.recalls))

        s_recalls_60 = list(filter(lambda
                                       recall: recall.recall_minutes is not None and recall.recall_minutes > 60 and recall.is_success is True,
                                   self.recalls))
        f_recalls_60 = list(filter(lambda
                                       recall: recall.recall_minutes is not None and recall.recall_minutes > 60 and recall.is_success is False,
                                   self.recalls))

        recalls_none = list(filter(lambda recall: recall.recall_minutes is None, self.recalls))
        
        message = f"""Дата: {self.date.strftime('%d.%m.%Y %H:%M')}
        
УЗ сутки (билайн/битрикс)
{self.unique_calls.beeline_calls} / {self.unique_calls.bitrix_calls}
        
УЗ 8-22 (билайн/битрикс)
{self.unique_calls_8_20.beeline_calls} / {self.unique_calls_8_20.bitrix_calls}
        
Форма сайта (SEO/контекст)
{self.source_site.seo} / {self.source_site.context}
        
JivoSite
{self.jivo_count}
        
Яндекс.Услуги (Целевые/не целевые)
{self.source_yandex.true_calls} / {self.source_yandex.false_calls}

<b>Обработка пропущенных</b>

0-10 (П/О): <a href='https://se-bot.ru/dashboard/recalls_yandex?min=0&max=10&is_success=1&id={self.id}'>{len(s_recalls_0_10)}</a> / <a href='https://se-bot.ru/dashboard/recalls_yandex?min=0&max=10&is_success=0&id={self.id}'>{len(f_recalls_0_10)}</a>
10-20 (П/О): <a href='https://se-bot.ru/dashboard/recalls_yandex?min=10&max=10&is_success=1&id={self.id}'>{len(s_recalls_10_20)}</a> / <a href='https://se-bot.ru/dashboard/recalls_yandex?min=10&max=20&is_success=0&id={self.id}'>{len(f_recalls_10_20)}</a>
20-30 (П/О): <a href='https://se-bot.ru/dashboard/recalls_yandex?min=20&max=10&is_success=1&id={self.id}'>{len(s_recalls_20_30)}</a> / <a href='https://se-bot.ru/dashboard/recalls_yandex?min=20&max=30&is_success=0&id={self.id}'>{len(f_recalls_20_30)}</a>
30-40 (П/О): <a href='https://se-bot.ru/dashboard/recalls_yandex?min=30&max=10&is_success=1&id={self.id}'>{len(s_recalls_30_40)}</a> / <a href='https://se-bot.ru/dashboard/recalls_yandex?min=30&max=40&is_success=0&id={self.id}'>{len(f_recalls_30_40)}</a>
40-50 (П/О): <a href='https://se-bot.ru/dashboard/recalls_yandex?min=40&max=10&is_success=1&id={self.id}'>{len(s_recalls_40_50)}</a> / <a href='https://se-bot.ru/dashboard/recalls_yandex?min=40&max=50&is_success=0&id={self.id}'>{len(f_recalls_40_50)}</a>
50-60 (П/О): <a href='https://se-bot.ru/dashboard/recalls_yandex?min=50&max=10&is_success=1&id={self.id}'>{len(s_recalls_50_60)}</a> / <a href='https://se-bot.ru/dashboard/recalls_yandex?min=50&max=60&is_success=0&id={self.id}'>{len(f_recalls_50_60)}</a>
60+ (П/О): <a href='https://se-bot.ru/dashboard/recalls_yandex?min=60&max=10000&is_success=1&id={self.id}'>{len(s_recalls_60)}</a> / <a href='https://se-bot.ru/dashboard/recalls_yandex?min=60&max=10000&is_success=0&id={self.id}'>{len(f_recalls_60)}</a>
"""
        report_bot.send_message(message)
