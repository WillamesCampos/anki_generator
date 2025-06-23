from genanki import Note


class NoteGenerator:
    def __init__(self, deck, model) -> None:
        self.deck = deck
        self.model = model

    def generate_note(self):
        note = Note(
            model=self.model,
            fields=[]
        )

        return note