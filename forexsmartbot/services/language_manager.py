"""
Language Manager for ForexSmartBot
Handles multi-language support for the application
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal


class LanguageManager(QObject):
    """Manages application language and translations."""
    
    language_changed = pyqtSignal(str)  # Emitted when language changes
    
    def __init__(self, settings_manager=None):
        super().__init__()
        self.settings_manager = settings_manager
        self.current_language = "en"
        self.translations = {}
        self.languages_dir = Path(__file__).parent.parent / "languages"
        self.languages_dir.mkdir(exist_ok=True)
        
        # Load current language from settings
        if self.settings_manager:
            self.current_language = self.settings_manager.get('language', 'en')
        
        # Load translations
        self.load_translations()
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages."""
        return {
            "en": "English",
            "fr": "Français",
            "es": "Español", 
            "zh": "中文",
            "ja": "日本語",
            "de": "Deutsch",
            "ru": "Русский",
            "et": "Eesti",
            "pt": "Português",
            "ko": "한국어",
            "ca": "Català",
            "eu": "Euskera",
            "gl": "Galego"
        }
    
    def load_translations(self):
        """Load translation files."""
        for lang_code in self.get_supported_languages().keys():
            self.translations[lang_code] = self._load_language_file(lang_code)
    
    def _load_language_file(self, lang_code: str) -> Dict[str, str]:
        """Load translation file for specific language."""
        lang_file = self.languages_dir / f"{lang_code}.json"
        
        if lang_file.exists():
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading language file {lang_code}: {e}")
        
        # Return empty dict if file doesn't exist or error
        return {}
    
    def set_language(self, lang_code: str):
        """Set the current language."""
        if lang_code in self.get_supported_languages():
            self.current_language = lang_code
            if self.settings_manager:
                self.settings_manager.set('language', lang_code)
            self.language_changed.emit(lang_code)
    
    def get_text(self, key: str, default: str = None) -> str:
        """Get translated text for a key."""
        if default is None:
            default = key
        
        # Try current language first
        if self.current_language in self.translations:
            text = self.translations[self.current_language].get(key, default)
            if text != default:
                return text
        
        # Fallback to English
        if self.current_language != "en" and "en" in self.translations:
            text = self.translations["en"].get(key, default)
            if text != default:
                return text
        
        return default
    
    def tr(self, key: str, default: str = None) -> str:
        """Shortcut for get_text method."""
        return self.get_text(key, default)
    
    def create_default_translations(self):
        """Create default translation files for all supported languages."""
        default_translations = self._get_default_translations()
        
        for lang_code, lang_name in self.get_supported_languages().items():
            lang_file = self.languages_dir / f"{lang_code}.json"
            
            if not lang_file.exists():
                with open(lang_file, 'w', encoding='utf-8') as f:
                    json.dump(default_translations[lang_code], f, indent=2, ensure_ascii=False)
    
    def _get_default_translations(self) -> Dict[str, Dict[str, str]]:
        """Get default translations for all languages."""
        return {
            "en": {
                "app_title": "ForexSmartBot",
                "file_menu": "File",
                "settings": "Settings",
                "exit": "Exit",
                "tools_menu": "Tools",
                "backtest": "Run Backtest",
                "export_trades": "Export Trades",
                "help_menu": "Help",
                "about": "About",
                "trading_status": "Trading Status",
                "broker": "Broker",
                "connection": "Connection",
                "balance": "Balance",
                "equity": "Equity",
                "drawdown": "Drawdown",
                "strategy_config": "Strategy Configuration",
                "strategy": "Strategy",
                "symbols": "Symbols",
                "leverage": "Leverage",
                "trading_controls": "Trading Controls",
                "connect": "Connect",
                "disconnect": "Disconnect",
                "start_trading": "Start Trading",
                "stop_trading": "Stop Trading",
                "open_positions": "Open Positions",
                "closed_positions": "Closed Positions",
                "performance_metrics": "Performance Metrics",
                "total_trades": "Total Trades",
                "win_rate": "Win Rate",
                "profit_factor": "Profit Factor",
                "max_drawdown": "Max Drawdown",
                "language": "Language",
                "startup": "Run on Startup",
                "theme": "Theme",
                "notifications": "Notifications",
                "telegram": "Telegram",
                "discord": "Discord"
            },
            "fr": {
                "app_title": "ForexSmartBot",
                "file_menu": "Fichier",
                "settings": "Paramètres",
                "exit": "Quitter",
                "tools_menu": "Outils",
                "backtest": "Lancer Backtest",
                "export_trades": "Exporter Trades",
                "help_menu": "Aide",
                "about": "À propos",
                "trading_status": "Statut Trading",
                "broker": "Courtier",
                "connection": "Connexion",
                "balance": "Solde",
                "equity": "Equity",
                "drawdown": "Drawdown",
                "strategy_config": "Configuration Stratégie",
                "strategy": "Stratégie",
                "symbols": "Symboles",
                "leverage": "Effet de levier",
                "trading_controls": "Contrôles Trading",
                "connect": "Connecter",
                "disconnect": "Déconnecter",
                "start_trading": "Démarrer Trading",
                "stop_trading": "Arrêter Trading",
                "open_positions": "Positions Ouvertes",
                "closed_positions": "Positions Fermées",
                "performance_metrics": "Métriques Performance",
                "total_trades": "Total Trades",
                "win_rate": "Taux de Réussite",
                "profit_factor": "Facteur de Profit",
                "max_drawdown": "Drawdown Max",
                "language": "Langue",
                "startup": "Démarrer au Démarrage",
                "theme": "Thème",
                "notifications": "Notifications",
                "telegram": "Telegram",
                "discord": "Discord"
            },
            "es": {
                "app_title": "ForexSmartBot",
                "file_menu": "Archivo",
                "settings": "Configuración",
                "exit": "Salir",
                "tools_menu": "Herramientas",
                "backtest": "Ejecutar Backtest",
                "export_trades": "Exportar Trades",
                "help_menu": "Ayuda",
                "about": "Acerca de",
                "trading_status": "Estado Trading",
                "broker": "Broker",
                "connection": "Conexión",
                "balance": "Balance",
                "equity": "Equity",
                "drawdown": "Drawdown",
                "strategy_config": "Configuración Estrategia",
                "strategy": "Estrategia",
                "symbols": "Símbolos",
                "leverage": "Apalancamiento",
                "trading_controls": "Controles Trading",
                "connect": "Conectar",
                "disconnect": "Desconectar",
                "start_trading": "Iniciar Trading",
                "stop_trading": "Detener Trading",
                "open_positions": "Posiciones Abiertas",
                "closed_positions": "Posiciones Cerradas",
                "performance_metrics": "Métricas Rendimiento",
                "total_trades": "Total Trades",
                "win_rate": "Tasa Éxito",
                "profit_factor": "Factor Beneficio",
                "max_drawdown": "Drawdown Máximo",
                "language": "Idioma",
                "startup": "Ejecutar al Inicio",
                "theme": "Tema",
                "notifications": "Notificaciones",
                "telegram": "Telegram",
                "discord": "Discord"
            },
            "zh": {
                "app_title": "ForexSmartBot",
                "file_menu": "文件",
                "settings": "设置",
                "exit": "退出",
                "tools_menu": "工具",
                "backtest": "运行回测",
                "export_trades": "导出交易",
                "help_menu": "帮助",
                "about": "关于",
                "trading_status": "交易状态",
                "broker": "经纪商",
                "connection": "连接",
                "balance": "余额",
                "equity": "净值",
                "drawdown": "回撤",
                "strategy_config": "策略配置",
                "strategy": "策略",
                "symbols": "交易对",
                "leverage": "杠杆",
                "trading_controls": "交易控制",
                "connect": "连接",
                "disconnect": "断开",
                "start_trading": "开始交易",
                "stop_trading": "停止交易",
                "open_positions": "持仓",
                "closed_positions": "已平仓",
                "performance_metrics": "绩效指标",
                "total_trades": "总交易数",
                "win_rate": "胜率",
                "profit_factor": "盈利因子",
                "max_drawdown": "最大回撤",
                "language": "语言",
                "startup": "开机启动",
                "theme": "主题",
                "notifications": "通知",
                "telegram": "Telegram",
                "discord": "Discord"
            },
            "ja": {
                "app_title": "ForexSmartBot",
                "file_menu": "ファイル",
                "settings": "設定",
                "exit": "終了",
                "tools_menu": "ツール",
                "backtest": "バックテスト実行",
                "export_trades": "取引エクスポート",
                "help_menu": "ヘルプ",
                "about": "について",
                "trading_status": "取引ステータス",
                "broker": "ブローカー",
                "connection": "接続",
                "balance": "残高",
                "equity": "エクイティ",
                "drawdown": "ドローダウン",
                "strategy_config": "戦略設定",
                "strategy": "戦略",
                "symbols": "シンボル",
                "leverage": "レバレッジ",
                "trading_controls": "取引コントロール",
                "connect": "接続",
                "disconnect": "切断",
                "start_trading": "取引開始",
                "stop_trading": "取引停止",
                "open_positions": "オープンポジション",
                "closed_positions": "クローズドポジション",
                "performance_metrics": "パフォーマンス指標",
                "total_trades": "総取引数",
                "win_rate": "勝率",
                "profit_factor": "プロフィットファクター",
                "max_drawdown": "最大ドローダウン",
                "language": "言語",
                "startup": "スタートアップ実行",
                "theme": "テーマ",
                "notifications": "通知",
                "telegram": "Telegram",
                "discord": "Discord"
            },
            "de": {
                "app_title": "ForexSmartBot",
                "file_menu": "Datei",
                "settings": "Einstellungen",
                "exit": "Beenden",
                "tools_menu": "Werkzeuge",
                "backtest": "Backtest ausführen",
                "export_trades": "Trades exportieren",
                "help_menu": "Hilfe",
                "about": "Über",
                "trading_status": "Trading Status",
                "broker": "Broker",
                "connection": "Verbindung",
                "balance": "Guthaben",
                "equity": "Eigenkapital",
                "drawdown": "Drawdown",
                "strategy_config": "Strategie Konfiguration",
                "strategy": "Strategie",
                "symbols": "Symbole",
                "leverage": "Hebel",
                "trading_controls": "Trading Kontrollen",
                "connect": "Verbinden",
                "disconnect": "Trennen",
                "start_trading": "Trading starten",
                "stop_trading": "Trading stoppen",
                "open_positions": "Offene Positionen",
                "closed_positions": "Geschlossene Positionen",
                "performance_metrics": "Leistungsmetriken",
                "total_trades": "Gesamt Trades",
                "win_rate": "Gewinnrate",
                "profit_factor": "Profitfaktor",
                "max_drawdown": "Max Drawdown",
                "language": "Sprache",
                "startup": "Beim Start ausführen",
                "theme": "Design",
                "notifications": "Benachrichtigungen",
                "telegram": "Telegram",
                "discord": "Discord"
            },
            "ru": {
                "app_title": "ForexSmartBot",
                "file_menu": "Файл",
                "settings": "Настройки",
                "exit": "Выход",
                "tools_menu": "Инструменты",
                "backtest": "Запустить Бэктест",
                "export_trades": "Экспорт Сделок",
                "help_menu": "Помощь",
                "about": "О программе",
                "trading_status": "Статус Торговли",
                "broker": "Брокер",
                "connection": "Соединение",
                "balance": "Баланс",
                "equity": "Эквити",
                "drawdown": "Просадка",
                "strategy_config": "Конфигурация Стратегии",
                "strategy": "Стратегия",
                "symbols": "Символы",
                "leverage": "Плечо",
                "trading_controls": "Управление Торговлей",
                "connect": "Подключить",
                "disconnect": "Отключить",
                "start_trading": "Начать Торговлю",
                "stop_trading": "Остановить Торговлю",
                "open_positions": "Открытые Позиции",
                "closed_positions": "Закрытые Позиции",
                "performance_metrics": "Метрики Производительности",
                "total_trades": "Всего Сделок",
                "win_rate": "Процент Побед",
                "profit_factor": "Фактор Прибыли",
                "max_drawdown": "Макс Просадка",
                "language": "Язык",
                "startup": "Запуск при Старте",
                "theme": "Тема",
                "notifications": "Уведомления",
                "telegram": "Telegram",
                "discord": "Discord"
            },
            "et": {
                "app_title": "ForexSmartBot",
                "file_menu": "Fail",
                "settings": "Seaded",
                "exit": "Välju",
                "tools_menu": "Tööriistad",
                "backtest": "Käivita Backtest",
                "export_trades": "Ekspordi Tehingud",
                "help_menu": "Abi",
                "about": "Teave",
                "trading_status": "Kaubanduse Staatus",
                "broker": "Broker",
                "connection": "Ühendus",
                "balance": "Saldo",
                "equity": "Omakapital",
                "drawdown": "Langus",
                "strategy_config": "Strateegia Konfiguratsioon",
                "strategy": "Strateegia",
                "symbols": "Sümbolid",
                "leverage": "Finantsvõimendus",
                "trading_controls": "Kaubanduse Kontrollid",
                "connect": "Ühenda",
                "disconnect": "Katkesta",
                "start_trading": "Alusta Kaubandust",
                "stop_trading": "Peata Kaubandus",
                "open_positions": "Avatud Positsioonid",
                "closed_positions": "Suletud Positsioonid",
                "performance_metrics": "Tulemuslikkuse Meetmed",
                "total_trades": "Kokku Tehinguid",
                "win_rate": "Võidutase",
                "profit_factor": "Kasumitegur",
                "max_drawdown": "Maks Langus",
                "language": "Keel",
                "startup": "Käivita Käivitamisel",
                "theme": "Teema",
                "notifications": "Teated",
                "telegram": "Telegram",
                "discord": "Discord"
            },
            "pt": {
                "app_title": "ForexSmartBot",
                "file_menu": "Arquivo",
                "settings": "Configurações",
                "exit": "Sair",
                "tools_menu": "Ferramentas",
                "backtest": "Executar Backtest",
                "export_trades": "Exportar Trades",
                "help_menu": "Ajuda",
                "about": "Sobre",
                "trading_status": "Status Trading",
                "broker": "Corretora",
                "connection": "Conexão",
                "balance": "Saldo",
                "equity": "Patrimônio",
                "drawdown": "Drawdown",
                "strategy_config": "Configuração Estratégia",
                "strategy": "Estratégia",
                "symbols": "Símbolos",
                "leverage": "Alavancagem",
                "trading_controls": "Controles Trading",
                "connect": "Conectar",
                "disconnect": "Desconectar",
                "start_trading": "Iniciar Trading",
                "stop_trading": "Parar Trading",
                "open_positions": "Posições Abertas",
                "closed_positions": "Posições Fechadas",
                "performance_metrics": "Métricas Performance",
                "total_trades": "Total Trades",
                "win_rate": "Taxa Sucesso",
                "profit_factor": "Fator Lucro",
                "max_drawdown": "Drawdown Máximo",
                "language": "Idioma",
                "startup": "Executar na Inicialização",
                "theme": "Tema",
                "notifications": "Notificações",
                "telegram": "Telegram",
                "discord": "Discord"
            },
            "ko": {
                "app_title": "ForexSmartBot",
                "file_menu": "파일",
                "settings": "설정",
                "exit": "종료",
                "tools_menu": "도구",
                "backtest": "백테스트 실행",
                "export_trades": "거래 내보내기",
                "help_menu": "도움말",
                "about": "정보",
                "trading_status": "거래 상태",
                "broker": "브로커",
                "connection": "연결",
                "balance": "잔고",
                "equity": "자본",
                "drawdown": "드로다운",
                "strategy_config": "전략 설정",
                "strategy": "전략",
                "symbols": "심볼",
                "leverage": "레버리지",
                "trading_controls": "거래 제어",
                "connect": "연결",
                "disconnect": "연결 해제",
                "start_trading": "거래 시작",
                "stop_trading": "거래 중지",
                "open_positions": "미결 포지션",
                "closed_positions": "결제 포지션",
                "performance_metrics": "성과 지표",
                "total_trades": "총 거래",
                "win_rate": "승률",
                "profit_factor": "수익 팩터",
                "max_drawdown": "최대 드로다운",
                "language": "언어",
                "startup": "시작 시 실행",
                "theme": "테마",
                "notifications": "알림",
                "telegram": "Telegram",
                "discord": "Discord"
            },
            "ca": {
                "app_title": "ForexSmartBot",
                "file_menu": "Fitxer",
                "settings": "Configuració",
                "exit": "Sortir",
                "tools_menu": "Eines",
                "backtest": "Executar Backtest",
                "export_trades": "Exportar Trades",
                "help_menu": "Ajuda",
                "about": "Quant a",
                "trading_status": "Estat Trading",
                "broker": "Broker",
                "connection": "Connexió",
                "balance": "Balanç",
                "equity": "Equity",
                "drawdown": "Drawdown",
                "strategy_config": "Configuració Estratègia",
                "strategy": "Estratègia",
                "symbols": "Símbols",
                "leverage": "Palanquejament",
                "trading_controls": "Controles Trading",
                "connect": "Connectar",
                "disconnect": "Desconnectar",
                "start_trading": "Iniciar Trading",
                "stop_trading": "Aturar Trading",
                "open_positions": "Posicions Obertes",
                "closed_positions": "Posicions Tancades",
                "performance_metrics": "Mètriques Rendiment",
                "total_trades": "Total Trades",
                "win_rate": "Taxa Èxit",
                "profit_factor": "Factor Benefici",
                "max_drawdown": "Drawdown Màxim",
                "language": "Idioma",
                "startup": "Executar a l'Inici",
                "theme": "Tema",
                "notifications": "Notificacions",
                "telegram": "Telegram",
                "discord": "Discord"
            },
            "eu": {
                "app_title": "ForexSmartBot",
                "file_menu": "Fitxategia",
                "settings": "Ezarpenak",
                "exit": "Irten",
                "tools_menu": "Tresnak",
                "backtest": "Backtest Exekutatu",
                "export_trades": "Trades Esportatu",
                "help_menu": "Laguntza",
                "about": "Honi buruz",
                "trading_status": "Trading Egoera",
                "broker": "Broker",
                "connection": "Konexioa",
                "balance": "Saldoa",
                "equity": "Equity",
                "drawdown": "Drawdown",
                "strategy_config": "Estrategia Konfigurazioa",
                "strategy": "Estrategia",
                "symbols": "Sinboloak",
                "leverage": "Palanka",
                "trading_controls": "Trading Kontrolak",
                "connect": "Konektatu",
                "disconnect": "Deskonektatu",
                "start_trading": "Trading Hasi",
                "stop_trading": "Trading Gelditu",
                "open_positions": "Posizio Irekiak",
                "closed_positions": "Posizio Itxiak",
                "performance_metrics": "Errendimendu Metrikak",
                "total_trades": "Guztira Trades",
                "win_rate": "Irabazi Tasa",
                "profit_factor": "Irabazi Faktorea",
                "max_drawdown": "Gehienezko Drawdown",
                "language": "Hizkuntza",
                "startup": "Abian Exekutatu",
                "theme": "Gaia",
                "notifications": "Jakinarazpenak",
                "telegram": "Telegram",
                "discord": "Discord"
            },
            "gl": {
                "app_title": "ForexSmartBot",
                "file_menu": "Ficheiro",
                "settings": "Configuración",
                "exit": "Saír",
                "tools_menu": "Ferramentas",
                "backtest": "Executar Backtest",
                "export_trades": "Exportar Trades",
                "help_menu": "Axuda",
                "about": "Acerca de",
                "trading_status": "Estado Trading",
                "broker": "Broker",
                "connection": "Conexión",
                "balance": "Saldo",
                "equity": "Equity",
                "drawdown": "Drawdown",
                "strategy_config": "Configuración Estratexia",
                "strategy": "Estratexia",
                "symbols": "Símbolos",
                "leverage": "Apalancamento",
                "trading_controls": "Controles Trading",
                "connect": "Conectar",
                "disconnect": "Desconectar",
                "start_trading": "Iniciar Trading",
                "stop_trading": "Deter Trading",
                "open_positions": "Posicións Abertas",
                "closed_positions": "Posicións Pechadas",
                "performance_metrics": "Métricas Rendemento",
                "total_trades": "Total Trades",
                "win_rate": "Taxa Éxito",
                "profit_factor": "Factor Beneficio",
                "max_drawdown": "Drawdown Máximo",
                "language": "Idioma",
                "startup": "Executar ao Inicio",
                "theme": "Tema",
                "notifications": "Notificacións",
                "telegram": "Telegram",
                "discord": "Discord"
            }
        }
