import pandas as pd
import glob
import random
import json
from dash import Dash, dcc, html, Input, Output, State, no_update, callback_context

#--- データの読み込み ---
def load_data():
    all_files = glob.glob("*.csv")
    category_map = {}
    for filename in all_files:
        try:
            # 最新のCSV構造(A列:カテゴリー, B列:数字)を想定
            df = pd.read_csv(filename, header=None)
            current_cat = None
            for _, row in df.iterrows():
                cat_val = row.iloc[0]
                num_val = row.iloc[1]
                
                # A列に値があればカテゴリーを更新
                if pd.notna(cat_val) and str(cat_val).strip() != "":
                    current_cat = str(cat_val).strip()
                    if current_cat not in category_map:
                        category_map[current_cat] = []
                
                # 数字をリストに追加（カンマなどを除去）
                if current_cat and pd.notna(num_val):
                    clean_num = str(num_val).replace(',', '').strip()
                    if clean_num:
                        category_map[current_cat].append(clean_num)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue
    return category_map

# データ準備
data_dict = load_data()
categories = sorted(list(data_dict.keys()))

#--- アプリの作成 ---
app = Dash(__name__)
server = app.server

# カスタムCSS/フォントの適用
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Premium Roulette</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Montserrat:wght@800&display=swap" rel="stylesheet">
        <style>
            body {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                font-family: 'Noto Sans JP', sans-serif;
                margin: 0;
            }
            .main-container {
                max-width: 600px;
                margin: 50px auto;
                background: white;
                padding: 40px;
                border-radius: 24px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                text-align: center;
            }
            .roulette-display {
                height: 180px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 30px 0;
                background: #f8f9fa;
                border-radius: 16px;
                border: 2px dashed #dee2e6;
                position: relative;
                overflow: hidden;
            }
            .result-number {
                font-family: 'Montserrat', sans-serif;
                font-size: 80px;
                color: #2c3e50;
                font-weight: 800;
                transition: all 0.3s ease;
            }
            .spin-button {
                background: linear-gradient(to right, #6a11cb 0%, #2575fc 100%);
                color: white;
                border: none;
                padding: 18px 60px;
                font-size: 24px;
                font-weight: bold;
                border-radius: 50px;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                width: 100%;
                margin-top: 20px;
            }
            .spin-button:hover {
                transform: scale(1.02);
                box-shadow: 0 10px 20px rgba(37, 117, 252, 0.3);
            }
            .spin-button:active {
                transform: scale(0.98);
            }
            .dropdown-container {
                text-align: left;
                margin-bottom: 20px;
            }
            .label {
                font-weight: bold;
                color: #495057;
                margin-bottom: 8px;
                display: block;
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
        html.H1("PREMIUM ROULETTE", style={'letterSpacing': '3px', 'color': '#1a1a1a'}),
        html.P("カテゴリーを選んでルーレットをスタート", style={'color': '#6c757d'}),
        
        html.Div([
            html.Span("1. CATEGORY", className="label"),
            dcc.Dropdown(
                id='category-dropdown',
                options=[{'label': k, 'value': k} for k in categories],
                placeholder="リストから選択...",
            ),
        ], className="dropdown-container"),

        # ルーレット表示部
        html.Div([
            html.Div(id='result-display', className="result-number", children="---")
        ], className="roulette-display"),

        html.Button('START SPIN', id='spin-button', n_clicks=0, className="spin-button"),
        
        # インターバルコンポーネント（アニメーション用）
        dcc.Interval(id='anim-interval', interval=80, n_intervals=0, disabled=True),
        dcc.Store(id='anim-counter', data=0),
        dcc.Store(id='final-choice', data="")

    ], className="main-container")
])

#--- コールバック ---

# ボタンクリックでアニメーション開始
@app.callback(
    Output('anim-interval', 'disabled'),
    Output('anim-counter', 'data'),
    Output('final-choice', 'data'),
    Input('spin-button', 'n_clicks'),
    State('category-dropdown', 'value'),
    prevent_initial_call=True
)
def start_animation(n_clicks, selected_cat):
    if not selected_cat:
        return no_update, no_update, no_update
    
    choices = data_dict.get(selected_cat, [])
    if not choices:
        return no_update, no_update, no_update
    
    final = random.choice(choices)
    return False, 0, final

# アニメーション中の数字切り替えと終了判定
@app.callback(
    Output('result-display', 'children'),
    Output('anim-interval', 'disabled', allow_duplicate=True),
    Output('anim-counter', 'data', allow_duplicate=True),
    Input('anim-interval', 'n_intervals'),
    State('anim-counter', 'data'),
    State('final-choice', 'data'),
    State('category-dropdown', 'value'),
    prevent_initial_call=True
)
def update_animation(n_intervals, counter, final, selected_cat):
    choices = data_dict.get(selected_cat, [])
    
    # 20回（約1.6秒）シャッフルして最後に本物を出す
    if counter < 20:
        return random.choice(choices), False, counter + 1
    else:
        return final, True, 0

if __name__ == '__main__':
    # サーバーデプロイ時は app.run() は不要だが、Colabテスト用に残す場合は以下
    app.run(jupyter_mode='inline')
