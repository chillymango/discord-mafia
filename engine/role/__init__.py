import importlib
import pkgutil
import typing as T

from engine.role.base import Role


def import_submodules(package, recursive=True):
    """ Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :type package: str | module
    :rtype: dict[str, types.ModuleType]
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results.update(import_submodules(full_name))
    return results

def test():
    from engine.role import mafia
    from engine.role import town
    from engine.role import neutral
    import_submodules(mafia)
    import_submodules(town)
    import_submodules(neutral)


def get_all_roles() -> T.List[T.Type[Role]]:
    test()
    roles: T.List[T.Type[Role]] = list()
    to_visit = [Role]
    while to_visit:
        node = to_visit.pop()
        subclasses = node.__subclasses__()
        if subclasses:
            to_visit.extend(subclasses)
        else:
            # only add leaf nodes
            # there's no true inheritance in this dojo
            # sorry mafia / triad
            roles.append(node)
    return roles


ALL_ROLES = get_all_roles()
NAME_TO_ROLE = {klass.__name__: klass for klass in ALL_ROLES}


def has_killing_action(role_cls: T.Type[Role]) -> bool:
    from engine.action.kill import Kill
    for action in role_cls.night_actions():
        if issubclass(action, Kill):
            return True
    return False


KILLING_ROLES = [klass for klass in ALL_ROLES if has_killing_action(klass)]
