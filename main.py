import json
import re
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.text import LabelBase

class FillInBlankScreen(Screen):
    def __init__(self, questions, **kwargs):
        super().__init__(**kwargs)
        self.questions = questions
        self.current_idx = 0
        self.selected_choice = ""
        
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Header navigation
        top_bar = BoxLayout(size_hint_y=0.1)
        btn_switch = Button(text="切換至：標點符號練習", font_name="Roboto")
        btn_switch.bind(on_release=lambda x: setattr(self.manager, 'current', 'punctuation'))
        top_bar.add_widget(btn_switch)
        self.layout.add_widget(top_bar)
        
        # Question display
        self.question_label = Label(
            text="", 
            font_size='24sp', 
            size_hint_y=0.3,
            halign='center',
            valign='middle'
        )
        self.question_label.bind(size=self.question_label.setter('text_size'))
        self.layout.add_widget(self.question_label)
        
        # Options container
        self.options_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.2)
        self.layout.add_widget(self.options_box)
        
        # Feedback label
        self.feedback_label = Label(text="", font_size='20sp', size_hint_y=0.15)
        self.layout.add_widget(self.feedback_label)
        
        # Action controls
        ctrl_box = BoxLayout(spacing=10, size_hint_y=0.15)
        self.btn_check = Button(text="檢查答案")
        self.btn_check.bind(on_release=self.check_answer)
        self.btn_next = Button(text="下一題")
        self.btn_next.bind(on_release=self.next_question)
        ctrl_box.add_widget(self.btn_check)
        ctrl_box.add_widget(self.btn_next)
        self.layout.add_widget(ctrl_box)
        
        self.add_widget(self.layout)
        self.load_question()

    def parse_question(self, raw_text):
        # Parses bracket choices like (地／得／的) or （地/得/的）
        pattern = r'[（\(](.*?)[）\)]'
        match = re.search(pattern, raw_text)
        if match:
            options_str = match.group(1)
            options = re.split(r'[／/]', options_str)
            prefix = raw_text[:match.start()]
            suffix = raw_text[match.end():]
            return prefix, options, suffix
        return raw_text, [], ""

    def load_question(self):
        self.options_box.clear_widgets()
        self.selected_choice = ""
        self.feedback_label.text = ""
        
        if self.current_idx >= len(self.questions):
            self.question_label.text = "測驗完成！"
            return

        q_data = self.questions[self.current_idx]
        self.prefix, self.options, self.suffix = self.parse_question(q_data["text"])
        self.update_sentence_display(" [ ___ ] ")

        for opt in self.options:
            btn = Button(text=opt, font_size='22sp')
            btn.bind(on_release=self.select_option)
            self.options_box.add_widget(btn)

    def select_option(self, instance):
        self.selected_choice = instance.text
        self.update_sentence_display(f" [ {self.selected_choice} ] ")

    def update_sentence_display(self, fill_text):
        self.question_label.text = f"{self.prefix}{fill_text}{self.suffix}"

    def check_answer(self, instance):
        if not self.selected_choice:
            self.feedback_label.text = "請先選擇一個答案！"
            return
            
        correct = self.questions[self.current_idx]["answer"]
        if self.selected_choice == correct:
            self.feedback_label.text = "答對了！非常棒！"
        else:
            self.feedback_label.text = f"再試一次！正確答案是：{correct}"

    def next_question(self, instance):
        if self.current_idx < len(self.questions) - 1:
            self.current_idx += 1
            self.load_question()
        else:
            self.feedback_label.text = "已經是最後一題了！"


class PunctuationScreen(Screen):
    def __init__(self, punctuation_data, **kwargs):
        super().__init__(**kwargs)
        self.marks = punctuation_data["available_marks"]
        self.questions = punctuation_data["questions"]
        self.current_idx = 0
        self.active_mark = None
        self.user_slots = []
        
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Navigation bar
        top_bar = BoxLayout(size_hint_y=0.1)
        btn_switch = Button(text="切換至：選詞填空練習")
        btn_switch.bind(on_release=lambda x: setattr(self.manager, 'current', 'fill_blank'))
        top_bar.add_widget(btn_switch)
        self.layout.add_widget(top_bar)

        # Available punctuation palette (Reusable across questions)
        palette_label = Label(text="選擇標點符號：", size_hint_y=0.08)
        self.layout.add_widget(palette_label)
        
        self.palette_box = GridLayout(cols=4, spacing=5, size_hint_y=0.2)
        for mark in self.marks:
            btn = Button(text=mark, font_size='22sp')
            btn.bind(on_release=self.select_mark)
            self.palette_box.add_widget(btn)
        self.layout.add_widget(self.palette_box)

        # Sentence & Slots area
        self.sentence_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.25)
        self.layout.add_widget(self.sentence_box)

        # Feedback area
        self.feedback_label = Label(text="", font_size='20sp', size_hint_y=0.15)
        self.layout.add_widget(self.feedback_label)

        # Action controls
        ctrl_box = BoxLayout(spacing=10, size_hint_y=0.15)
        btn_check = Button(text="檢查標點")
        btn_check.bind(on_release=self.check_answer)
        btn_next = Button(text="下一題")
        btn_next.bind(on_release=self.next_question)
        ctrl_box.add_widget(btn_check)
        ctrl_box.add_widget(btn_next)
        self.layout.add_widget(ctrl_box)

        self.add_widget(self.layout)
        self.load_question()

    def select_mark(self, instance):
        self.active_mark = instance.text
        self.feedback_label.text = f"已選擇標點：『 {self.active_mark} 』，請點擊底下的空格填入"

    def load_question(self):
        self.sentence_box.clear_widgets()
        self.feedback_label.text = ""
        self.active_mark = None
        
        if self.current_idx >= len(self.questions):
            self.feedback_label.text = "所有標點練習已完成！"
            return

        q_data = self.questions[self.current_idx]
        segments = re.split(r'[（\(][）\)]', q_data["text"])
        
        self.slot_buttons = []
        self.user_slots = [""] * (len(segments) - 1)

        for i, seg in enumerate(segments):
            if seg:
                lbl = Label(text=seg, font_size='20sp', size_hint_x=None)
                lbl.texture_update()
                lbl.width = lbl.texture_size[0] + 10
                self.sentence_box.add_widget(lbl)

            if i < len(segments) - 1:
                slot_btn = Button(text="[   ]", font_size='20sp', size_hint_x=None, width=70)
                slot_btn.slot_index = i
                slot_btn.bind(on_release=self.fill_slot)
                self.slot_buttons.append(slot_btn)
                self.sentence_box.add_widget(slot_btn)

    def fill_slot(self, instance):
        if self.active_mark:
            idx = instance.slot_index
            self.user_slots[idx] = self.active_mark
            instance.text = f"[ {self.active_mark} ]"
        else:
            self.feedback_label.text = "請先在上方點擊選擇一個標點符號！"

    def check_answer(self, instance):
        expected = self.questions[self.current_idx]["answers"]
        if self.user_slots == expected:
            self.feedback_label.text = "全對了！標點符號用得很準確！"
        else:
            self.feedback_label.text = f"填寫有誤。參考答案：{' '.join(expected)}"

    def next_question(self, instance):
        if self.current_idx < len(self.questions) - 1:
            self.current_idx += 1
            self.load_question()
        else:
            self.feedback_label.text = "已經是最後一題！"


class ChineseLearningApp(App):
    def build(self):
        with open("questions.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        sm = ScreenManager()
        sm.add_widget(FillInBlankScreen(data["fill_in_blank"], name='fill_blank'))
        sm.add_widget(PunctuationScreen(data["punctuation"], name='punctuation'))
        return sm


if __name__ == "__main__":
    ChineseLearningApp().run()
