"""Pillow로 그림 묶음의 한 칸을 카드 크기로 읽습니다."""
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageTk
from game_rules import BASE


def isolate_sprite(picture):
    """그림 묶음 가장자리의 옆 동물 조각을 화면에서 제외합니다."""
    small = ImageOps.contain(picture, (150, 150))
    mask = Image.new('L', small.size)
    mask.putdata([255 if min(pixel) < 220 else 0 for pixel in small.getdata()])
    mask = mask.filter(ImageFilter.MaxFilter(5))
    width, height = mask.size
    remaining = {i for i, value in enumerate(mask.getdata()) if value}
    largest = set()
    while remaining:
        seed = remaining.pop()
        component, todo = {seed}, [seed]
        while todo:
            index = todo.pop()
            x, y = index % width, index // width
            for nx, ny in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                neighbor = ny * width + nx
                if 0 <= nx < width and 0 <= ny < height and neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    todo.append(neighbor)
        if len(component) > len(largest):
            largest = component
    if not largest:
        return picture
    mask.putdata([255 if i in largest else 0 for i in range(width * height)])
    mask = mask.resize(picture.size, Image.Resampling.NEAREST)
    clean = Image.new('RGB', picture.size, 'white')
    clean.paste(picture, mask=mask)
    return clean


class CardImages:
    def __init__(self):
        self.sheets = {}
        self.photos = {}
        self.missing = set()

    def get(self, path, cell, size=(130, 110), columns=5, rows=5, box=None):
        key = (path, cell, size, tuple(box) if box else None)
        if key in self.photos:
            return self.photos[key]
        try:
            if path not in self.sheets:
                with Image.open(BASE / path) as source:
                    rgba = source.convert('RGBA')
                    white = Image.new('RGBA', rgba.size, 'white')
                    self.sheets[path] = Image.alpha_composite(white, rgba).convert('RGB')
            sheet = self.sheets[path]
            x, y = cell % columns, cell // columns
            bounds = (round(x * sheet.width / columns), round(y * sheet.height / rows),
                      round((x + 1) * sheet.width / columns), round((y + 1) * sheet.height / rows))
            if box:
                bounds = tuple(round(v * (sheet.width if i % 2 == 0 else sheet.height) / 1254)
                               for i, v in enumerate(box))
            picture = sheet.crop(bounds)
            if box:
                picture = isolate_sprite(picture)
            picture = ImageOps.contain(picture, size, Image.Resampling.LANCZOS)
        except (OSError, ValueError):
            self.missing.add(path)
            picture = Image.new('RGB', size, '#eef2e8')
            draw = ImageDraw.Draw(picture)
            draw.ellipse((35, 20, 95, 80), fill='#cedfc3')
            draw.text((60, 40), '?', fill='#274335')
        photo = ImageTk.PhotoImage(picture)
        self.photos[key] = photo
        return photo
