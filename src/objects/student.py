from objects import user
from dataclasses import dataclass


@dataclass
class Student:
    id: int
    carline: int
    first: str
    last: str
    grade: str
    crew: str
    picutre_url: str
    pickups: dict
    visitors: dict
    schedule: dict
    at_now: dict

    def printName(self):
        return f'{self.first} {self.last}'