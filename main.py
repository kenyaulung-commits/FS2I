import os
import json
import re
import time
import urllib.request
import flet as ft
import flet_audio as fta  # Official Flet audio package

GITHUB_RAW_URL = "https://raw.githubusercontent.com/kenyaulung-commits/FS2I/main/questions.json"

def main(page: ft.Page):
    page.title = "FS2I 中文學習 App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "questions.json")

    status_text = ft.Text(value="", size=14, color="white", weight="bold")

    # -------------------------------------------------------------
    # Audio Setup with flet_audio
    # -------------------------------------------------------------
    audio_success = fta.Audio(src="success.mp3", autoplay=False)
    audio_fail = fta.Audio(src="fail.mp3", autoplay=False)
    page.overlay.extend([audio_success, audio_fail])

    def play_sound_and_wait(audio_control):
    try:
        # Schedule the async play method on Flet's event loop
        page.run_task(audio_control.play)
    except Exception as e:
        print(f"Audio error: {e}")
    time.sleep(0.5)

    # -------------------------------------------------------------
    # Online Question Source Sync Logic
    # -------------------------------------------------------------
    def load_questions_data():
        try:
            req = urllib.request.Request(GITHUB_RAW_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=4) as response:
                if response.status == 200:
                    raw_json = response.read().decode("utf-8")
                    data = json.loads(raw_json)
                    with open(json_path, "w", encoding="utf-8") as f:
                        f.write(raw_json)
                    status_text.value = "已成功連線 GitHub 更新至最新題目！"
                    return data
        except Exception:
            pass

        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                status_text.value = "離線模式：已載入本機預存題目。"
                return json.load(f)
        
        return {"fill_in_blank": [], "punctuation": {"available_marks": [], "questions": []}}

    data = load_questions_data()

    # -------------------------------------------------------------
    # EXERCISE 1: Fill in the Blank (選詞填空)
    # -------------------------------------------------------------
    fib_idx = 0
    fib_questions = data.get("fill_in_blank", [])
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
            question_text.value = "測驗完成！太棒了！"
            page.update()
            return

        q = fib_questions[fib_idx]
        prefix, options, suffix = parse_fib_question(q["text"])
        question_text.value = f"{prefix} [ ___ ] {suffix}"

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
        question_text.value = f"{prefix} [ {choice} ] {suffix}"
        page.update()

    def next_fib_question(e):
        nonlocal fib_idx
        if not selected_choice:
            fib_feedback.value = "請先選擇一個答案！"
            fib_feedback.color = "red"
            page.update()
            return

        correct_answer = fib_questions[fib_idx]["answer"]
        if selected_choice == correct_answer:
            fib_feedback.value = "答對了！非常棒！"
            fib_feedback.color = "green"
            page.update()
            play_sound_and_wait(audio_success)

            if fib_idx < len(fib_questions) - 1:
                fib_idx += 1
                load_fib_question()
            else:
                question_text.value = "選詞填空練習全數完成！"
                options_row.controls.clear()
                page.update()
        else:
            fib_feedback.value = "答錯了！請再試一次！"
            fib_feedback.color = "red"
            page.update()
            play_sound_and_wait(audio_fail)

    fib_view = ft.Column([
        question_text,
        options_row,
        fib_feedback,
        ft.Button(content=ft.Text("下一題", size=20), on_click=next_fib_question)
    ], alignment="center", horizontal_alignment="center", spacing=20)

    # -------------------------------------------------------------
    # EXERCISE 2: Punctuation Marks (標點符號)
    # -------------------------------------------------------------
    punc_idx = 0
    punc_data = data.get("punctuation", {"available_marks": [], "questions": []})
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

        p_questions = punc_data.get("questions", [])
        if punc_idx >= len(p_questions):
            punc_feedback.value = "所有標點練習已完成！"
            page.update()
            return

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
        nonlocal punc_idx
        p_questions = punc_data.get("questions", [])
        expected = p_questions[punc_idx]["answers"]

        if user_slots == expected:
            punc_feedback.value = "全對了！標點符號用得很準確！"
            punc_feedback.color = "green"
            page.update()
            play_sound_and_wait(audio_success)

            if punc_idx < len(p_questions) - 1:
                punc_idx += 1
                load_punc_question()
            else:
                punc_feedback.value = "標點符號練習全數完成！"
                page.update()
        else:
            punc_feedback.value = "填寫有誤，請再試一次！"
            punc_feedback.color = "red"
            page.update()
            play_sound_and_wait(audio_fail)

    punc_view = ft.Column([
        ft.Text(value="選擇標點符號：", size=16),
        palette_row,
        ft.Divider(),
        sentence_row,
        punc_feedback,
        ft.Button(content=ft.Text("下一題", size=20), on_click=next_punc_question)
    ], alignment="center", horizontal_alignment="center", spacing=20)

    # -------------------------------------------------------------
    # Navigation & View Switcher
    # -------------------------------------------------------------
    view_container = ft.Container(content=fib_view)

    def switch_to_fib(e):
        view_container.content = fib_view
        page.update()

    def switch_to_punc(e):
        view_container.content = punc_view
        page.update()

    nav_row = ft.Row([
        ft.Button(content=ft.Text("選詞填空"), on_click=switch_to_fib),
        ft.Button(content=ft.Text("標點符號"), on_click=switch_to_punc)
    ], alignment="center", spacing=15)

    bg_image_path = os.path.join(base_dir, "assets", "bg.jpg")

    main_wrapper = ft.Container(
        content=ft.Column([
            status_text,
            nav_row,
            ft.Divider(),
            view_container
        ], horizontal_alignment="center"),
        padding=ft.Padding(left=20, top=60, right=20, bottom=20),
        expand=True,
        image=ft.DecorationImage(
            src="bg.jpg",
            fit="cover"
        ) if os.path.exists(bg_image_path) else None
    )

    page.add(main_wrapper)
    load_fib_question()
    load_punc_question()

ft.run(main, assets_dir="assets")
