"""
Kill-Report
"""
import typing as T

if T.TYPE_CHECKING:
    from engine.actor import Actor


class KillReport:

    def __init__(self):
        self._public: T.List[T.Tuple["Actor", str]] = []  # public ledger of kills and descriptions
        self._private: T.List[T.Tuple["Actor", str]] = []  # private is added to public when transition is called

    def transition(self) -> None:
        consolidate = dict()
        for actor, reportstr in self._private:
            if actor.is_alive:
                # this report is no longer valid
                continue
            if actor in consolidate:
                consolidate[actor] += ". Attacked multiple times."
            else:
                consolidate[actor] = reportstr
        for actor, new_report in consolidate.items():
            self._public.append((actor, new_report))
        self._private = []

    def stage_report(self, actor: "Actor", report: str) -> None:
        self._private.append((actor, report))

    def lynch(self, actor: "Actor") -> None:
        """
        Append directly to kill report
        """
        self._public.append((actor, "Lynched."))

    def constable(self, actor: "Actor") -> None:
        self._public.append((actor, "Shot by the Constable."))

    def double_flower(self, actor: "Actor") -> None:
        self._public.append((actor, "Assassinated"))

    def afk(self, actor: "Actor") -> None:
        self._public.append((actor, "Died of a heart attack"))
