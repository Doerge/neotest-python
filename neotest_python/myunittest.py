import inspect
import os
import sys
import traceback
import unittest
from pathlib import Path
from types import TracebackType

from .base import NeotestAdapter, NeotestResultStatus


class UnittestNeotestAdapter(NeotestAdapter):
    def case_file(self, case):
        return str(Path(inspect.getmodule(case).__file__).absolute())  # type: ignore

    def case_id_elems(self, case):
        file = self.case_file(case)
        elems = [file, case.__class__.__name__]
        if isinstance(case, unittest.TestCase):
            elems.append(case._testMethodName)
        return elems

    def case_id(self, case):
        return "::".join(self.case_id_elems(case))

    def id_to_unittest_args(self, case_id):
        """Converts a neotest ID into test specifier for unittest"""
        #path, *child_ids = case_id.split("::")
        tmp = case_id.split("::")
        path = tmp[0]
        child_ids = tmp[1:]
        if not child_ids:
            if os.path.isfile(path):
                # Test files can be passed directly to unittest
                return [path]
            # Directories need to be run via the 'discover' argument
            return ["discover", "-s", path]

        # Otherwise, convert the ID into a dotted path, relative to current dir
        relative_file = os.path.relpath(path, os.getcwd())
        relative_stem = os.path.splitext(relative_file)[0]
        relative_dotted = relative_stem.replace(os.sep, ".")
        #return [".".join([relative_dotted, *child_ids])]
        child_ids.insert(0, relative_dotted)
        return [".".join(child_ids)]

    # TODO: Stream results
    def run(self, args, _):
        results = {}

        errs = {}

        class NeotestTextTestResult(unittest.TextTestResult):
            def addFailure(_, test, err):
                errs[self.case_id(test)] = err
                return super().addFailure(test, err)

            def addError(_, test, err):
                errs[self.case_id(test)] = err
                return super().addError(test, err)

            def addSuccess(_, test):
                results[self.case_id(test)] = {
                    "status": NeotestResultStatus.PASSED,
                }

        class NeotestUnittestRunner(unittest.TextTestRunner):
            def run(self, test):
                result = unittest.TextTestRunner(resultclass=NeotestTextTestResult).run(test)
                for case, message in result.failures + result.errors:
                    case_id = self.case_id(case)
                    error_line = None
                    case_file = self.case_file(case)
                    if case_id in errs:
                        trace = errs[case_id][2]
                        summary = traceback.extract_tb(trace)
                        error_line = next(
                            frame.lineno - 1
                            for frame in reversed(summary)
                            if frame.filename == case_file
                        )
                    results[case_id] = {
                        "status": NeotestResultStatus.FAILED,
                        "errors": [{"message": message, "line": error_line}],
                        "short": None,
                    }
                for case, message in result.skipped:
                    results[self.case_id(case)] = {
                        "short": None,
                        "status": NeotestResultStatus.SKIPPED,
                        "errors": None,
                    }
                return result

        # Make sure we can import relative to current path
        sys.path.insert(0, os.getcwd())

        # We only get a single case ID as the argument
        argv = sys.argv[0:1] + self.id_to_unittest_args(args[-1])
        unittest.main(
            module=None,
            argv=argv,
            testRunner=NeotestUnittestRunner(resultclass=NeotestTextTestResult),
            exit=False,
        )

        return results
