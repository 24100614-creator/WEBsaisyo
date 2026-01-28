import pandas as pd
import glob
import random
import os
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
            # Shift-JISやUTF-8など、エンコーディングエラーを回避
            try:
                df = pd.read_csv(filename, header=None, encoding='utf-8')
            except:
                df = pd.read_csv(filename, header=None, encoding='shift-jis')
            
            current_cat = None
            for _, row in df.iterrows():
                # A列(0):カテゴリー, B列(1):数字
                cat_val = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                num_val = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                
                # A列に文字があれば新しいカテゴリー
                if cat_val != "" and cat_val != "nan":
                    current_cat = cat_val
                    if current_cat not in category_map:
                        category_map[current_cat] = []
                
                # 数字の掃除（末尾のカンマなどを除去）
                if current_cat and num_val != "" and num_val != "nan":
                    clean_num = num_val.rstrip(',')
                    if clean_num:
                        category_map[current_cat].append(clean_num)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue
            
    # 空のカテゴリーを削除
    return {k: v for k, v in category_map.items() if v}

# データ初期化
data_dict = load_data()
categories = sorted(list(data_dict.keys()))

#--- アプリ作成 ---
app = Dash(__name__)
server = app.server

# デザインのカスタマイズ
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Magic Roulette</title>
        {%favicon%}
        {%css%}
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@900&family=Noto+Sans+JP:wght@500;900&display=swap');
            body {
                background: #f0f2f5;
                font-family: 'Noto Sans JP', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }
            .card {
                background: white;
                padding: 40px;
                border-radius: 30px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.1);
                text-align: center;
                width: 90%;
                max-width: 450px;
            }
            .display-box {
                background: #1a1a1a;
                color: #00ffcc;
                font-family: 'Montserrat', sans-serif;
                font-size: 80px;
                height: 160px;
                line-height: 160px;
                border-radius: 20px;
                margin: 30px 0;
                box-shadow: inset 0 0 20px rgba(0,255,204,0.2);
                text-shadow: 0 0 15px rgba(0,255,204,0.5);
                overflow: hidden;
            }
            .spin-button {
                background: linear-gradient(135deg, #00dbde 0%, #fc00ff 100%);
                color: white;
                border: none;
                padding: 18px;
                width: 100%;
                font-size: 22px;
                font-weight: 900;
                border-radius: 15px;
                cursor: pointer;
                transition: 0.3s;
            }
            .spin-button:hover {
                transform: scale(1.03);
                filter: brightness(1.1);
            }
            .spin-button:disabled {
                background: #ccc;
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
        html.H1("ROULETTE", style={'margin': '0', 'fontWeight': '900', 'letterSpacing': '5px'}),
        html.P("カテゴリーを選んでスタート！", style={'color': '#666'}),
        
        html.Div([
            dcc.Dropdown(
                id='cat-drop',
                options=[{'label': c, 'value': c} for c in categories],
                placeholder="--- カテゴリー選択 ---",
                style={'textAlign': 'left'}
            ),
        ], style={'marginTop': '20px'}),

        html.Div("---", id='display-text', className="display-box"),

        html.Button("SPIN START!", id='spin-btn', className="spin-button"),

        # アニメーション用
        dcc.Interval(id='timer', interval=60, n_intervals=0, disabled=True),
        dcc.Store(id='store-final-val'),
        dcc.Store(id='store-counter', data=0)
    ], className="card")
])

#--- コールバック ---

# 1. ボタンが押されたらアニメーション開始＆最終結果を決定
@app.callback(
    Output('timer', 'disabled'),
    Output('timer', 'n_intervals'),
    Output('store-final-val', 'data'),
    Output('store-counter', 'data'),
    Input('spin-btn', 'n_clicks'),
    State('cat-drop', 'value'),
    prevent_initial_call=True
)
def start_spin(n, cat):
    if not cat: return no_update, no_update, no_update, no_update
    
    choices = data_dict.get(cat, [])
    if not choices: return no_update, no_update, no_update, no_update
    
    final = random.choice(choices)
    return False, 0, final, 0

# 2. アニメーション処理（数字をパタパタ変える）
@app.callback(
    Output('display-text', 'children'),
    Output('timer', 'disabled', allow_duplicate=True),
    Input('timer', 'n_intervals'),
    State('store-final-val', 'data'),
    State('cat-drop', 'value'),
    State('store-counter', 'data'),
    prevent_initial_call=True
)
def update_animation(n, final, cat, counter):
    choices = data_dict.get(cat, [])
    
    # 25回シャッフルしたら終了
    if n < 25:
        return random.choice(choices), False
    else:
        return final, True

if __name__ == '__main__':
    app.run(jupyter_mode='inline')
