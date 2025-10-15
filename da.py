# vacancy_app.py
# Полное приложение для поиска вакансий HH.ru + SuperJob
# Для PythonAnywhere

from flask import Flask, request, Response, render_template_string
import requests
import json

app = Flask(__name__)

# ============ ВШИТЫЕ CREDENTIALS ============
SUPERJOB_APP_ID = "4014"
SUPERJOB_SECRET_KEY = "v3.r.138979256.3b5b15795a107a49a55e7f4e5eed1857dfe78cde.dda83a292af5754f027da2f0c96152b9b34f0dee"

# ============ ПРОКСИ ДЛЯ SUPERJOB API ============
@app.route('/proxy')
def proxy():
    target_url = request.args.get('url')
    api_key = request.args.get('key', SUPERJOB_SECRET_KEY)
    
    if not target_url:
        return {'error': 'URL parameter required'}, 400
    
    try:
        headers = {
            'X-Api-App-Id': api_key,
            'User-Agent': 'VacancyParser/1.0'
        }
        
        response = requests.get(target_url, headers=headers, timeout=30)
        
        return Response(
            response.content,
            status=response.status_code,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json; charset=utf-8'
            }
        )
    except Exception as e:
        return {'error': str(e)}, 500

# ============ OAUTH CALLBACK ============
@app.route('/callback')
def callback():
    return render_template_string(CALLBACK_HTML)

# ============ ГЛАВНАЯ СТРАНИЦА ============
@app.route('/')
def index():
    # Вставляем credentials в HTML через JavaScript
    html = MAIN_HTML.replace(
        '// CREDENTIALS_PLACEHOLDER',
        f'''
        // Автоматическая авторизация
        localStorage.setItem('sj_credentials', JSON.stringify({{
            client_id: '{SUPERJOB_APP_ID}',
            client_secret: '{SUPERJOB_SECRET_KEY}'
        }}));
        localStorage.setItem('sj_secret_key', '{SUPERJOB_SECRET_KEY}');
        '''
    )
    return render_template_string(html)

# ============ HTML CALLBACK СТРАНИЦЫ ============
CALLBACK_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SuperJob OAuth Callback</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            text-align: center;
        }
        .container {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        h1 { margin: 0 0 20px 0; }
        .spinner {
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄 Обработка авторизации...</h1>
        <div class="spinner"></div>
        <p id="message">Пожалуйста, подождите</p>
    </div>
    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const error = urlParams.get('error');
        const messageEl = document.getElementById('message');

        if (error) {
            messageEl.textContent = `❌ Ошибка: ${error}`;
            setTimeout(() => window.close(), 3000);
        } else if (code) {
            messageEl.textContent = `✅ Код получен: ${code.substring(0, 10)}...`;
            localStorage.setItem('sj_auth_code', code);
            setTimeout(() => {
                messageEl.textContent = '✅ Готово! Можно закрыть это окно.';
                if (window.opener) {
                    window.opener.postMessage({ type: 'sj_auth_success', code }, '*');
                    setTimeout(() => window.close(), 1000);
                } else {
                    messageEl.textContent = '✅ Вернитесь на главную страницу';
                }
            }, 1000);
        } else {
            messageEl.textContent = '⚠️ Не получен код авторизации';
        }
    </script>
</body>
</html>
'''

# ============ ГЛАВНЫЙ HTML ============
MAIN_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вакансии - HH.ru и SuperJob</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #f0f4f8;
            color: #333;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            text-align: center;
            color: #7f8c8d;
            font-size: 16px;
            margin-bottom: 30px;
        }

        .auth-status {
            background: linear-gradient(135deg, #ff8800 0%, #ff6b35 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .auth-status.logged-out {
            background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
        }
        .auth-info { flex: 1; }
        .auth-info h3 { margin: 0 0 5px 0; }
        .auth-info p { margin: 0; opacity: 0.9; font-size: 14px; }
        .auth-actions button {
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid white;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
        }
        .auth-actions button:hover {
            background: white;
            color: #ff8800;
        }

        .source-selector {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 8px;
            margin: 20px 0;
            color: white;
        }
        .source-selector h3 {
            margin: 0 0 15px 0;
            text-align: center;
        }
        .source-options {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        .source-option {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            padding: 20px 30px;
            cursor: pointer;
            transition: all 0.3s;
            min-width: 200px;
            text-align: center;
        }
        .source-option:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateY(-3px);
        }
        .source-option.active {
            background: white;
            color: #667eea;
            border-color: white;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        }
        .source-option input[type="radio"] { display: none; }
        .source-option .source-logo {
            font-size: 32px;
            margin-bottom: 10px;
        }
        .source-option .source-name {
            font-weight: bold;
            font-size: 18px;
        }

        .filters-box {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 25px;
            margin: 20px 0;
            border: 1px solid #e9ecef;
        }
        .filter-row {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 20px;
            align-items: flex-start;
        }
        .filter-group {
            flex: 1;
            min-width: 250px;
        }
        .filter-group label {
            display: block;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
            font-size: 14px;
        }
        .filter-group small {
            color: #7f8c8d;
            font-weight: normal;
            display: block;
            margin-top: 4px;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 15px;
            transition: border 0.3s;
            font-family: inherit;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #1a73e8;
        }

        .city-selector { position: relative; }
        .city-dropdown {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            background: white;
            cursor: pointer;
            font-size: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .city-dropdown:hover { border-color: #1a73e8; }
        .city-options {
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 2px solid #1a73e8;
            border-radius: 6px;
            margin-top: 5px;
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .city-options.active { display: block; }
        .city-option {
            padding: 10px 15px;
            cursor: pointer;
            transition: background 0.2s;
            border-bottom: 1px solid #f0f0f0;
        }
        .city-option:hover { background: #f0f8ff; }
        .city-option input[type="checkbox"] { margin-right: 10px; }

        .checkbox-group {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 15px;
        }
        .checkbox-group label {
            display: flex;
            align-items: center;
            cursor: pointer;
            font-weight: normal;
        }
        .checkbox-group input[type="checkbox"] {
            margin-right: 6px;
            cursor: pointer;
        }

        .exclusion-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
            min-height: 40px;
            padding: 8px;
            border: 2px dashed #ddd;
            border-radius: 6px;
        }
        .exclusion-tag {
            background: #e74c3c;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 14px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .exclusion-tag .remove-tag {
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
        }
        .add-exclusion-btn {
            background: #95a5a6;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 8px;
        }

        button {
            padding: 14px 24px;
            font-size: 16px;
            font-weight: bold;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .btn-search {
            background: #1a73e8;
            color: white;
            width: 100%;
            font-size: 18px;
            padding: 16px;
        }
        .btn-hh { background: #00a0e1; color: white; }
        .btn-avito { background: #005bb9; color: white; }
        .btn-sj { background: #ff8800; color: white; }
        .btn-zp { background: #4caf50; color: white; }

        .external-links {
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #fff9e6;
            border-radius: 8px;
            border: 1px solid #ffe6a0;
        }
        .external-links button { margin: 5px; }

        .stats {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .stat-item {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 6px;
            backdrop-filter: blur(10px);
        }
        .stat-number {
            font-size: 32px;
            font-weight: bold;
            display: block;
        }
        .stat-label {
            font-size: 14px;
            opacity: 0.9;
        }
        .stats .source-badge {
            display: inline-block;
            padding: 5px 15px;
            background: rgba(255,255,255,0.2);
            border-radius: 20px;
            margin-left: 10px;
            font-size: 14px;
        }

        .results { margin-top: 40px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
            box-shadow: 0 1px 5px rgba(0,0,0,0.1);
        }
        th, td {
            border: 1px solid #ddd;
            padding: 14px;
            text-align: left;
            vertical-align: top;
        }
        th {
            background: #34495e;
            color: white;
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        tr:nth-child(even) { background: #f9f9f9; }
        tr:hover {
            background: #f0f8ff;
            cursor: pointer;
        }
        .vacancy-title {
            font-weight: bold;
            color: #2c3e50;
        }
        .company-name {
            color: #7f8c8d;
            font-weight: bold;
        }
        .salary {
            color: #27ae60;
            font-weight: bold;
        }
        .location {
            color: #3498db;
            font-size: 13px;
        }
        .date {
            color: #95a5a6;
            font-size: 12px;
        }

        .loader {
            text-align: center;
            padding: 40px;
            font-size: 16px;
            color: #7f8c8d;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #1a73e8;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .no-results {
            text-align: center;
            padding: 60px;
            color: #e74c3c;
            font-size: 18px;
        }

        .scroll-top {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #1a73e8;
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 24px;
            cursor: pointer;
            display: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 1000;
        }
        .scroll-top.visible { display: block; }

        .badge-new {
            background: #e74c3c;
            color: white;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-left: 8px;
            font-weight: bold;
        }

        .badge-source {
            background: #95a5a6;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            margin-left: 6px;
            font-weight: normal;
        }
        .badge-source.hh { background: #00a0e1; }
        .badge-source.sj { background: #ff8800; }

        @media (max-width: 768px) {
            body { padding: 10px; }
            .container { padding: 15px; }
            h1 { font-size: 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏭 Вакансии линейного персонала</h1>
        <p class="subtitle">Грузчики • Кладовщики • Комплектовщики • Упаковщики • Разнорабочие</p>

        <div class="auth-status" id="authStatus">
            <div class="auth-info">
                <h3 id="authTitle">✅ SuperJob: Авторизован</h3>
                <p id="authText">App ID: 4014 (встроенный)</p>
            </div>
            <div class="auth-actions">
                <button onclick="logout()" id="btnLogout">Выйти</button>
            </div>
        </div>

        <div class="source-selector">
            <h3>🎯 Выберите источник вакансий</h3>
            <div class="source-options">
                <label class="source-option active" for="sourceHH">
                    <input type="radio" name="source" id="sourceHH" value="hh" checked onchange="switchSource('hh')">
                    <div class="source-logo">🔵</div>
                    <div class="source-name">HH.ru</div>
                    <small>Без авторизации</small>
                </label>
                <label class="source-option" for="sourceSJ">
                    <input type="radio" name="source" id="sourceSJ" value="superjob" onchange="switchSource('superjob')">
                    <div class="source-logo">🟠</div>
                    <div class="source-name">SuperJob</div>
                    <small>Готов к работе</small>
                </label>
            </div>
        </div>

        <div class="filters-box">
            <h3 style="margin-top: 0; color: #2c3e50;">🔍 Настройте поиск</h3>
            
            <div class="filter-row">
                <div class="filter-group">
                    <label for="query">Должность:</label>
                    <input type="text" id="query" placeholder="Например: грузчик" value="склад">
                </div>

                <div class="filter-group">
                    <label>Город(а):</label>
                    <div class="city-selector">
                        <div class="city-dropdown" onclick="toggleCityDropdown()">
                            <span id="selectedCitiesText">Санкт-Петербург</span>
                            <span>▼</span>
                        </div>
                        <div class="city-options" id="cityOptions"></div>
                    </div>
                </div>
            </div>

            <div id="exclusionBlock" class="filter-row">
                <div class="filter-group" style="flex: 1 1 100%;">
                    <label for="exclusionInput">
                        Слова-исключения (HH.ru):
                        <small>Вакансии с этими словами будут скрыты</small>
                    </label>
                    <input type="text" id="exclusionInput" placeholder="Введите слово">
                    <button class="add-exclusion-btn" onclick="addExclusion()">➕ Добавить</button>
                    <div class="exclusion-tags" id="exclusionTags">
                        <small style="color: #7f8c8d;">Нет исключений</small>
                    </div>
                </div>
            </div>

            <div class="checkbox-group">
                <label>
                    <input type="checkbox" id="freshOnly" checked> За последние 30 дней
                </label>
                <label>
                    <input type="checkbox" id="lastTwoDays"> За последние 2 дня
                </label>
                <label>
                    <input type="checkbox" id="withSalary"> С зарплатой
                </label>
                <label>
                    <input type="checkbox" id="noExp" checked> Без опыта
                </label>
                <label>
                    <input type="checkbox" id="fullTime" checked> Полная занятость
                </label>
                <label>
                    <input type="checkbox" id="oneVacancyPerCompany"> Одна вакансия от компании
                </label>
            </div>

            <button onclick="startNewSearch()" class="btn-search">🔎 Найти вакансии</button>
        </div>

        <div class="stats" id="stats" style="display: none;">
            <h3 style="margin: 0 0 10px 0;">
                📊 Статистика
                <span class="source-badge" id="currentSourceBadge">HH.ru</span>
            </h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-number" id="statTotal">0</span>
                    <span class="stat-label">Всего найдено</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number" id="statLoaded">0</span>
                    <span class="stat-label">Загружено</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number" id="statWithSalary">0</span>
                    <span class="stat-label">С зарплатой</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number" id="statExcluded">0</span>
                    <span class="stat-label">Исключено</span>
                </div>
            </div>
        </div>

        <div class="external-links">
            <p style="margin: 0 0 10px 0; font-weight: bold; color: #856404;">🌐 Открыть на сайтах:</p>
            <button onclick="go('hh')" class="btn-hh">HH.ru</button>
            <button onclick="go('avito')" class="btn-avito">Avito</button>
            <button onclick="go('superjob')" class="btn-sj">SuperJob</button>
            <button onclick="go('zarplata')" class="btn-zp">Zarplata.ru</button>
        </div>

        <div class="results">
            <h2>📋 Результаты</h2>
            <table id="vacancyTable">
                <thead>
                    <tr>
                        <th style="width: 35%;">Должность</th>
                        <th style="width: 25%;">Компания</th>
                        <th style="width: 15%;">Зарплата</th>
                        <th style="width: 15%;">Город</th>
                        <th style="width: 10%;">Дата</th>
                    </tr>
                </thead>
                <tbody id="vacancyTableBody">
                    <tr><td colspan="5" class="loader">Нажмите "Найти вакансии"</td></tr>
                </tbody>
            </table>

            <div id="loadingIndicator" class="loader" style="display: none;">
                <div class="spinner"></div>
                <p>Загружаем...</p>
            </div>
        </div>
    </div>

    <button class="scroll-top" id="scrollTopBtn" onclick="scrollToTop()">↑</button>

    <script>
        // CREDENTIALS_PLACEHOLDER
        
        const API_BASE = 'https://api.superjob.ru/2.0';

        let currentPage = 0;
        let isLoading = false;
        let hasMore = true;
        let totalFound = 0;
        let loadedCount = 0;
        let withSalaryCount = 0;
        let excludedCount = 0;
        let currentQuery = '';
        let currentSource = 'hh';
        let exclusionWords = [];

        const citiesHH = {
            1: 'Москва', 2: 'Санкт-Петербург', 3: 'Екатеринбург',
            4: 'Новосибирск', 66: 'Нижний Новгород', 88: 'Казань',
            78: 'Самара', 76: 'Краснодар', 54: 'Ростов-на-Дону', 113: 'Вся Россия'
        };

        const citiesSJ = {
            4: 'Москва', 14: 'Санкт-Петербург', 33: 'Екатеринбург',
            13: 'Новосибирск', 12: 'Нижний Новгород', 55: 'Казань',
            5: 'Самара', 25: 'Краснодар', 73: 'Ростов-на-Дону', 0: 'Вся Россия'
        };

        let currentCities = [];

        function logout() {
            if (confirm('Credentials встроены в код. Вы уверены, что хотите выйти?')) {
                alert('Перезагрузите страницу для повторной авторизации');
            }
        }

        function getDateDaysAgo(days) {
            const date = new Date();
            date.setDate(date.getDate() - days);
            return date.toISOString().split('T')[0];
        }

        function getUnixTimeDaysAgo(days) {
            const date = new Date();
            date.setDate(date.getDate() - days);
            return Math.floor(date.getTime() / 1000);
        }

        function formatDate(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const diffDays = Math.ceil(Math.abs(now - date) / (1000 * 60 * 60 * 24));
            
            if (diffDays === 1) return 'Сегодня';
            if (diffDays === 2) return 'Вчера';
            if (diffDays <= 7) return `${diffDays - 1} дн. назад`;
            
            return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
        }

        function formatDateFromUnix(unixtime) {
            return formatDate(new Date(unixtime * 1000).toISOString());
        }

        function isNew(dateString) {
            const diffHours = Math.abs(new Date() - new Date(dateString)) / (1000 * 60 * 60);
            return diffHours < 24;
        }

        function isNewFromUnix(unixtime) {
            return isNew(new Date(unixtime * 1000).toISOString());
        }

        function switchSource(source) {
            currentSource = source;
            
            document.querySelectorAll('.source-option').forEach(opt => opt.classList.remove('active'));
            document.querySelector(`label[for="source${source === 'hh' ? 'HH' : 'SJ'}"]`).classList.add('active');
            
            document.getElementById('exclusionBlock').style.display = source === 'hh' ? 'block' : 'none';
            
            // Set default city for the new source
            const defaultId = currentSource === 'hh' ? 2 : 4;
            currentCities = [defaultId]; // Reset to default for the new source
            
            loadCities();
        }

        function loadCities() {
            const cities = currentSource === 'hh' ? citiesHH : citiesSJ;
            const container = document.getElementById('cityOptions');
            container.innerHTML = '';
            
            for (const [id, name] of Object.entries(cities)) {
                const cityId = parseInt(id);
                const isChecked = currentCities.includes(cityId); // Check if city is in currentCities
                
                const div = document.createElement('div');
                div.className = 'city-option';
                div.innerHTML = `
                    <label>
                        <input type="checkbox" value="${id}" ${isChecked ? 'checked' : ''} onchange="updateCitySelection()">
                        ${name}
                    </label>
                `;
                container.appendChild(div);
            }
            
            updateCitySelection();
        }

        function toggleCityDropdown() {
            document.getElementById('cityOptions').classList.toggle('active');
        }

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.city-selector')) {
                document.getElementById('cityOptions').classList.remove('active');
            }
        });

        function updateCitySelection() {
            const checkboxes = document.querySelectorAll('#cityOptions input:checked');
            currentCities = Array.from(checkboxes).map(cb => parseInt(cb.value));
            
            const cities = currentSource === 'hh' ? citiesHH : citiesSJ;
            const text = currentCities.length === 0 ? 'Выберите город' :
                         currentCities.length === 1 ? cities[currentCities[0]] :
                         `Выбрано: ${currentCities.length}`;
            document.getElementById('selectedCitiesText').textContent = text;
        }

        function addExclusion() {
            const word = document.getElementById('exclusionInput').value.trim().toLowerCase();
            if (word && !exclusionWords.includes(word)) {
                exclusionWords.push(word);
                updateExclusionTags();
                document.getElementById('exclusionInput').value = '';
            }
        }

        function removeExclusion(word) {
            exclusionWords = exclusionWords.filter(w => w !== word);
            updateExclusionTags();
        }

        function updateExclusionTags() {
            const container = document.getElementById('exclusionTags');
            container.innerHTML = exclusionWords.length === 0 
                ? '<small style="color: #7f8c8d;">Нет исключений</small>'
                : exclusionWords.map(w => `
                    <div class="exclusion-tag">
                        <span>${w}</span>
                        <span class="remove-tag" onclick="removeExclusion('${w}')">×</span>
                    </div>
                `).join('');
        }

        function isExcluded(text) {
            if (!text || exclusionWords.length === 0) return false;
            return exclusionWords.some(word => text.toLowerCase().includes(word));
        }

        function startNewSearch() {
            currentPage = 0;
            hasMore = true;
            loadedCount = 0;
            withSalaryCount = 0;
            excludedCount = 0;
            totalFound = 0;
            
            currentQuery = document.getElementById('query').value.trim() || 'склад';
            
            const tbody = document.getElementById('vacancyTableBody');
            tbody.innerHTML = '<tr><td colspan="5" class="loader"><div class="spinner"></div>Поиск...</td></tr>';
            
            document.getElementById('stats').style.display = 'none';
            document.getElementById('currentSourceBadge').textContent = currentSource === 'hh' ? 'HH.ru' : 'SuperJob';
            
            loadMoreVacancies();
        }

        async function loadMoreVacancies() {
            if (isLoading || !hasMore) return;
            
            if (currentSource === 'hh') {
                await loadFromHH();
            } else {
                await loadFromSuperJob();
            }
        }

        async function loadFromHH() {
            isLoading = true;
            document.getElementById('loadingIndicator').style.display = 'block';
            
            try {
                const params = new URLSearchParams({
                    text: currentQuery,
                    per_page: 100,
                    page: currentPage,
                    order_by: 'publication_time'
                });

                currentCities.forEach(city => params.append('area', city));
                
                if (document.getElementById('lastTwoDays')?.checked) {
                    params.append('date_from', getDateDaysAgo(2));
                } else if (document.getElementById('freshOnly')?.checked) {
                    params.append('date_from', getDateDaysAgo(30));
                }
                if (document.getElementById('withSalary')?.checked) {
                    params.append('only_with_salary', 'true');
                }
                if (document.getElementById('noExp')?.checked) {
                    params.append('experience', 'noExperience');
                }
                if (document.getElementById('fullTime')?.checked) {
                    params.append('employment', 'full');
                }

                const response = await fetch(`https://api.hh.ru/vacancies?${params}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const data = await response.json();
                totalFound = data.found;
                hasMore = currentPage < data.pages - 1 && currentPage < 19;

                const tbody = document.getElementById('vacancyTableBody');
                if (currentPage === 0) tbody.innerHTML = '';

                if (data.items?.length > 0) {
                    const companiesAdded = new Set();
                    const oneVacancyPerCompany = document.getElementById('oneVacancyPerCompany')?.checked;

                    data.items.forEach(v => {
                        const companyName = v.employer?.name || 'Не указано';

                        if (oneVacancyPerCompany && companiesAdded.has(companyName)) {
                            excludedCount++;
                            return;
                        }

                        const fullText = `${v.name} ${companyName} ${v.snippet?.requirement || ''}`;
                        if (isExcluded(fullText)) {
                            excludedCount++;
                            return;
                        }

                        const salary = v.salary 
                            ? `${v.salary.from ? v.salary.from.toLocaleString() : ''}${v.salary.to ? ' – ' + v.salary.to.toLocaleString() : ''} ${v.salary.currency || ''}`.trim()
                            : "Не указана";

                        if (v.salary) withSalaryCount++;
                        loadedCount++;

                        const row = document.createElement("tr");
                        row.innerHTML = `
                            <td class="vacancy-title">
                                ${v.name}
                                ${isNew(v.published_at) ? '<span class="badge-new">NEW</span>' : ''}
                                <span class="badge-source hh">HH</span>
                            </td>
                            <td class="company-name">${companyName}</td>
                            <td class="salary">${salary}</td>
                            <td class="location">${v.area?.name || 'Не указано'}</td>
                            <td class="date">${formatDate(v.published_at)}</td>
                        `;
                        row.onclick = () => window.open(`https://hh.ru/vacancy/${v.id}`, '_blank');
                        tbody.appendChild(row);

                        if (oneVacancyPerCompany) {
                            companiesAdded.add(companyName);
                        }
                    });

                    updateStats();
                    currentPage++;
                } else if (currentPage === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" class="no-results">😔 Не найдено</td></tr>`;
                    hasMore = false;
                }

            } catch (error) {
                console.error('HH Error:', error);
                handleError(error);
            } finally {
                isLoading = false;
                document.getElementById('loadingIndicator').style.display = 'none';
            }
        }

        async function loadFromSuperJob() {
            isLoading = true;
            document.getElementById('loadingIndicator').style.display = 'block';
            
            const secretKey = localStorage.getItem('sj_secret_key');
            
            if (!secretKey) {
                document.getElementById('vacancyTableBody').innerHTML = `
                    <tr><td colspan="5" style="text-align:center; padding: 40px;">
                        <h3>⚠️ Ошибка авторизации</h3>
                        <p>Перезагрузите страницу</p>
                    </td></tr>
                `;
                isLoading = false; hasMore = false;
                document.getElementById('loadingIndicator').style.display = 'none';
                return;
            }
            
            try {
                let allVacancies = [];
                let totalFoundForSJ = 0;
                let hasMoreForSJ = false;

                // If multiple cities are selected, make separate requests
                const citiesToSearch = currentCities.length > 0 ? currentCities : [0]; // Default to 'Вся Россия' if no cities selected

                for (const cityId of citiesToSearch) {
                    const params = new URLSearchParams({
                        keyword: currentQuery, count: 100, page: currentPage,
                        order_field: 'date', order_direction: 'desc'
                    });

                    params.append('t', cityId); // Append only one city ID per request

                    if (document.getElementById('lastTwoDays')?.checked) params.append('date_published_from', getUnixTimeDaysAgo(2));
                    else if (document.getElementById('freshOnly')?.checked) params.append('date_published_from', getUnixTimeDaysAgo(30));
                    if (document.getElementById('withSalary')?.checked) params.append('no_agreement', '1');
                    if (document.getElementById('noExp')?.checked) params.append('experience', '1');
                    if (document.getElementById('fullTime')?.checked) params.append('type_of_work', '6');

                    const apiUrl = `https://api.superjob.ru/2.0/vacancies/?${params}`;
                    const proxyUrl = `/proxy?url=${encodeURIComponent(apiUrl)}&key=${encodeURIComponent(secretKey)}`;
                    
                    const response = await fetch(proxyUrl);
                    
                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error('Proxy error:', errorText);
                        throw new Error(`HTTP ${response.status}: ${errorText}`);
                    }
                    
                    const data = await response.json();
                    totalFoundForSJ += data.total;
                    if (data.more) hasMoreForSJ = true; // If any city has more, then overall has more
                    
                    if (data.objects?.length > 0) {
                        allVacancies = allVacancies.concat(data.objects);
                    }
                }

                totalFound = totalFoundForSJ;
                hasMore = hasMoreForSJ;

                const tbody = document.getElementById('vacancyTableBody');
                if (currentPage === 0) tbody.innerHTML = '';

                if (allVacancies.length > 0) {
                    const companiesAdded = new Set();
                    const oneVacancyPerCompany = document.getElementById('oneVacancyPerCompany')?.checked;

                    allVacancies.forEach(v => {
                        const companyName = v.firm_name || '—';

                        if (oneVacancyPerCompany && companiesAdded.has(companyName)) {
                            excludedCount++;
                            return;
                        }

                        const salary = v.payment_from || v.payment_to
                            ? `${v.payment_from ? v.payment_from.toLocaleString() : ''}${v.payment_to ? ' – ' + v.payment_to.toLocaleString() : ''} ₽`.trim()
                            : v.agreement ? "По дог." : "—";

                        if (v.payment_from || v.payment_to) withSalaryCount++;
                        loadedCount++;

                        const row = document.createElement("tr");
                        row.innerHTML = `
                            <td class="vacancy-title">${v.profession}${isNewFromUnix(v.date_published) ? '<span class="badge-new">NEW</span>' : ''}<span class="badge-source sj">SJ</span></td>
                            <td class="company-name">${companyName}</td>
                            <td class="salary">${salary}</td>
                            <td class="location">${v.town?.title || '—'}</td>
                            <td class="date">${formatDateFromUnix(v.date_published)}</td>
                        `;
                        row.onclick = () => window.open(v.link, '_blank');
                        tbody.appendChild(row);

                        if (oneVacancyPerCompany) {
                            companiesAdded.add(companyName);
                        }
                    });

                    updateStats();
                    currentPage++;
                } else if (currentPage === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" class="no-results">😔 Не найдено</td></tr>`;
                    hasMore = false;
                }

            } catch (error) {
                console.error('SJ Error:', error);
                handleError(error);
            } finally {
                isLoading = false;
                document.getElementById('loadingIndicator').style.display = 'none';
            }
        }

        function handleError(error) {
            const tbody = document.getElementById('vacancyTableBody');
            if (currentPage === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align:center; color:#e74c3c; padding: 40px;">
                            ⚠️ Ошибка: ${error.message}<br>
                            <button onclick="startNewSearch()" style="margin-top: 15px;">🔄 Повторить</button>
                        </td>
                    </tr>
                `;
            }
            hasMore = false;
        }

        function updateStats() {
            document.getElementById('stats').style.display = 'block';
            document.getElementById('statTotal').textContent = totalFound.toLocaleString();
            document.getElementById('statLoaded').textContent = loadedCount.toLocaleString();
            document.getElementById('statWithSalary').textContent = withSalaryCount.toLocaleString();
            document.getElementById('statExcluded').textContent = excludedCount.toLocaleString();
        }

        window.addEventListener('scroll', () => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight;
            
            const scrollBtn = document.getElementById('scrollTopBtn');
            scrollBtn.classList.toggle('visible', scrollTop > 300);
            
            if (scrollTop + windowHeight >= documentHeight - 500) {
                if (!isLoading && hasMore) loadMoreVacancies();
            }
        });

        function scrollToTop() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function go(platform) {
            const query = document.getElementById('query').value.trim() || "склад";
            const encoded = encodeURIComponent(query);
            const urls = {
                hh: `https://spb.hh.ru/search/vacancy?text=${encoded}`,
                avito: `https://www.avito.ru/rossiya/vakansii?q=${encoded}`,
                superjob: `https://www.superjob.ru/vacancy/search/?keywords=${encoded}`,
                zarplata: `https://www.zarplata.ru/vacancies?search=${encoded}`
            };
            if (urls[platform]) window.open(urls[platform], '_blank');
        }

        window.onload = () => {
            // Set initial default city
            const defaultId = currentSource === 'hh' ? 2 : 4;
            currentCities = [defaultId];
            
            loadCities();
            
            document.getElementById('exclusionInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') addExclusion();
            });

            document.getElementById('query').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') startNewSearch();
            });
        };
    </script>
</body>
</html>
'''

# ============ ЗАПУСК ============
if __name__ == '__main__':
    print('🚀 Vacancy App running!')
    print('📍 Для PythonAnywhere настройте WSGI на этот файл')
    print('📍 Для локального запуска: app.run()')
    
    # Для локального тестирования (закомментируйте на PythonAnywhere)
    app.run(host='0.0.0.0', port=8000, debug=True)
