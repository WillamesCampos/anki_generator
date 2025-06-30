from genanki import Model, Note, Deck, Package
from gtts import gTTS
import uuid
import os
from datetime import datetime

# Criação do modelo de cartão
model_id = int(str(uuid.uuid4().int)[:9])
model = Model(
    model_id,
    'Backend Interview English Model with Audio',
    fields=[
        {'name': 'Term'},
        {'name': 'Translation'},
        {'name': 'Example'},
        {'name': 'ExampleTranslation'},
        {'name': 'Notes'},
        {'name': 'Audio'},
    ],
    templates=[{
        'name': 'Card 1',
        'qfmt': '{{Term}}<br>{{Audio}}',
        'afmt': '''
            <b>Tradução:</b> {{Translation}}<br><br>
            <b>Frase:</b> {{Example}}<br>
            <b>Tradução da frase:</b> {{ExampleTranslation}}<br><br>
            <b>Observações:</b> {{Notes}}
        '''
    }]
)

# Criação do baralho
deck = Deck(
    2059400220,
    'Vocabulário Técnico - Backend & Entrevistas (com Áudio)'
)

# Novos termos
cards = [
    ('collaborate', 'colaborar', 'I collaborated with the frontend team to fix the bug.', 'Colaborei com o time de frontend para corrigir o bug.', 'Muito usado em entrevistas'),
    ('meet the deadline', 'cumprir o prazo', 'We worked overtime to meet the deadline.', 'Trabalhamos horas extras para cumprir o prazo.', 'Expressão típica de trabalho'),
    ('ownership', 'senso de responsabilidade', 'I took ownership of the migration project.', 'Tomei responsabilidade pelo projeto de migração.', 'Comum em entrevistas'),
    ('scalable', 'escalável', 'We designed a scalable architecture.', 'Projetamos uma arquitetura escalável.', 'Jargão técnico'),
    ('bottleneck', 'gargalo', 'The database was a performance bottleneck.', 'O banco de dados era um gargalo de performance.', 'Engenharia de software'),
    ('refactor', 'refatorar', 'I refactored the code to improve readability.', 'Refatorei o código para melhorar a legibilidade.', 'Muito comum em entrevistas'),
    ('trade-off', 'compromisso / escolha entre opções', 'There was a trade-off between speed and quality.', 'Houve um compromisso entre velocidade e qualidade.', 'Soft skills e arquitetura'),
    ('align', 'alinhar', 'We aligned our goals during the sprint planning.', 'Alinhamos nossos objetivos durante o planejamento da sprint.', 'Usado com frequência em times ágeis'),
    ('assertive', 'assertivo', 'I try to be assertive when giving feedback.', 'Tento ser assertivo ao dar feedback.', 'Comportamento profissional'),
    ('estimate', 'estimar', 'I estimated 3 days to complete the task.', 'Estimei 3 dias para concluir a tarefa.', 'Gestão de tempo e prazos'),
]

# Palavras anteriores (adicione à variável cards)
cards += [
    ('handle', 'lidar com', 'I handled the API errors manually.', 'Eu lidei com os erros da API manualmente.', 'Usado com erros, requisições, tarefas'),
    ('implement', 'implementar', 'I implemented a login feature using Django.', 'Eu implementei uma funcionalidade de login usando Django.', 'Comum para funcionalidades'),
    ('debug', 'depurar', 'I had to debug a strange issue in production.', 'Tive que depurar um problema estranho em produção.', 'Muito usado com bugs'),
    ('scale', 'escalar', 'We scaled our services to handle more users.', 'Escalamos nossos serviços para atender mais usuários.', 'Escalabilidade de sistema'),
    ('deploy', 'fazer deploy', 'We deployed the new version last night.', 'Fizemos deploy da nova versão ontem à noite.', 'Junto de ferramentas CI/CD'),
    ('middleware', 'intermediário', 'We added an auth middleware to validate tokens.', 'Adicionamos um middleware de autenticação para validar tokens.', 'Entre requisição e resposta'),
    ('endpoint', 'rota da API', 'The `/login` endpoint handles user auth.', 'A rota `/login` cuida da autenticação do usuário.', 'URLs da API'),
    ('environment variable', 'variável de ambiente', 'We use environment variables to store secrets.', 'Usamos variáveis de ambiente para guardar segredos.', 'Arquivos `.env`'),
    ('queue', 'fila', 'Jobs are processed in the background using a queue.', 'Tarefas são processadas em segundo plano usando uma fila.', 'Ex: RabbitMQ, Celery'),
    ('asynchronous', 'assíncrono', 'We use asynchronous calls to improve performance.', 'Usamos chamadas assíncronas para melhorar a performance.', 'Relacionado a tarefas paralelas'),
]


# Diretório para salvar os áudios
audio_dir = 'anki_audio'
os.makedirs(audio_dir, exist_ok=True)
media_files = []

# Adiciona os cards com áudio
for term, translation, example, example_translation, notes in cards:
    audio_filename = f'{term.replace(" ", "_")}.mp3'
    audio_path = os.path.join(audio_dir, audio_filename)

    tts = gTTS(term, lang='en', tld='com')  # inglês americano
    tts.save(audio_path)
    media_files.append(audio_path)

    audio_tag = f'[sound:{audio_filename}]'

    note = Note(
        model=model,
        fields=[term, translation, example, example_translation, notes, audio_tag]
    )
    deck.add_note(note)

# Exporta o deck
output_path = f'vocab_backend_interview_audio_{datetime.now().strftime("%d-%m-%Y")}.apkg'
Package(deck, media_files).write_to_file(output_path)
print("✅ Deck gerado com sucesso!")
