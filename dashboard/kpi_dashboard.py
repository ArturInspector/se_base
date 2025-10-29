"""
Flask Blueprint для KPI Dashboard

URL: /dashboard/kpi
"""
from flask import Blueprint, render_template, jsonify, request, Response
from functools import wraps
from chat.ai.kpi_analyzer import KPIAnalyzer
from chat.ai.grading import ConversationGrader
import logging
import config

logger = logging.getLogger(__name__)

kpi_dashboard_bp = Blueprint('kpi_dashboard', __name__, url_prefix='/dashboard/kpi')


def check_auth(username, password):
    return username == config.Production.KPI_DASHBOARD_USER and password == config.Production.KPI_DASHBOARD_PASSWORD


def authenticate():
    return Response(
        'Access Denied', 401,
        {'WWW-Authenticate': 'Basic realm="KPI Dashboard"'}
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@kpi_dashboard_bp.route('/')
@requires_auth
def index():
    return render_template('kpi_dashboard.html')


@kpi_dashboard_bp.route('/api/metrics')
@requires_auth
def get_metrics():
    """
    API: получить метрики за период
    
    Query params:
        hours: За сколько часов (default: 24)
        variant: Вариант эксперимента (optional)
    """
    hours = int(request.args.get('hours', 24))
    variant = request.args.get('variant', None)
    
    analyzer = KPIAnalyzer()
    metrics = analyzer.get_dashboard_metrics(hours, variant)
    
    return jsonify(metrics)


@kpi_dashboard_bp.route('/api/top-issues')
@requires_auth
def get_top_issues():
    """
    API: топ проблем
    """
    hours = int(request.args.get('hours', 24))
    limit = int(request.args.get('limit', 10))
    
    analyzer = KPIAnalyzer()
    issues = analyzer.get_top_issues(hours, limit)
    
    return jsonify({"issues": issues})


@kpi_dashboard_bp.route('/api/distribution')
@requires_auth
def get_distribution():
    """
    API: распределение диалогов по результатам
    """
    hours = int(request.args.get('hours', 24))
    
    analyzer = KPIAnalyzer()
    distribution = analyzer.get_conversation_distribution(hours)
    
    return jsonify({"distribution": distribution})


@kpi_dashboard_bp.route('/api/compare')
@requires_auth
def compare_experiments():
    """
    API: A/B testing сравнение
    
    Query params:
        variant_a: Вариант A
        variant_b: Вариант B
        hours: За сколько часов
    """
    variant_a = request.args.get('variant_a', 'control')
    variant_b = request.args.get('variant_b', 'test')
    hours = int(request.args.get('hours', 24))
    
    analyzer = KPIAnalyzer()
    comparison = analyzer.compare_experiments(variant_a, variant_b, hours)
    
    return jsonify(comparison)


@kpi_dashboard_bp.route('/api/conversations')
@requires_auth
def get_conversations():
    """
    API: последние диалоги для ручной проверки
    
    Query params:
        limit: Сколько (default: 20)
        min_score: Минимальный score (фильтр плохих)
        max_score: Максимальный score (фильтр хороших)
    """
    limit = int(request.args.get('limit', 20))
    min_score = request.args.get('min_score', type=float)
    max_score = request.args.get('max_score', type=float)
    
    analyzer = KPIAnalyzer()
    conversations = analyzer.get_recent_conversations(
        limit=limit,
        min_score=min_score,
        max_score=max_score
    )
    
    return jsonify({"conversations": conversations})


@kpi_dashboard_bp.route('/api/realtime')
@requires_auth
def realtime_stats():
    """
    API: реалтайм статистика за последний час
    """
    analyzer = KPIAnalyzer()
    
    # Метрики за последний час
    last_hour = analyzer.get_dashboard_metrics(hours=1)
    # Метрики за предыдущий час для сравнения
    prev_hour = analyzer.get_dashboard_metrics(hours=2)  # TODO: нужна логика для предыдущего часа
    
    return jsonify({
        "current": last_hour,
        "trend": {
            "conversion": "up" if last_hour['deals']['conversion_rate'] > 50 else "down",
            "quality": "up" if last_hour['quality']['avg_score'] > 0.7 else "down"
        }
    })


@kpi_dashboard_bp.route('/logs')
@requires_auth
def logs_page():
    """
    Страница просмотра логов
    """
    return render_template('logs_viewer.html')


@kpi_dashboard_bp.route('/api/logs')
@requires_auth
def get_logs():
    """
    API: получить логи из journalctl
    
    Query params:
        service: Название сервиса (pepsiai_se_base, etc)
        lines: Количество строк (default: 100)
    """
    import subprocess
    
    service = request.args.get('service', 'pepsiai_se_base')
    lines = int(request.args.get('lines', 100))
    
    try:
        cmd = ['journalctl', '-u', service, '-n', str(lines), '--no-pager']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return jsonify({
                "error": f"journalctl error: {result.stderr}",
                "logs": []
            })
        
        logs = result.stdout.strip().split('\n')
        
        return jsonify({
            "service": service,
            "lines_count": len(logs),
            "logs": logs
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout reading logs", "logs": []})
    except Exception as e:
        logger.error(f"Error reading journalctl for {service}: {e}")
        return jsonify({"error": str(e), "logs": []})

