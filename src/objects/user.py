from dataclasses import dataclass
from objects import role

## Helper Functions
# Input: List of JSON objects containing an object for each role the user has
# Output: A boolean value is returned; if the user has access based on the roles input,
#         True will be returned; otherwise False
# Implementation: This function is implemented by utilizing the builtin filter() function
#                 on the list of roles in the input to reduce the list to contain only those roles
#                 with the matching role_id required. Once this list is shortedn, the cardinality
#                 of the list is then measured to determine if the roles that grant access are in the
#                 user input roles.
# Time Complexity: O(n) | n is the number of roles the user has assigned
# Space Complexity: O(1)
def checkAccess(roles: list [role.Role]) -> bool:
    n: int = len(list(filter(lambda r: r.isAppAccess(), roles)))
    print(n)
    return n > 0
# END checkAccess


@dataclass
class User:
    id: int
    preferred: str
    first: str
    last: str
    isFaculty: bool
    hasAccess: bool
    roles: list [role.Role]


    ## Overloaded version of initialization with a JSON response of a GET User request
    def __init__(self, response: dict) -> None:
        self.id = response['id']
        try:
            self.preferred = response['preferred_name']
        except KeyError:
            self.preferred = response['first_name']
        self.first = response['first_name']
        self.last = response['last_name']
        self.isFaculty = response['is_faculty']
        self.roles = [role.Role(r['id'], r['name']) for r in response['roles']]
        self.hasAccess = checkAccess(self.roles)
