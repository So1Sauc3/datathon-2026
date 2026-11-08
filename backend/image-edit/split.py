"""Split cards.png (4x13 sprite sheet) into individual PNGs with white backgrounds."""

from pathlib import Path

from PIL import Image

ROWS = 4
COLS = 13
SHEET = Path(__file__).with_name("cards.png")
OUT_DIR = Path(__file__).with_name("cards")

SUITS = ["hearts", "clubs", "diamonds", "spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]


def main() -> None:
    sheet = Image.open(SHEET).convert("RGBA")
    cell_w = sheet.width // COLS
    cell_h = sheet.height // ROWS
    OUT_DIR.mkdir(exist_ok=True)

    for row, suit in enumerate(SUITS):
        for col, rank in enumerate(RANKS):
            left = col * cell_w
            top = row * cell_h
            card = sheet.crop((left, top, left + cell_w, top + cell_h))

            white = Image.new("RGBA", card.size, (255, 255, 255, 255))
            white.alpha_composite(card)

            out = OUT_DIR / f"{suit}_{rank}.png"
            white.convert("RGB").save(out)
            print(f"wrote {out.name}")


if __name__ == "__main__":
    main()
