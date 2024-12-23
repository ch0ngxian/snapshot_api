from ninja import Schema
from datetime import datetime

class CreateGameSchema(Schema):
    starts_at: datetime