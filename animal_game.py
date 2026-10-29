"""실행: uv run python animal_game.py"""
import tkinter as tk
from tkinter import messagebox, ttk, font
from game_rules import Game, TRAITS, load_animals
from card_images import CardImages

BG, INK, GREEN = '#f4f6ef', '#233d31', '#326c4c'


class AnimalGame:
    def __init__(self, root):
        self.root = root
        available = font.families(root)
        self.font = next((f for f in ('Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans CJK KR') if f in available), 'Arial')
        ttk.Style(root).configure('.', font=(self.font, 10))
        root.title('동물 특성 카드 게임')
        root.geometry('1050x870')
        root.minsize(760, 650)
        root.configure(bg=BG)
        root.option_add('*Font', (self.font, 11))
        self.images = CardImages()
        self.animals = load_animals()
        self.game = None
        self.selected = None
        self.buttons = {}
        tk.Label(root, text='동물 특성 카드 게임', font=(self.font, 24, 'bold'),
                 bg=BG, fg=INK).pack(pady=(18, 5))
        tk.Label(root, text='두 특성에 어울리는 동물을 골라 보세요 · 카드 15장 · 10턴',
                 bg=BG, fg=INK).pack()
        self.status = tk.Label(root, text='두 개 +3점 / 한 개 +1점 / 틀리면 -1점 / 패스 0점', bg=BG)
        self.status.pack(pady=10)
        self.trait_frame = tk.Frame(root, bg=BG)
        self.trait_frame.pack()
        toolbar = tk.Frame(root, bg=BG)
        toolbar.pack(pady=10)
        self.start = ttk.Button(toolbar, text='시작', command=self.new_game)
        self.start.pack(side='left', padx=5)
        self.submit = ttk.Button(toolbar, text='카드 내기', command=self.play, state='disabled')
        self.submit.pack(side='left', padx=5)
        self.skip = ttk.Button(toolbar, text='패스', command=lambda: self.play(True), state='disabled')
        self.skip.pack(side='left', padx=5)
        self.next = ttk.Button(toolbar, text='다음 턴', command=self.advance, state='disabled')
        self.next.pack(side='left', padx=5)
        ttk.Button(toolbar, text='규칙', command=self.rules).pack(side='left', padx=5)
        self.result = tk.Label(root, text='시작을 누르면 새로운 카드 15장을 받습니다.',
                               bg=BG, fg=GREEN, wraplength=900, height=4, justify='center')
        self.result.pack(fill='x', padx=15)
        area = tk.Frame(root, bg=BG)
        area.pack(fill='both', expand=True, padx=20, pady=(0, 15))
        self.canvas = tk.Canvas(area, bg=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(area, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.cards = tk.Frame(self.canvas, bg=BG)
        window = self.canvas.create_window((0, 0), window=self.cards, anchor='nw')
        self.cards.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(window, width=e.width))

    def rules(self):
        messagebox.showinfo('게임 규칙',
            '특성 2개 일치 +3 / 1개 일치 +1 / 불일치 -1 / 패스 0\n'
            '낸 카드는 사라지고 새 카드는 받지 않습니다. 패스는 언제나 가능합니다.\n'
            '10턴 후 점수를 합산합니다. 정답 특성은 제출 후 공개합니다.\n\n'
            '대표 성체를 기준으로 단순화한 학습용 분류입니다.\n'
            '날개는 비행 능력과 다르고, 채식은 주식이 식물인 경우입니다.\n'
            '성별·계절·지역에 따른 차이는 제출 후 카드 설명을 참고하세요.', parent=self.root)

    def new_game(self):
        self.game = Game(self.animals)
        self.start.configure(text='다시 하기', state='disabled')
        self.result.configure(text='카드를 고르고 카드 내기를 누르세요. 정답은 제출 후 공개됩니다.')
        self.render()

    def render(self):
        game = self.game
        self.selected = None
        self.submit.configure(state='disabled')
        self.skip.configure(state='disabled' if game.waiting else 'normal')
        self.next.configure(state='normal' if game.waiting else 'disabled')
        turn = min(10, len(game.history) + (not game.waiting))
        self.status.configure(text=f'{turn} / 10턴     |     {game.score}점     |     남은 카드 {len(game.hand)}장')
        for child in self.trait_frame.winfo_children():
            child.destroy()
        for trait in game.traits:
            index = list(TRAITS).index(trait)
            photo = self.images.get('assets/traits.png', index, (60, 60), 5, 2)
            tk.Label(self.trait_frame, text=TRAITS[trait], image=photo, compound='left',
                     bg='white', fg=INK, padx=15, pady=5).pack(side='left', padx=10)
        for child in self.cards.winfo_children():
            child.destroy()
        self.buttons.clear()
        for index, card in enumerate(game.hand):
            self.cards.columnconfigure(index % 5, weight=1)
            photo = self.images.get(card['image'], card['cell'], box=card.get('crop'))
            button = tk.Button(self.cards, text=f"{card['name_ko']}\n{card['name_en']}",
                image=photo, compound='top', bg='white', fg=INK, relief='flat', borderwidth=2,
                wraplength=160, font=(self.font, 10), padx=3, pady=6,
                state='disabled' if game.waiting else 'normal',
                command=lambda cid=card['id']: self.select(cid))
            button.grid(row=index // 5, column=index % 5, sticky='nsew', padx=4, pady=4)
            self.buttons[card['id']] = button
        if self.images.missing:
            self.result.configure(text='일부 그림이 없습니다. 이름으로 진행할 수 있습니다. assets 폴더를 확인하세요.')

    def select(self, card_id):
        if self.game.waiting:
            return
        self.selected = card_id
        for cid, button in self.buttons.items():
            button.configure(bg='#d7ebcc' if cid == card_id else 'white',
                             relief='solid' if cid == card_id else 'flat')
        self.submit.configure(state='normal')

    def play(self, skip=False):
        if not self.game or self.game.waiting or (not skip and self.selected is None):
            return
        record = self.game.play(None if skip else self.selected)
        card = record['card']
        if card:
            detail = ' / '.join(f'{TRAITS[t]}: {"해당" if ok else "아님"}'
                               for t, ok in zip(record['traits'], record['matches']))
            text = f"{card['name_ko']}  {record['points']:+d}점 · {detail}\n{card['note']}"
        else:
            text = '패스 · 0점. 카드는 그대로 유지됩니다.'
        self.render()
        self.result.configure(text=text)
        self.next.configure(text='최종 결과' if len(self.game.history) == 10 else '다음 턴')

    def advance(self):
        if not self.game or not self.game.waiting:
            return
        if self.game.next_turn():
            self.render()
            self.result.configure(text='새로운 특성입니다. 카드를 선택하거나 패스하세요.')
            self.canvas.yview_moveto(0)
            return
        self.next.configure(state='disabled')
        self.start.configure(state='normal')
        lines = [f"{i}. {r['card']['name_ko'] if r['card'] else '패스'} · "
                 f"{' + '.join(TRAITS[t] for t in r['traits'])} → {r['points']:+d}점"
                 for i, r in enumerate(self.game.history, 1)]
        self.result.configure(text=f'10턴 완료! 최종 {self.game.score}점 · 다시 하기로 새 게임을 시작하세요.')
        messagebox.showinfo(f'최종 {self.game.score}점', '\n'.join(lines), parent=self.root)


if __name__ == '__main__':
    root = tk.Tk()
    try:
        AnimalGame(root)
    except (ValueError, OSError, KeyError) as error:
        messagebox.showerror('카드 자료 확인', str(error), parent=root)
        root.destroy()
    else:
        root.mainloop()
