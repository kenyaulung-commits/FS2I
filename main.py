import json
import re
import flet as ft

def main(page: ft.Page):
    page.title = "中文學習 App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Load questions data
    with open("questions.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # -------------------------------------------------------------
    # EXERCISE 1: Fill in the Blank (選詞填空)
    # -------------------------------------------------------------
    fib_idx = 0
    fib_questions = data["fill_in_blank"]
    selected_choice = ""

    question_text = ft.Text(value="", size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    options_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=10)
    fib_feedback = ft.Text(value="", size=18)

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
            question_text.value = "測驗完成！"
            page.update()
            return

        q = fib_questions[fib_idx]
        prefix, options, suffix = parse_fib_question(q["text"])
        question_text.value = f"{prefix} [ ___ ] {suffix}"

        for opt in options:
            def make_click_handler(choice):
                return lambda e: select_option(choice, prefix, suffix)

            options_row.controls.append(
                ft.ElevatedButton(text=opt, on_click=make_click_handler(opt))
            )
        page.update()

    def select_option(choice, prefix, suffix):
        nonlocal selected_choice
        selected_choice = choice
        question_text.value = f"{prefix} [ {choice} ] {suffix}"
        page.update()

    def check_fib_answer(e):
        if not selected_choice:
            fib_feedback.value = "請先選擇一個答案！"
        elif selected_choice == fib_questions[fib_idx]["answer"]:
            fib_feedback.value = "答對了！非常棒！"
        else:
            fib_feedback.value = f"再試一次！正確答案是：{fib_questions[fib_idx]['answer']}"
        page.update()

    def next_fib_question(e):
        nonlocal fib_idx
        if fib_idx < len(fib_questions) - 1:
            fib_idx += 1
            load_fib_question()
        else:
            fib_feedback.value = "已經是最後一題了！"
            page.update()

    fib_view = ft.Column([
        question_text,
        options_row,
        fib_feedback,
        ft.Row([
            ft.ElevatedButton("檢查答案", on_click=check_fib_answer),
            ft.ElevatedButton("下一題", on_click=next_fib_question)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=15)
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)

    # -------------------------------------------------------------
    # EXERCISE 2: Punctuation Marks (標點符號)
    # -------------------------------------------------------------
    punc_idx = 0
    punc_data = data["punctuation"]
    active_mark = None
    user_slots = []

    palette_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=8)
    sentence_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=5, wrap=True)
    punc_feedback = ft.Text(value="", size=18)

    def load_punc_question():
        nonlocal active_mark, user_slots
        active_mark = None
        punc_feedback.value = ""
        palette_row.controls.clear()
        sentence_row.controls.clear()

        if punc_idx >= len(punc_data["questions"]):
            punc_feedback.value = "所有標點練習已完成！"
            page.update()
            return

        # Render available symbols bar
        for mark in punc_data["available_marks"]:
            def make_mark_handler(m):
                return lambda e: select_mark(m)
            palette_row.controls.append(
                ft.OutlinedButton(text=mark, on_click=make_mark_handler(mark))
            )

        # Render sentence and slot buttons
        q_text = punc_data["questions"][punc_idx]["text"]
        segments = re.split(r'[（\(][）\)]', q_text)
        user_slots = [""] * (len(segments) - 1)

        for i, seg in enumerate(segments):
            if seg:
                sentence_row.controls.append(ft.Text(value=seg, size=20))
            if i < len(segments) - 1:
                def make_slot_handler(slot_i):
                    return lambda e: fill_slot(e.control, slot_i)
                sentence_row.controls.append(
                    ft.ElevatedButton(text="[   ]", on_click=make_slot_handler(i))
                )
        page.update()

    def select_mark(m):
        nonlocal active_mark
        active_mark = m
        punc_feedback.value = f"已選擇標點：『 {active_mark} 』，請點擊底下的空格填入"
        page.update()

    def fill_slot(btn_control, idx):
        if active_mark:
            user_slots[idx] = active_mark
            btn_control.text = f"[ {active_mark} ]"
        else:
            punc_feedback.value = "請先在上方點擊選擇一個標點符號！"
        page.update()

    def check_punc_answer(e):
        expected = punc_data["questions"][punc_idx]["answers"]
        if user_slots == expected:
            punc_feedback.value = "全對了！標點符號用得很準確！"
        else:
            punc_feedback.value = f"填寫有誤。參考答案：{' '.join(expected)}"
        page.update()

    def next_punc_question(e):
        nonlocal punc_idx
        if punc_idx < len(punc_data["questions"]) - 1:
            punc_idx += 1
            load_punc_question()
        else:
            punc_feedback.value = "已經是最後一題！"
            page.update()

    punc_view = ft.Column([
        ft.Text("選擇標點符號：", size=16),
        palette_row,
        ft.Divider(),
        sentence_row,
        punc_feedback,
        ft.Row([
            ft.ElevatedButton("檢查標點", on_click=check_punc_answer),
            ft.ElevatedButton("下一題", on_click=next_punc_question)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=15)
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)

    # -------------------------------------------------------------
    # Navigation Tabs
    # -------------------------------------------------------------
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="選詞填空", content=fib_view),
            ft.Tab(text="標點符號", content=punc_view),
        ],
        expand=True
    )

    page.add(tabs)
    load_fib_question()
    load_punc_question()

# Start application
ft.app(target=main)
