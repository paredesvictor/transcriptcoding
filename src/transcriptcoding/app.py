"""
Code trancripts from directed interviews in a CSV format
"""
import os
import csv
import toga
from toga.style.pack import COLUMN, LEFT, ROW, Pack
from random import shuffle


class Coder(toga.App):
    def startup(self):
        # Create elements
        q_box = toga.Box()
        a_box = toga.Box()
        c_box = toga.Box()
        s_box = toga.Box()
        box = toga.Box()

        self.q_input = toga.MultilineTextInput(readonly=True)
        self.a_input = toga.MultilineTextInput(readonly=True)
        self.c_input = toga.MultilineTextInput(readonly=False)
        q_label = toga.Label("Question", style=Pack(text_align=LEFT))
        a_label = toga.Label("Answer", style=Pack(text_align=LEFT))
        c_label = toga.Label("Code", style=Pack(text_align=LEFT))

        button_next = toga.Button("Next Answer (cmd + enter)", on_press=self.write_code)
        button_save = toga.Button("Save (cmd + s)", on_press=self.save)
        button_quit = toga.Button("Quit", on_press=self.quit)

        cmd_next = toga.Command(
            self.write_code,
            text="Next Question",
            shortcut=toga.Key.MOD_1 + "<enter>",
        )

        cmd_save = toga.Command(
            self.save, text="Save CSV", shortcut=toga.Key.MOD_1 + "s"
        )

        self.count_label = toga.Label("", style=Pack(text_align=LEFT))

        q_box.add(q_label)
        q_box.add(self.q_input)
        a_box.add(a_label)
        a_box.add(self.a_input)
        c_box.add(c_label)
        c_box.add(self.c_input)
        s_box.add(button_save)
        s_box.add(button_quit)

        box.add(q_box)
        box.add(a_box)
        box.add(c_box)
        box.add(self.count_label)
        box.add(button_next)
        box.add(s_box)

        self.commands.add(cmd_next, cmd_save)

        # Set style
        box.style.update(direction=COLUMN, padding=10)

        q_box.style.update(direction=ROW, padding=5, flex=1)
        a_box.style.update(direction=ROW, padding=5, flex=3)
        c_box.style.update(direction=ROW, padding=5, flex=1)
        s_box.style.update(direction=ROW, padding=5, flex=0.5)

        self.q_input.style.update(flex=1)
        self.a_input.style.update(flex=1)
        self.c_input.style.update(flex=1)

        q_label.style.update(width=100, padding_left=10)
        a_label.style.update(width=100, padding_left=10)
        c_label.style.update(width=100, padding_left=10)

        button_next.style.update(padding=15)
        button_save.style.update(padding=15)
        button_quit.style.update(padding=15)

        # Create and show window
        self.main_window = toga.MainWindow(size=(640, 700))
        self.main_window.content = box
        self.main_window.show()

        # Initialize empty generator
        self.gen = None
        self.gen_is_empty = True
        self.code = None
        self.questions = None
        self.part_ID = None
        self.current_part = None
        self.current_q_idx = None

        # Open file selection dialog
        self.main_window.open_file_dialog(
            "Selectionner le fichier csv",
            file_types=["csv"],
            on_result=self.set_data,
        )

    def set_data(self, *handler):
        path_to_file = handler[1]
        if not path_to_file:
            self.quit()
        parent = path_to_file.parent
        stem = path_to_file.stem
        with open(path_to_file, "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            self.questions = reader.__next__()[1:]
            self.part_ID = []
            self.answers = {}
            self.code = {}
            for i, row in enumerate(reader):
                self.part_ID.append(row[0])
                self.answers[row[0]] = row[1:]
                self.code[row[0]] = ["" for e in row[1:]]

        self.code_file_name = os.path.join(parent, f"{stem}_codes.csv")
        if os.path.exists(self.code_file_name):
            with open(self.code_file_name, "r") as csvfile:
                reader = csv.reader(csvfile)
                for i, row in enumerate(reader):
                    if i != 0:
                        self.code[self.part_ID[i - 1]] = row[1:]

        # Create a list of unique answers ID for each answer that have not been coded
        nb_questions = len(self.questions)
        answer_ID = []
        for i, p in enumerate(self.code.keys()):
            for j, code in enumerate(self.code[p]):
                if code == "":
                    answer_ID.append(i * nb_questions + j)
        self.n_codes = len(answer_ID)
        # Shuffle the list
        shuffle(answer_ID)

        # Define a generator that iterate over each non coded answer
        def question_gen():
            for i, id in enumerate(answer_ID):
                question_idx = id % nb_questions
                participant = self.part_ID[id // nb_questions]
                question = self.questions[question_idx]
                answer = self.answers[participant][question_idx]
                yield (participant, question_idx, question, answer, i)

        # Create a generator and start it
        self.gen = question_gen()
        self.gen_is_empty = False
        self.next_question()

    def write_code(self, *args):
        if not self.gen_is_empty:
            self.code[self.current_part][self.current_q_idx] = self.c_input.value
        self.next_question()

    def next_question(self, *args):
        if not self.gen_is_empty:
            try:
                self.current_part, self.current_q_idx, question, answer, count = next(
                    self.gen
                )
            except StopIteration:
                self.gen_is_empty = True
                self.q_input.value = "--- END OF QUESTIONS, PLEASE SAVE AND QUIT ---"
                self.a_input.value = "--- END OF QUESTIONS, PLEASE SAVE AND QUIT ---"
                self.c_input.value = "--- END OF QUESTIONS, PLEASE SAVE AND QUIT ---"
                self.count_label.text = f"{self.n_codes} / {self.n_codes}"
                return
            self.q_input.value = question
            self.a_input.value = answer
            self.c_input.value = ""
            self.count_label.text = f"{count} / {self.n_codes}"

    def save(self, *args):
        with open(self.code_file_name, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([""] + self.questions)
            for id in self.part_ID:
                writer.writerow([id] + self.code[id])

    def quit(self, *args):
        self.exit()


def main():
    return Coder("Coder", "coder.test", icon=None)
