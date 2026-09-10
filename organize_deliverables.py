import os
import shutil

def organize_project_structure():
    base_dir = os.path.abspath('financial_trade_monitoring')
    
    dirs = {
        'data': os.path.join(base_dir, 'data'),
        'sql': os.path.join(base_dir, 'sql'),
        'python': os.path.join(base_dir, 'python'),
        'antigravity': os.path.join(base_dir, 'antigravity'),
        'excel': os.path.join(base_dir, 'excel'),
        'tableau': os.path.join(base_dir, 'tableau')
    }

    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    # 1. Data files
    if os.path.exists('trades_raw.csv'):
        shutil.copy('trades_raw.csv', os.path.join(dirs['data'], 'trades_raw.csv'))
    if os.path.exists('trade_monitoring_all_trades.csv'):
        shutil.copy('trade_monitoring_all_trades.csv', os.path.join(dirs['data'], 'all_trades_scored.csv'))
    if os.path.exists('trade_monitoring_flagged.csv'):
        shutil.copy('trade_monitoring_flagged.csv', os.path.join(dirs['data'], 'flagged_trades.csv'))
    if os.path.exists('trade_monitoring_summary.json'):
        shutil.copy('trade_monitoring_summary.json', os.path.join(dirs['data'], 'summary.json'))

    # 2. SQL files
    if os.path.exists('schema.sql'):
        shutil.copy('schema.sql', os.path.join(dirs['sql'], 'schema.sql'))
    if os.path.exists('feature_engineering.sql'):
        shutil.copy('feature_engineering.sql', os.path.join(dirs['sql'], 'feature_queries.sql'))

    # 3. Python files
    if os.path.exists('anomaly_detection.py'):
        shutil.copy('anomaly_detection.py', os.path.join(dirs['python'], 'anomaly_detection.py'))

    # 4. Antigravity files
    if os.path.exists('antigravity_workflow.yaml'):
        shutil.copy('antigravity_workflow.yaml', os.path.join(dirs['antigravity'], 'workflow_config.yaml'))

    # 5. Excel files
    if os.path.exists('alert_trades.xlsx'):
        shutil.copy('alert_trades.xlsx', os.path.join(dirs['excel'], 'alert_trades.xlsx'))
    if os.path.exists('vba_modules/AlertWorkbookVBA.bas'):
        shutil.copy('vba_modules/AlertWorkbookVBA.bas', os.path.join(dirs['excel'], 'AlertWorkbookVBA.bas'))

    # 6. Tableau files
    if os.path.exists('TABLEAU_DASHBOARD_SPEC.md'):
        shutil.copy('TABLEAU_DASHBOARD_SPEC.md', os.path.join(dirs['tableau'], 'TABLEAU_DASHBOARD_SPEC.md'))

    print(f"[OK] Organized project files in '{base_dir}'")

if __name__ == '__main__':
    organize_project_structure()
