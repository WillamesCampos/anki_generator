from genanki import Model
import uuid


class CardModel:

    def __init__(cls, title) -> None:
        cls.model = None
        cls.fields = None
        cls.template = None
        cls.title = title

    @classmethod
    def __gen_id() -> uuid:
        return uuid.uuid4()

    @classmethod
    def __create_template(cls) -> list:
        cls.template = [{
            'name': 'Card 1',
            'qfmt': '{{Term}}<br>{{Audio}}',
            'afmt': '''
                <b>Tradução:</b> {{Translation}}<br><br>
                <b>Frase:</b> {{Example}}<br>
                <b>Tradução da frase:</b> {{ExampleTranslation}}<br><br>
                <b>Observações:</b> {{Notes}}
            '''
        }]

    @classmethod
    def __create_fields(cls) -> list:
        cls.fields = [
            {'name': 'Term'},
            {'name': 'Translation'},
            {'name': 'Example'},
            {'name': 'ExampleTranslation'},
            {'name': 'Notes'},
            {'name': 'Audio'},
        ]

    @classmethod
    def create_model(cls):
        cls.__create_fields()
        cls.__create_template()

        cls.model = Model(
            model_id=cls.__gen_id(),
            name=cls.title,
            templates=cls.template,
            fields=cls.fields
        )
