import pandas as pd
import glob
import random
import os
import time
from dash import Dash, dcc, html, Input, Output, State, no_update

#--- データの読み込み (エラーに強い設計) ---
def load_data():
    all_files = glob.glob("*.csv")
    category_map = {}
    
    if not all_files:
        print("CSVファイルが見つかりません。")
        return category_map

    for filename in all_files:
        try:
            try:
                df = pd.read_csv(filename, header=None, encoding='utf-8')
            except:
                df = pd.read_csv(filename, header=None, encoding='shift-jis')
            
            current_cat = None
            for _, row in df.iterrows():
                cat_val = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                num_val = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                
                if cat_val != "" and cat_val != "nan":
                    current_cat = cat_val
                    if current_cat not in category_map:
                        category_map[current_cat] = []
                
                if current_cat and num_val != "" and num_val != "nan":
                    clean_num = num_val.rstrip(',')
                    if clean_num:
                        category_map[current_cat].append(clean_num)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue
            
    return {k: v for k, v in category_map.items() if v}

data_dict = load_data()
categories = sorted(list(data_dict.keys()))

#--- アプリ作成 ---
app = Dash(__name__)
server = app.server

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Premium Magic Roulette</title>
        {%favicon%}
        {%css%}
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@900&family=Noto+Sans+JP:wght@500;900&display=swap');
            body {
                background: #0f172a;
                font-family: 'Noto Sans JP', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }
            .card {
                background: #ffffff;
                padding: 40px;
                border-radius: 40px;
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
                text-align: center;
                width: 90%;
                max-width: 450px;
            }
            .display-box {
                background: #000000;
                color: #00ffcc;
                font-family: 'Montserrat', sans-serif;
                font-size: 90px;
                height: 180px;
                line-height: 180px;
                border-radius: 25px;
                margin: 30px 0;
                box-shadow: inset 0 0 30px rgba(0,255,204,0.3);
                transition: all 0.1s ease;
                overflow: hidden;
            }
            .spinning {
                color: #008877;
                opacity: 0.7;
                transform: scale(0.95);
            }
            .fixed {
                color: #ff0077;
                text-shadow: 0 0 20px #ff0077, 0 0 40px #ff0077;
                transform: scale(1.1);
                animation: pop 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }
            @keyframes pop {
                0% { transform: scale(0.8); }
                100% { transform: scale(1.1); }
            }
            .spin-button {
                background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
                color: white;
                border: none;
                padding: 20px;
                width: 100%;
                font-size: 24px;
                font-weight: 900;
                border-radius: 20px;
                cursor: pointer;
                transition: 0.3s;
                box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4);
            }
            .spin-button:hover {
                transform: translateY(-3px);
                filter: brightness(1.1);
            }
            .spin-button:disabled {
                background: #475569;
                box-shadow: none;
                cursor: not-allowed;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = html.Div([
    html.Div([
        html.H1("ROULETTE", style={'margin': '0', 'fontWeight': '900', 'letterSpacing': '8px', 'color': '#1e293b'}),
        html.P("カテゴリーを選んで運試し！", style={'color': '#64748b', 'marginTop': '5px'}),
        
        html.Div([
            dcc.Dropdown(
                id='cat-drop',
                options=[{'label': c, 'value': c} for c in categories],
                placeholder="カテゴリーを選択",
                style={'textAlign': 'left'}
            ),
        ], style={'marginTop': '20px'}),

        html.Div("---", id='display-text', className="display-box"),

        html.Button("SPIN START!", id='spin-btn', className="spin-button"),

        # 3秒間の演出用
        # intervalを短く設定し、callback側で表示更新を間引くことで「徐々にゆっくり」を実現
        dcc.Interval(id='timer', interval=50, n_intervals=0, disabled=True),
        dcc.Store(id='store-final-val'),
    ], className="card")
])

#--- コールバック ---

@app.callback(
    Output('timer', 'disabled'),
    Output('timer', 'n_intervals'),
    Output('store-final-val', 'data'),
    Output('spin-btn', 'disabled'),
    Input('spin-btn', 'n_clicks'),
    State('cat-drop', 'value'),
    prevent_initial_call=True
)
def start_spin(n, cat):
    if not cat: return no_update, no_update, no_update, no_update
    
    choices = data_dict.get(cat, [])
    if not choices: return no_update, no_update, no_update, no_update
    
    final = random.choice(choices)
    return False, 0, final, True

@app.callback(
    Output('display-text', 'children'),
    Output('display-text', 'className'),
    Output('timer', 'disabled', allow_duplicate=True),
    Output('spin-btn', 'disabled', allow_duplicate=True),
    Input('timer', 'n_intervals'),
    State('store-final-val', 'data'),
    State('cat-drop', 'value'),
    prevent_initial_call=True
)
def update_animation(n, final, cat,):
    choices = data_dict.get(cat, [])
    
    # 演出の合計ステップ（50ms * 60回 = 約3秒）
    total_steps = 60
    
    if n < total_steps:
        # 徐々に更新頻度を下げるロジック
        # 最初(n=0)は毎回更新、最後(n=60)に近づくほど更新を飛ばす
        # 閾値を計算（nが大きくなるほど更新間隔を広げる）
        threshold = (n // 10) # 0, 1, 2, 3, 4, 5
        
        if n % (threshold + 1) == 0:
            return random.choice(choices), "display-box spinning", False, True
        else:
            return no_update, "display-box spinning", False, True
    else:
        # 終了：最終結果を表示してボタンを有効化
        return final, "display-box fixed", True, False

if __name__ == '__main__':
    app.run(jupyter_mode='inline')
