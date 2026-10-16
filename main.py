import os
import json
import re
import random
import threading
import time
from datetime import datetime
import urllib.request
import flet as ft

# -------------------------------------------------------------
# GitHub Raw URL for Manual Question Updates
# -------------------------------------------------------------
GITHUB_RAW_URL = "https://raw.githubusercontent.com/kenyaulung-commits/FS2I/main/questions.json"

def main(page: ft.Page):
    page.title = "FS2I 中文學習 App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "questions.json")
    history_path = os.path.join(base_dir, "history.json")

    status_text = ft.Text(value="離線模式：已載入本機預存題目。", size=13, color="white", weight="bold")

    # -------------------------------------------------------------
    # 1. PLAY HISTORY MANAGEMENT
    # -------------------------------------------------------------
    history_list = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8)
    history_container = ft.Container(content=history_list, height=220)

    def load_history():
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_history_entry(quiz_name, score, total):
        history = load_history()
        entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "quiz": quiz_name,
            "score": f"{score} / {total} ({int((score/total)*100) if total else 0}%)"
        }
        history.insert(0, entry)  # Newest first
        history = history[:30]    # Keep last 30 entries
        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def refresh_history_ui():
        history_list.controls.clear()
        records = load_history()
        if not records:
            history_list.controls.append(
                ft.Text("尚無遊玩紀錄", color=ft.Colors.GREY_600, size=14)
            )
        else:
            for item in records:
                history_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(f"⏱ {item['time']}", size=12, color=ft.Colors.GREY_700),
                                ft.Text(f"🎮 {item['quiz']}", size=12, weight="bold", color=ft.Colors.BLUE_800),
                            ], alignment="spaceBetween"),
                            ft.Text(f"答對：{item['score']}", size=14, weight="bold", color=ft.Colors.GREEN_700)
                        ], spacing=3),
                        padding=8,
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=8
                    )
                )

    # -------------------------------------------------------------
    # 2. LOCAL-FIRST QUESTION DATA LOADING
    # -------------------------------------------------------------
    def load_local_questions():
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading local JSON: {e}")
        return {"fill_in_blank": [], "punctuation": {"available_marks": [], "questions": []}}

    data_store = {"data": load_local_questions()}

    # -------------------------------------------------------------
    # 3. SETTINGS OVERLAY & GITHUB SYNC
    # -------------------------------------------------------------
    def manual_github_sync(e):
        sync_btn.disabled = True
        sync_status.value = "連線 GitHub 下載中..."
        sync_status.color = "blue"
        settings_dialog.update()

        try:
            req = urllib.request.Request(GITHUB_RAW_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    raw_json = response.read().decode("utf-8")
                    new_data = json.loads(raw_json)
                    with open(json_path, "w", encoding="utf-8") as f:
                        f.write(raw_json)
                    data_store["data"] = new_data
                    status_text.value = "已成功連線 GitHub 更新至最新題目！"
                    sync_status.value = "✅ 題目更新成功！"
                    sync_status.color = "green"
                    reset_fib()
        except Exception as err:
            sync_status.value = f"❌ 更新失敗：{err}"
            sync_status.color = "red"

        sync_btn.disabled = False
        settings_dialog.update()
        page.update()

    sync_btn = ft.Button(content=ft.Text("連線 GitHub 更新題目"), icon=ft.Icons.REFRESH, on_click=manual_github_sync)
    sync_status = ft.Text(value="", size=12, weight="bold")

    settings_dialog = ft.AlertDialog(
        title=ft.Row([
            ft.Icon(ft.Icons.SETTINGS, color=ft.Colors.BLUE_600),
            ft.Text("設定與遊玩紀錄", weight="bold", size=20)
        ]),
        content=ft.Container(
            content=ft.Column([
                ft.Text("1. 題目更新", size=16, weight="bold", color=ft.Colors.BLUE_800),
                sync_btn,
                sync_status,
                ft.Divider(),
                ft.Text("2. 遊玩紀錄 (Time / Quiz / Score)", size=16, weight="bold", color=ft.Colors.BLUE_800),
                history_container
            ], spacing=10, tight=True),
            width=320
        ),
        actions=[
            ft.TextButton("關閉", on_click=lambda e: page.close(settings_dialog))
        ]
    )

    def open_settings(e):
        refresh_history_ui()
        sync_status.value = ""
        page.open(settings_dialog)

    # -------------------------------------------------------------
    # 4. EXERCISE 1: Fill in the Blank (選詞填空) - RANDOMIZED
    # -------------------------------------------------------------
    fib_idx = 0
    fib_score = 0
    fib_questions = []
    selected_choice = ""

    question_text = ft.Text(value="", size=22, weight="bold", text_align="center")
    options_row = ft.Row(alignment="center", spacing=10)
    fib_feedback = ft.Text(value="", size=18, weight="bold")

    def parse_fib_question(raw_text):
        match = re.search(r'[（\(](.*?)[）\)]', raw_text)
        if match:
            options = re.split(r'[／/]', match.group(1))
            prefix = raw_text[:match.start()]
            suffix = raw_text[match.end():]
            return prefix, options, suffix
        return raw_text, [], ""

    def load_fib_question():
        nonlocal selected_choice
        selected_choice = ""
        fib_feedback.value = ""
        options_row.controls.clear()

        if fib_idx >= len(fib_questions):
            show_fib_results()
            return

        q = fib_questions[fib_idx]
        prefix, options, suffix = parse_fib_question(q["text"])
        question_text.value = f"第 {fib_idx + 1} / {len(fib_questions)} 題：\n{prefix} [ ___ ] {suffix}"

        for opt in options:
            def make_click_handler(choice):
                return lambda e: select_option(choice, prefix, suffix)

            options_row.controls.append(
                ft.Button(content=ft.Text(opt, size=18), on_click=make_click_handler(opt))
            )
        page.update()

    def select_option(choice, prefix, suffix):
        nonlocal selected_choice
        selected_choice = choice
        question_text.value = f"第 {fib_idx + 1} / {len(fib_questions)} 題：\n{prefix} [ {choice} ] {suffix}"
        page.update()

    def next_fib_question(e):
        nonlocal fib_idx, fib_score
        if not selected_choice:
            fib_feedback.value = "請先選擇一個答案！"
            fib_feedback.color = "red"
            page.update()
            return

        correct_answer = fib_questions[fib_idx]["answer"]
        if selected_choice == correct_answer:
            fib_score += 1
            fib_idx += 1
            if fib_idx < len(fib_questions):
                load_fib_question()
            else:
                show_fib_results()
        else:
            fib_feedback.value = "答錯了！請再試一次！"
            fib_feedback.color = "red"
            page.update()

    def show_fib_results():
        save_history_entry("選詞填空", fib_score, len(fib_questions))
        fib_view.controls.clear()
        pct = int((fib_score / len(fib_questions)) * 100) if fib_questions else 0
        
        fib_view.controls.extend([
            ft.Container(
                content=ft.Column([
                    ft.Text("🎉 恭喜完成測驗！ 🎉", size=26, weight="bold", color=ft.Colors.AMBER_900),
                    ft.Text("🏆 選詞填空 挑戰成功！", size=20, weight="bold", color=ft.Colors.BLUE_800),
                    ft.Divider(),
                    ft.Text(f"最終得分：{fib_score} / {len(fib_questions)}", size=24, weight="bold", color=ft.Colors.GREEN_700),
                    ft.Text(f"正確率：{pct}%", size=20, weight="bold", color=ft.Colors.BLUE_700),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Button(
                        content=ft.Text("再玩一次 (隨機重組)", size=18, weight="bold"),
                        style=ft.ButtonStyle(padding=15),
                        on_click=lambda e: reset_fib()
                    )
                ], horizontal_alignment="center", spacing=10),
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12)
            )
        ])
        page.update()

    def reset_fib():
        nonlocal fib_idx, fib_score, fib_questions
        raw_list = data_store["data"].get("fill_in_blank", [])
        fib_questions = random.sample(raw_list, len(raw_list)) if raw_list else []
        fib_idx = 0
        fib_score = 0
        fib_view.controls.clear()
        fib_view.controls.extend([
            question_text,
            options_row,
            fib_feedback,
            ft.Button(content=ft.Text("下一題", size=20), on_click=next_fib_question)
        ])
        load_fib_question()

    fib_view = ft.Column([
        question_text,
        options_row,
        fib_feedback,
        ft.Button(content=ft.Text("下一題", size=20), on_click=next_fib_question)
    ], alignment="center", horizontal_alignment="center", spacing=20)

    # -------------------------------------------------------------
    # 5. EXERCISE 2: Punctuation Marks (標點符號) - RANDOMIZED
    # -------------------------------------------------------------
    punc_idx = 0
    punc_score = 0
    p_questions = []
    active_mark = None
    user_slots = []

    palette_row = ft.Row(alignment="center", spacing=8)
    sentence_row = ft.Row(alignment="center", spacing=5, wrap=True)
    punc_feedback = ft.Text(value="", size=18, weight="bold")

    def load_punc_question():
        nonlocal active_mark, user_slots
        active_mark = None
        punc_feedback.value = ""
        palette_row.controls.clear()
        sentence_row.controls.clear()

        if punc_idx >= len(p_questions):
            show_punc_results()
            return

        punc_data = data_store["data"].get("punctuation", {"available_marks": [], "questions": []})
        for mark in punc_data.get("available_marks", []):
            def make_mark_handler(m):
                return lambda e: select_mark(m)
            palette_row.controls.append(
                ft.Button(content=ft.Text(mark, size=18), on_click=make_mark_handler(mark))
            )

        q_text = p_questions[punc_idx]["text"]
        segments = re.split(r'[（\(][）\)]', q_text)
        user_slots = [""] * (len(segments) - 1)

        for i, seg in enumerate(segments):
            if seg:
                sentence_row.controls.append(ft.Text(value=seg, size=20))
            if i < len(segments) - 1:
                def make_slot_handler(slot_i):
                    return lambda e: fill_slot(e.control, slot_i)
                sentence_row.controls.append(
                    ft.Button(content=ft.Text("[   ]", size=18), on_click=make_slot_handler(i))
                )
        page.update()

    def select_mark(m):
        nonlocal active_mark
        active_mark = m
        punc_feedback.value = f"已選擇：『 {active_mark} 』，點擊空格填入"
        punc_feedback.color = "blue"
        page.update()

    def fill_slot(btn_control, idx):
        if active_mark:
            user_slots[idx] = active_mark
            btn_control.content = ft.Text(f"[ {active_mark} ]", size=18)
        else:
            punc_feedback.value = "請先點選上方的標點符號！"
            punc_feedback.color = "red"
        page.update()

    def next_punc_question(e):
        nonlocal punc_idx, punc_score
        expected = p_questions[punc_idx]["answers"]

        if user_slots == expected:
            punc_score += 1
            punc_idx += 1
            if punc_idx < len(p_questions):
                load_punc_question()
            else:
                show_punc_results()
        else:
            punc_feedback.value = "填寫有誤，請再試一次！"
            punc_feedback.color = "red"
            page.update()

    def show_punc_results():
        save_history_entry("標點符號", punc_score, len(p_questions))
        punc_view.controls.clear()
        pct = int((punc_score / len(p_questions)) * 100) if p_questions else 0

        punc_view.controls.extend([
            ft.Container(
                content=ft.Column([
                    ft.Text("🎉 恭喜完成測驗！ 🎉", size=26, weight="bold", color=ft.Colors.AMBER_900),
                    ft.Text("🏆 標點符號 挑戰成功！", size=20, weight="bold", color=ft.Colors.BLUE_800),
                    ft.Divider(),
                    ft.Text(f"最終得分：{punc_score} / {len(p_questions)}", size=24, weight="bold", color=ft.Colors.GREEN_700),
                    ft.Text(f"正確率：{pct}%", size=20, weight="bold", color=ft.Colors.BLUE_700),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Button(
                        content=ft.Text("再玩一次 (隨機重組)", size=18, weight="bold"),
                        style=ft.ButtonStyle(padding=15),
                        on_click=lambda e: reset_punc()
                    )
                ], horizontal_alignment="center", spacing=10),
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12)
            )
        ])
        page.update()

    def reset_punc():
        nonlocal punc_idx, punc_score, p_questions
        punc_data = data_store["data"].get("punctuation", {"available_marks": [], "questions": []})
        raw_list = punc_data.get("questions", [])
        p_questions = random.sample(raw_list, len(raw_list)) if raw_list else []
        punc_idx = 0
        punc_score = 0
        punc_view.controls.clear()
        punc_view.controls.extend([
            ft.Text(value="選擇標點符號：", size=16),
            palette_row,
            ft.Divider(),
            sentence_row,
            punc_feedback,
            ft.Button(content=ft.Text("下一題", size=20), on_click=next_punc_question)
        ])
        load_punc_question()

    punc_view = ft.Column([
        ft.Text(value="選擇標點符號：", size=16),
        palette_row,
        ft.Divider(),
        sentence_row,
        punc_feedback,
        ft.Button(content=ft.Text("下一題", size=20), on_click=next_punc_question)
    ], alignment="center", horizontal_alignment="center", spacing=20)

    # -------------------------------------------------------------
    # 6. NAVIGATION & TOP BAR WITH SETTINGS ICON
    # -------------------------------------------------------------
    view_container = ft.Container(content=fib_view)

    def switch_to_fib(e):
        reset_fib()
        view_container.content = fib_view
        page.update()

    def switch_to_punc(e):
        reset_punc()
        view_container.content = punc_view
        page.update()

    top_header = ft.Row([
        ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_color=ft.Colors.WHITE,
            tooltip="設定與紀錄",
            on_click=open_settings
        ),
        status_text
    ], alignment="spaceBetween")

    nav_row = ft.Row([
        ft.Button(content=ft.Text("選詞填空"), on_click=switch_to_fib),
        ft.Button(content=ft.Text("標點符號"), on_click=switch_to_punc)
    ], alignment="center", spacing=15)

    # -------------------------------------------------------------
    # 7. BOTTOM ANIMATION: MARIO & YOSHI WANDERING
    # -------------------------------------------------------------
    mario_yoshi_sprite = ft.Row([
        ft.Text("🔴 🏃‍♂️ Mario", size=16, weight="bold", color=ft.Colors.RED_700),
        ft.Text("🟢 🦖 Yoshi", size=16, weight="bold", color=ft.Colors.GREEN_700),
    ], spacing=15)

    wander_container = ft.Container(
        content=mario_yoshi_sprite,
        offset=ft.Offset(0, 0),
        animate_offset=ft.Animation(3000, ft.AnimationCurve.EASE_IN_OUT),
        padding=ft.padding.only(top=10, bottom=10)
    )

    def start_wandering_loop():
        def loop():
            pos = 0
            while True:
                time.sleep(3.2)
                try:
                    pos = 0.8 if pos == 0 else 0
                    wander_container.offset = ft.Offset(pos, 0)
                    page.update()
                except Exception:
                    break

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()

    # -------------------------------------------------------------
    # MAIN WRAPPER ASSEMBLY
    # -------------------------------------------------------------
    bg_image_path = os.path.join(base_dir, "assets", "bg.jpg")

    main_wrapper = ft.Container(
        content=ft.Column([
            top_header,
            nav_row,
            ft.Divider(),
            view_container,
            ft.Divider(),
            wander_container
        ], horizontal_alignment="center", alignment="spaceBetween"),
        padding=ft.Padding(left=15, top=40, right=15, bottom=10),
        expand=True,
        image=ft.DecorationImage(
            src="bg.jpg",
            fit="cover"
        ) if os.path.exists(bg_image_path) else None
    )

    page.add(main_wrapper)
    reset_fib()
    start_wandering_loop()

ft.run(main, assets_dir="assets")
