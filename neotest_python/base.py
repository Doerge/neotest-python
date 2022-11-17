import abc


class NeotestResultStatus(object):
    #SKIPPED = 1
    #PASSED = 2
    #FAILED = 3
    SKIPPED = "skipped"
    PASSED = "passed"
    FAILED = "failed"


    def max(a, b):
        if a == NeotestResultStatus.FAILED or b == NeotestResultStatus.FAILED:
            return NeotestResultStatus.FAILED

        if a == NeotestResultStatus.PASSED or b == NeotestResultStatus.PASSED:
            return NeotestResultStatus.PASSED

        if a == NeotestResultStatus.SKIPPED or b == NeotestResultStatus.SKIPPED:
            return NeotestResultStatus.SKIPPED

        raise Exception("ERROR: Unexpected NeotestResultStatus.")

NeotestError = dict()
NeotestResult = dict()


class NeotestAdapter:
    __metaclass__ = abc.ABCMeta
    def update_result(self, base, update):
        if not base:
            return update
        return {
            "status": NeotestResultStatus.max(base["status"], update["status"]),
            "errors": (base.get("errors") or []) + (update.get("errors") or []) or None,
            "short": (base.get("short") or "") + (update.get("short") or ""),
        }

    @abc.abstractmethod
    def run(self, args, stream):
        del args, stream
        raise NotImplementedError
