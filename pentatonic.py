import tkinter as tk
from tkinter import ttk, messagebox, font
from collections import Counter

# 音の基本的な対応表
# シャープとフラットの等価な関係を定義
ENHARMONIC_EQUIVALENTS = {
    "C#": "Db", "Db": "C#",
    "D#": "Eb", "Eb": "D#",
    "F#": "Gb", "Gb": "F#",
    "G#": "Ab", "Ab": "G#",
    "A#": "Bb", "Bb": "A#"
}

# シャープ表記の音名リスト（内部処理用）
NOTES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_TO_INT = {note: i for i, note in enumerate(NOTES_SHARP)}

# ドレミ表記（シャープとフラット両方）
SOLFEGE_SHARP = ["ド", "ド#", "レ", "レ#", "ミ", "ファ", "ファ#", "ソ", "ソ#", "ラ", "ラ#", "シ"]
SOLFEGE_FLAT = ["ド", "レb", "レ", "ミb", "ミ", "ファ", "ソb", "ソ", "ラb", "ラ", "シb", "シ"]


def get_root_and_type(code_name_raw):
    """
    入力されたコード名からルート音、マイナーかどうかの情報、その表記タイプ（シャープ/フラット/ナチュラル）を判定します。
    例: "Db" -> ("Db", True, "flat"), "C#" -> ("C#", True, "sharp"), "C" -> ("C", False, "natural")
    """
    if not code_name_raw:
        return None, None, None

    is_minor_chord = False
    root_part_candidate = ""

    # 'm' (マイナー)の有無をチェック
    if "m" in code_name_raw:
        m_index = code_name_raw.find("m")
        # 'm'が単独でマイナーを表す場合 (例: 'Cm', 'Dm7'の'm'はルート音の直後ではないので区別する)
        if m_index > 0 and (m_index + 1 == len(code_name_raw) or not code_name_raw[m_index + 1].isalpha()):
            is_minor_chord = True
            root_part_candidate = code_name_raw[:m_index] # 'm'より前の部分がルート音の候補
        else:
            root_part_candidate = code_name_raw # 'm'が別の意味を持つ場合（例: 'Maj7'など）は全体をルート音候補とする
    else:
        root_part_candidate = code_name_raw # 'm'がない場合は全体がルート音候補

    # 後ろから順にルート音を探す（例: 'C#maj7'の場合、'C#', 'C'の順に試す）
    for i in range(len(root_part_candidate), 0, -1):
        potential_root = root_part_candidate[:i]
        # 定義済みの音名リスト、または異名同音の対照表に存在するかチェック
        if potential_root in NOTES_SHARP or potential_root in ENHARMONIC_EQUIVALENTS:
            root_note_str = potential_root
            
            # ルート音の表記タイプを判定
            if '#' in root_note_str:
                notation_type = "sharp"
            elif 'b' in root_note_str or '♭' in root_note_str: # '♭'も考慮
                notation_type = "flat"
            else:
                notation_type = "natural"

            return root_note_str, is_minor_chord, notation_type

    # 1文字のナチュラル音名がルートの場合（例: 'Cmaj7'の'C'）
    if len(root_part_candidate) >= 1 and root_part_candidate[0] in NOTES_SHARP:
        root_note_str = root_part_candidate[0]
        return root_note_str, is_minor_chord, "natural"
    
    return None, None, None


def get_pentatonic_scale_notes(code_name_raw):
    """
    コード名からペンタトニックスケールの構成音をシャープ表記で取得し、
    元のコードのルート、マイナー情報、表記タイプを返します。
    """
    root_note_str_orig, is_minor_chord, notation_type = get_root_and_type(code_name_raw)

    if not root_note_str_orig:
        return None

    root_for_calc = root_note_str_orig
    # フラット表記のルート音の場合、シャープ表記に変換して計算に使う
    if 'b' in root_note_str_orig or '♭' in root_note_str_orig:
        root_for_calc = ENHARMONIC_EQUIVALENTS.get(root_note_str_orig, None)
        if root_for_calc is None:
            return None # 異名同音変換できない不正なフラット表記

    if root_for_calc not in NOTE_TO_INT:
        return None # 変換後のルート音が音名リストにない場合

    root_int = NOTE_TO_INT[root_for_calc]
    # メジャーペンタトニックとマイナーペンタトニックのインターバルを定義
    intervals = [0, 3, 5, 7, 10] if is_minor_chord else [0, 2, 4, 7, 9]
    
    # スケール構成音をシャープ表記で計算
    scale_notes_sharp = [NOTES_SHARP[(root_int + i) % 12] for i in intervals]
    
    return scale_notes_sharp, is_minor_chord, notation_type

def get_transposition_semitones(instrument_key):
    """
    移調楽器のキーに基づいて、実音から記譜音への半音のずれを返します。
    (記譜音 = 実音 + 半音のずれ)
    """
    key = instrument_key.strip().upper()
    transpositions = {
        "C": 0,   # C管 (実音と同じ)
        "BB": 2,  # B♭管 (実音より長2度高い記譜音)
        "B♭": 2, # B♭管 (記号表記も考慮)
        "EB": 9,  # E♭管 (実音より長6度高い記譜音)
        "E♭": 9, # E♭管 (記号表記も考慮)
        "F": 7,   # F管 (実音より完全4度高い記譜音)
    }
    return transpositions.get(key, None)

def get_solfege_name(note_name_sharp_or_flat, base_note_sharp="C"):
    """
    音名を基準音からの相対的な「ドレミ」表記に変換します。
    note_name_sharp_or_flat がシャープ表記かフラット表記かに応じて、適切なドレミ表記を返します。
    """
    
    is_flat_notation = False
    if 'b' in note_name_sharp_or_flat or '♭' in note_name_sharp_or_flat:
        is_flat_notation = True
    
    note_for_idx = note_name_sharp_or_flat
    # フラット表記の音符の場合、シャープ表記に変換してNOTE_TO_INTのインデックスを取得
    if is_flat_notation:
        note_for_idx = ENHARMONIC_EQUIVALENTS.get(note_name_sharp_or_flat, note_name_sharp_or_flat)

    # 変換後の音符がNOTE_TO_INTに存在しない場合はそのまま返す（エラーハンドリング）
    if note_for_idx not in NOTE_TO_INT:
        return note_name_sharp_or_flat

    note_index = NOTE_TO_INT[note_for_idx]
    base_index = NOTE_TO_INT.get(base_note_sharp, NOTE_TO_INT["C"]) # 基準音のインデックス

    # 基準音からの相対的なインデックスを計算（12で割った余り）
    relative_index = (note_index - base_index + 12) % 12
    
    # 元の音符がフラット表記であればSOLFEGE_FLATを使用、そうでなければSOLFEGE_SHARPを使用
    if is_flat_notation:
        return SOLFEGE_FLAT[relative_index]
    else:
        return SOLFEGE_SHARP[relative_index]

# --- GUI関連のグローバル変数 ---
MAX_MEASURES = 24 # 最大小節数
measure_widgets_to_destroy = [] # 動的に生成されるウィジェットを格納し、破棄するために使用
measure_vars = [] # コード入力欄のStringVarを格納

# コード選択肢のリスト
chord_options = [
    "", # 空欄を一番上に置く
    "C", "Cm", "C#", "C#m", "Db", "Dbm", "D", "Dm", "D#", "D#m", "Eb", "Ebm", "E", "Em", "F", "Fm",
    "F#", "F#m", "Gb", "Gbm", "G", "Gm", "G#", "G#m", "Ab", "Abm", "A", "Am", "A#", "A#m", "Bb", "Bbm", "B", "Bm"
]

measure_frame_id = None # measure_canvas内のmeasure_frameのIDを保持

def _update_scroll_region():
    """Canvasのスクロール領域を更新し、measure_frameの幅をCanvasに合わせます。"""
    global measure_frame_id
    measure_frame.update_idletasks() # ウィジェットの最新のサイズ・位置情報を取得

    canvas_width = measure_canvas.winfo_width()
    if canvas_width > 0:
        if measure_frame_id:
            # 既存のウィンドウアイテムがあれば幅を更新
            measure_canvas.itemconfigure(measure_frame_id, width=canvas_width)
        else:
            # まだウィンドウアイテムが作成されていなければ作成
            measure_frame_id = measure_canvas.create_window((0,0), window=measure_frame, anchor="nw", width=canvas_width)

    # measure_frameの位置を左上 (0,0) に設定
    measure_canvas.coords(measure_frame_id, 0, 0)
    # measure_canvasのスクロール領域をmeasure_frameの全範囲に設定
    measure_canvas.config(scrollregion=measure_canvas.bbox("all"))

def update_measure_inputs():
    """小節数選択に基づいて、コード入力欄を動的に更新します。"""
    # 既存のウィジェットを破棄
    for widgets_list_for_measure in measure_widgets_to_destroy:
        for widget in widgets_list_for_measure:
            widget.destroy()
    measure_widgets_to_destroy.clear()
    measure_vars.clear()

    num_measures = measure_count_var.get()
    try:
        num_measures = int(num_measures)
        if not (1 <= num_measures <= MAX_MEASURES):
            raise ValueError
    except ValueError:
        messagebox.showwarning("入力エラー", f"小節数は1から{MAX_MEASURES}の整数で入力してください。")
        measure_count_var.set(8) # デフォルト値に戻す
        num_measures = 8 # 処理を続行するためにデフォルト値を使用
        
    # 新しい小節入力欄を生成
    for i in range(num_measures):
        measure_label = ttk.Label(measure_frame, text=f"{i+1:2d}小節目:")
        measure_label.grid(row=i, column=0, padx=5, pady=2, sticky="w")

        chord1_var = tk.StringVar()
        chord1_combo = ttk.Combobox(measure_frame, textvariable=chord1_var, values=chord_options, width=8, state="readonly")
        chord1_combo.grid(row=i, column=1, padx=2, pady=2, sticky="w")
        chord1_combo.set(chord_options[0]) # 初期値を空欄に設定

        chord2_var = tk.StringVar()
        chord2_combo = ttk.Combobox(measure_frame, textvariable=chord2_var, values=chord_options, width=8, state="readonly")
        chord2_combo.grid(row=i, column=2, padx=2, pady=2, sticky="w")
        chord2_combo.set(chord_options[0]) # 初期値を空欄に設定

        # 破棄リストと変数リストに追加
        measure_widgets_to_destroy.append([measure_label, chord1_combo, chord2_combo])
        measure_vars.append([chord1_var, chord2_var])

    # Canvasのスクロール領域を更新するために、少し遅延させて呼び出す
    root.after(10, _update_scroll_region)

def display_welcome_message():
    """ウェルカムメッセージを結果表示エリアに表示します。"""
    result_text.delete("1.0", tk.END) # 結果表示エリアをクリア
    welcome_message = (
        "🎷 ペンタトニックスケール表示ツールへようこそ！\n\n"
        "このツールは、管楽器奏者のアドリブ演奏をサポートするために作られました。\n\n"
        "コード進行を入力すると、対応するペンタトニックスケール(5音)を、あなたの楽器の「記譜音」で『ドレミ』表記に変換して表示します。\n\n"
        "さらに、コード進行の中で特に多く登場する音を自動でハイライト！\n"
        "どの音からアドリブを始めればよいか迷ったときのヒントになります。\n\n"
        "ぜひ、練習や演奏にご活用ください。"
    )
    result_text.insert(tk.END, welcome_message)
    result_text.see(tk.END) # メッセージ全体が見えるようにスクロール

def run_analysis_gui():
    """GUIから入力された情報に基づいてスケール解析を実行し、結果を表示します。"""
    key = key_var.get().strip()
    transposition = get_transposition_semitones(key)

    # 以前のハイライトタグを削除
    for tag in result_text.tag_names():
        if tag.startswith("highlight_"):
            result_text.tag_delete(tag)
    result_text.delete("1.0", tk.END) # 結果表示エリアをクリア

    if not key:
        messagebox.showwarning("入力エラー", "楽器キーを選択してください。")
        display_welcome_message() # エラー後もウェルカムメッセージを表示
        return

    if transposition is None:
        messagebox.showwarning("キーエラー", "無効な楽器キーです。C, B♭, E♭, F のいずれかを選んでください。")
        display_welcome_message() # エラー後もウェルカムメッセージを表示
        return

    selected_measures_count = measure_count_var.get()
    try:
        selected_measures_count = int(selected_measures_count)
    except ValueError:
        messagebox.showwarning("入力エラー", "小節数が不正です。")
        display_welcome_message() # エラー後もウェルカムメッセージを表示
        return

    all_measures_data = []
    all_solfege_notes_for_counting = []
    
    # 各小節のコードデータを収集
    for i in range(selected_measures_count):
        if i < len(measure_vars):
            chord1 = measure_vars[i][0].get().strip()
            chord2 = measure_vars[i][1].get().strip()
            measure_chords = []
            if chord1: measure_chords.append(chord1)
            if chord2: measure_chords.append(chord2)
            all_measures_data.append(measure_chords)
        else:
            all_measures_data.append([]) # 小節数が減った場合に備えて空リストを追加

    # コードが全く入力されていない場合はメッセージを表示して終了
    if not any(chord_list for chord_list in all_measures_data if chord_list): 
        messagebox.showinfo("情報", "コード進行が選択されていません。")
        display_welcome_message() # コードが入力されていない場合はウェルカムメッセージを表示
        return

    # --- 全体の音の出現回数を事前にカウントするフェーズ ---
    for measure_chords in all_measures_data:
        for chord_name_raw in measure_chords:
            scale_data = get_pentatonic_scale_notes(chord_name_raw)
            if scale_data:
                scale_notes_sharp, is_minor_chord, notation_type = scale_data
                for note_sharp in scale_notes_sharp:
                    idx_sharp = NOTE_TO_INT[note_sharp]
                    transposed_idx = (idx_sharp + transposition) % 12
                    transposed_note_sharp = NOTES_SHARP[transposed_idx]
                    
                    note_for_solfege = transposed_note_sharp
                    
                    # 元のコードの表記タイプに合わせて、移調後の音名のドレミ表記を決定する
                    # マイナーペンタトニックの場合、ナチュラルルートでもフラット表記を優先するヒューリスティック
                    if notation_type == "flat" or (notation_type == "natural" and is_minor_chord):
                        note_for_solfege = ENHARMONIC_EQUIVALENTS.get(transposed_note_sharp, transposed_note_sharp)
                        # 例: Cmのペンタトニックに含まれるD#が移調後もD#だった場合、Ebとして扱う
                        if is_minor_chord:
                            if transposed_note_sharp == "D#": note_for_solfege = "Eb"
                            elif transposed_note_sharp == "G#": note_for_solfege = "Ab"
                            elif transposed_note_sharp == "A#": note_for_solfege = "Bb"

                    solfege_note = get_solfege_name(note_for_solfege)
                    all_solfege_notes_for_counting.append(solfege_note)
    
    note_counts = Counter(all_solfege_notes_for_counting)
    top_3_notes_info = note_counts.most_common(3) # 出現頻度の高い上位3つの音を取得

    highlight_colors_map = {}
    colors = ["red", "blue", "green"] # ハイライト色
    for i, (note, count) in enumerate(top_3_notes_info):
        if i < len(colors):
            highlight_colors_map[note] = colors[i]

    # ハイライトタグの設定
    for i, (note, color) in enumerate(highlight_colors_map.items()):
        tag_name = f"highlight_{i+1}"
        # フォント設定を共通のフォントで、太字にする
        # chosen_font_familyはグローバルスコープで定義されているためアクセス可能
        result_text.tag_config(tag_name, foreground=color, font=(chosen_font_family, 10, "bold")) 

    # --- 結果の表示フェーズ ---
    result_text.insert(tk.END, f"--- ペンタトニックスケール表示 --- 記譜音({key}管)\n\n") 
    
    for i, measure_chords in enumerate(all_measures_data):
        result_text.insert(tk.END, f" {i+1:2d}小節目:\n") 
        
        if not measure_chords:
            result_text.insert(tk.END, "  （コードなし）\n\n")
            continue # 次の小節へ

        for chord_name_raw in measure_chords:
            scale_data = get_pentatonic_scale_notes(chord_name_raw)

            if scale_data:
                scale_notes_sharp, is_minor_chord, notation_type = scale_data 
                
                solfege_notes_display = []
                for note_sharp in scale_notes_sharp:
                    idx_sharp = NOTE_TO_INT[note_sharp]
                    transposed_idx = (idx_sharp + transposition) % 12
                    transposed_note_sharp = NOTES_SHARP[transposed_idx]

                    note_for_solfege = transposed_note_sharp
                    
                    # ここでも、表示の際に元のコードの表記タイプを考慮
                    if notation_type == "flat" or (notation_type == "natural" and is_minor_chord):
                        note_for_solfege = ENHARMONIC_EQUIVALENTS.get(transposed_note_sharp, transposed_note_sharp)
                        if is_minor_chord: # マイナーの場合のD#, G#, A#の優先表示
                            if transposed_note_sharp == "D#": note_for_solfege = "Eb"
                            elif transposed_note_sharp == "G#": note_for_solfege = "Ab"
                            elif transposed_note_sharp == "A#": note_for_solfege = "Bb"

                    solfege_note = get_solfege_name(note_for_solfege)
                    solfege_notes_display.append(solfege_note)

                # scale_type = "マイナー" if is_minor_chord else "メジャー" # この行はもう不要です
                result_text.insert(tk.END, f"   {chord_name_raw}: ") # ここから変更
                
                # ドレミ音符をハイライト付きで表示
                for j, solfege_note in enumerate(solfege_notes_display):
                    tag = None
                    for k, (top_note, color) in enumerate(highlight_colors_map.items()):
                        if solfege_note == top_note:
                            tag = f"highlight_{k+1}"
                            break
                    
                    if tag:
                        result_text.insert(tk.END, solfege_note, tag)
                    else:
                        result_text.insert(tk.END, solfege_note)
                    
                    if j < len(solfege_notes_display) - 1:
                        result_text.insert(tk.END, " ")

                result_text.insert(tk.END, "\n")
            else:
                result_text.insert(tk.END, f"   {chord_name_raw}: 無効なコード\n")
        result_text.insert(tk.END, "\n")

    # --- 凡例の追加 ---
    if top_3_notes_info:
        result_text.insert(tk.END, "---\n")
        result_text.insert(tk.END, "【出現頻度の高い記譜音】\n")
        for i, (note, count) in enumerate(top_3_notes_info):
            if i < len(colors):
                tag_name = f"highlight_{i+1}"
                result_text.insert(tk.END, "   • ")
                result_text.insert(tk.END, note, tag_name)
                result_text.insert(tk.END, f" ({count}回出現)\n")
            else:
                break
        result_text.insert(tk.END, "\n")

    result_text.see(tk.END) # 結果の最後にスクロール


# --- GUI構築 ---
root = tk.Tk()
root.title("ペンタトニックスケール表示ツール（管楽器向け）")

# --- 色定義 ---
COLOR_MAIN_BG = "#F0F0F0"   # メインフレームの背景色（明るいグレー）
COLOR_FRAME_BG = "#FFFFFF"  # フレームの背景色（白）
COLOR_TEXT_FG = "#333333"   # 基本的な文字色（濃いグレー）
COLOR_BORDER = "#CCCCCC"    # フレームのボーダー色（中間のグレー）

# カスタムフォントを定義
try:
    # 優先的に使用したいフォントリスト
    font_families = ["Meiryo UI", "Yu Gothic UI", "Hiragino Sans", "Noto Sans CJK JP", "BIZ UDPGothic", "MS Gothic", "TkDefaultFont"]
    available_fonts = font.families() # システムで利用可能なフォントを取得
    
    chosen_font_family = ""
    # 利用可能なフォントの中から優先順位に従って選択
    for f_family in font_families:
        if f_family in available_fonts:
            chosen_font_family = f_family
            break
    
    # どれも利用できなければTkinterのデフォルトフォントを使用
    if not chosen_font_family:
        chosen_font_family = "TkDefaultFont"

    default_font_tuple = (chosen_font_family, 10) # デフォルトフォント設定
    text_widget_font_tuple = (chosen_font_family, 10) # Textウィジェット用のフォント設定

    # --- スタイルの設定 ---
    style = ttk.Style()
    
    # 全てのttkウィジェットのデフォルトフォントと色を設定
    style.configure(".", 
                    font=default_font_tuple,
                    background=COLOR_MAIN_BG,   # 全体の背景
                    foreground=COLOR_TEXT_FG)   # 全体の文字色

    # LabelFrameの背景色とボーダー色
    style.configure("TLabelframe", 
                    background=COLOR_MAIN_BG, # LabelFrame自体の背景はメインBGに合わせる
                    foreground=COLOR_TEXT_FG, # タイトル文字色
                    bordercolor=COLOR_BORDER, # ボーダー色
                    relief="solid") # ボーダースタイル
    style.configure("TLabelframe.Label", 
                    background=COLOR_MAIN_BG, # LabelFrameのタイトル部分の背景もメインBGに合わせる
                    foreground=COLOR_TEXT_FG) # LabelFrameのタイトル文字色

    # Frameの背景色
    style.configure("TFrame", 
                    background=COLOR_MAIN_BG)

    # Comboboxの背景色と文字色 (OSのテーマに強く依存するため、完全にコントロールは難しい場合も)
    style.map('TCombobox',
              fieldbackground=[('readonly', COLOR_FRAME_BG)], # 選択フィールドの背景
              selectbackground=[('readonly', COLOR_FRAME_BG)], # 選択時の背景
              selectforeground=[('readonly', COLOR_TEXT_FG)], # 選択時の文字色
              background=[('readonly', COLOR_FRAME_BG)], # ボタン部分の背景
              foreground=[('readonly', COLOR_TEXT_FG)]) # ボタン部分の文字色
    
    # Buttonの背景色と文字色
    style.configure("TButton", 
                    background="#E0E0E0", # ボタンの少し濃いめのグレー
                    foreground=COLOR_TEXT_FG,
                    padding=5) # パディングを追加してボタンを大きく見せる
    style.map("TButton", 
              background=[('active', '#D0D0D0')]) # ホバー時の色

    # スピンボックスの背景と文字色
    style.configure("TSpinbox",
                    fieldbackground=COLOR_FRAME_BG,
                    foreground=COLOR_TEXT_FG)

    # Labelの文字色 (すでにStyleで設定済みだが、明示的に指定する場合)
    style.configure("TLabel", 
                    background=COLOR_MAIN_BG,
                    foreground=COLOR_TEXT_FG)

except Exception as e:
    print(f"スタイル設定エラー: {e}。デフォルトのスタイルを使用します。")
    chosen_font_family = "TkDefaultFont" # エラー時はデフォルトに戻す
    default_font_tuple = (chosen_font_family, 10)
    text_widget_font_tuple = (chosen_font_family, 10)
    style = ttk.Style()
    style.configure(".", font=default_font_tuple)


# メインフレームの背景色を設定
main_frame = ttk.Frame(root, padding=15, style="TFrame") # styleを指定
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
root.columnconfigure(0, weight=1) # メインウィンドウの列1を伸縮可能にする
main_frame.columnconfigure(0, weight=1) # メインフレームの左列を伸縮可能にする
main_frame.columnconfigure(1, weight=2) # メインフレームの右列（結果表示）をより伸縮可能にする
root.rowconfigure(0, weight=0) # 上部コントロールは伸縮しない
root.rowconfigure(1, weight=1) # 下部（入力と結果）は伸縮可能にする

# 上部コントロールフレーム
control_frame = ttk.LabelFrame(main_frame, text="設定", padding=10, style="TLabelframe")
control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5) 

ttk.Label(control_frame, text="小節数:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
measure_count_var = tk.StringVar(value=8) # 小節数のStringVarを初期化（ここを8に変更）
measure_count_spinbox = ttk.Spinbox(control_frame, from_=1, to=MAX_MEASURES, textvariable=measure_count_var, command=update_measure_inputs, width=5)
measure_count_spinbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)

ttk.Label(control_frame, text="楽器キー:").grid(row=0, column=2, sticky="w", padx=15, pady=5)
key_var = tk.StringVar(value="C") # 楽器キーのStringVarを初期化
key_combo = ttk.Combobox(control_frame, textvariable=key_var, values=["C", "Bb", "Eb", "F"], width=10, state="readonly")
key_combo.grid(row=0, column=3, sticky="w", padx=5, pady=5)

ttk.Button(control_frame, text="スケールを表示", command=run_analysis_gui).grid(row=0, column=4, padx=20, pady=5)


# コード入力フレーム (スクロール可能)
input_frame = ttk.LabelFrame(main_frame, text="コード進行入力（1小節2コードまで）", padding=10, style="TLabelframe")
input_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W, tk.E), pady=5, padx=(0, 5)) 
input_frame.rowconfigure(0, weight=1) # Canvasを伸縮可能にする
input_frame.columnconfigure(0, weight=1) # Canvasを伸縮可能にする

# Canvasの背景色をCOLOR_MAIN_BGに設定
measure_canvas = tk.Canvas(input_frame, height=400, highlightthickness=0, bg=COLOR_MAIN_BG) 
measure_canvas.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))

measure_scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=measure_canvas.yview)
measure_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
measure_canvas.configure(yscrollcommand=measure_scrollbar.set)

# measure_frameの背景色も設定 (これは既にCOLOR_MAIN_BGが適用されるようにスタイル設定されています)
measure_frame = ttk.Frame(measure_canvas, style="TFrame") 

# measure_frameをCanvas内に作成するが、_update_scroll_region()で動的に行う
measure_frame_id = None 

# Canvasのリサイズイベント時にスクロール領域を更新するためのバインド
def _on_canvas_configure(event):
    _update_scroll_region()

measure_canvas.bind('<Configure>', _on_canvas_configure)


# 結果表示エリア
result_frame = ttk.LabelFrame(main_frame, text="解析結果", padding=10, style="TLabelframe")
result_frame.grid(row=1, column=1, sticky=(tk.N, tk.S, tk.W, tk.E), padx=(5,0), pady=5) 
result_frame.rowconfigure(0, weight=1) # Textウィジェットを伸縮可能にする
result_frame.columnconfigure(0, weight=1) # Textウィジェットを伸縮可能にする

# result_textのフォントと背景・文字色を設定
result_text = tk.Text(result_frame, height=20, width=60, wrap="word", 
                      font=text_widget_font_tuple, bg=COLOR_FRAME_BG, fg=COLOR_TEXT_FG)
result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

result_scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=result_text.yview)
result_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
result_text.configure(yscrollcommand=result_scrollbar.set)


# --- 初期状態の小節入力欄を生成 ---
# GUIの初期化が完了した後にupdate_measure_inputsを呼び出すため、少し遅延させる
root.after(100, update_measure_inputs) 
# --- アプリケーション起動時にウェルカムメッセージを表示 ---
root.after(150, display_welcome_message) 

root.mainloop()