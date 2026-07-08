class ScopesNotGrantedError(Exception):
    def __init__(self, ungranted: set[str]) -> None:
        super().__init__(f"Scopes not granted by the organization: {', '.join(sorted(ungranted))}")


class ScopesInUseError(Exception):
    def __init__(self, in_use: set[str]) -> None:
        super().__init__(f"Scopes still in use by one or more clients: {', '.join(sorted(in_use))}")


class OrganizationHasClientsError(Exception):
    def __init__(self) -> None:
        super().__init__("Organization still has one or more active clients")
