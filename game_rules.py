"""그림과 창 없이도 확인할 수 있는 카드 데이터와 게임 규칙."""
import json
import random
from pathlib import Path

BASE = Path(__file__).resolve().parent
TRAITS = dict(zip(
    ('herbivore', 'hibernate', 'shell', 'wings', 'aquatic',
     'scales', 'horns', 'nocturnal', 'fur', 'eggs'),
    ('채식', '겨울잠', '단단한 껍질', '날개', '물속 생활',
     '비늘', '뿔', '야행성', '털', '알을 낳음')))


def load_animals(path=BASE / 'animals.json'):
    animals = json.loads(Path(path).read_text(encoding='utf-8'))
    if len(animals) < 100:
        raise ValueError('서로 다른 동물 카드가 100종 이상 필요합니다.')
    seen = set()
    for card in animals:
        name = card.get('name_ko', '이름 없는 카드')
        if not all(card.get(key) for key in ('id', 'name_ko', 'name_en', 'image')):
            raise ValueError(f'{name}: ID·이름·그림 경로를 확인하세요.')
        if card['id'] in seen:
            raise ValueError(f'{name}: 중복된 ID입니다.')
        seen.add(card['id'])
        values = card.get('traits', {})
        if set(values) != set(TRAITS) or any(type(v) is not bool for v in values.values()):
            raise ValueError(f'{name}: 특성 10개는 모두 참/거짓이어야 합니다.')
    return animals


class Game:
    def __init__(self, animals, rng=None):
        self.rng = rng or random.Random()
        self.hand = self.rng.sample(animals, 15)
        self.history = []
        self.score = 0
        self.traits = self.rng.sample(list(TRAITS), 2)
        self.waiting = False

    def play(self, card_id=None):
        if self.waiting or len(self.history) >= 10:
            raise ValueError('이번 턴은 이미 끝났습니다.')
        card = None
        if card_id is not None:
            card = next((c for c in self.hand if c['id'] == card_id), None)
            if card is None:
                raise ValueError('손에 있는 카드를 선택하세요.')
        matches = [bool(card and card['traits'][t]) for t in self.traits]
        points = (-1, 1, 3)[sum(matches)] if card else 0
        record = dict(card=card, traits=self.traits[:], matches=matches, points=points)
        self.history.append(record)
        self.score += points
        if card:
            self.hand.remove(card)
        self.waiting = True
        return record

    def next_turn(self):
        if not self.waiting or len(self.history) >= 10:
            return False
        self.traits = self.rng.sample(list(TRAITS), 2)
        self.waiting = False
        return True
