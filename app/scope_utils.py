import inject


def parse(value: str | None) -> set[str]:
    if not value:
        return set()
    split = value.split()
    return set(split.strip() for split in split)


def is_subset(child: str | None, parent: str | None) -> bool:
    return parse(child).issubset(parse(parent))


@inject.params(allowed_scopes="allowed_scopes")
def check_in_configured_scopes(allowed_scopes: set[str], requested: str | None) -> bool:
    if not requested:
        return True
    return parse(requested).issubset(allowed_scopes)
