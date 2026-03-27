ROLES = {
    "admin": ["create", "read", "update", "delete", "send", "export"],
    "accountant": ["read", "export"],
    "viewer": ["read"],
}


def has_permission(role: str, action: str) -> bool:
    return action in ROLES.get(role, [])


def require_permission(role: str, action: str) -> None:
    if not has_permission(role, action):
        raise PermissionError(f"Role '{role}' cannot perform '{action}'")
