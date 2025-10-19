from flask import blueprints, session, request, abort, redirect, render_template, send_file
from errors import *
import traceback
import reports

app = blueprints.Blueprint('reports', __name__, url_prefix='/kek/reports')


@app.route('/api/avito/data')
def api_avito_data():
    year = request.values.get('year', 0, int)
    month = request.values.get('month', 0, int)
    ad_id = request.values.get('ad_id', 0, int)

    if ad_id != -1:
        path = reports.docs.generateReportByCity(year, month, ad_id)
    else:
        path = reports.docs.generate_report_by_all_cities(year, month)
    return send_file(path, as_attachment=True)