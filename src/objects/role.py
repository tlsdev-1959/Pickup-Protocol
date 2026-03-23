from dataclasses import dataclass

@dataclass
class Role:
    id: int
    name: str
    
    def isAppAccess(self):
        return self.id == 74122