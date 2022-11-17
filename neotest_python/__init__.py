import argparse
import json

from neotest_python.base import NeotestAdapter, NeotestResult


class TestRunner(object):
    PYTEST = "pytest"
    UNITTEST = "unittest"

    def __init__(self, runner):
        self.runner = runner

    def __eq__(self, compare):
        return self.runner == compare


def get_adapter(runner):
    if runner == TestRunner.PYTEST:
        from .pytest import PytestNeotestAdapter

        return PytestNeotestAdapter()
    elif runner == TestRunner.UNITTEST:
        from .myunittest import UnittestNeotestAdapter

        return UnittestNeotestAdapter()
    raise NotImplementedError(runner)


parser = argparse.ArgumentParser()
parser.add_argument("--runner", required=True)
parser.add_argument(
    "--results-file",
    dest="results_file",
    required=True,
    help="File to store result JSON in",
)
parser.add_argument(
    "--stream-file",
    dest="stream_file",
    required=True,
    help="File to stream result JSON to",
)
parser.add_argument("args", nargs="*")


def main(argv):
    args = parser.parse_args(argv)
    adapter = get_adapter(TestRunner(args.runner))

    with open(args.stream_file, "w") as stream_file:

        def stream(pos_id, result):
            stream_file.write(json.dumps({"id": pos_id, "result": result}) + "\n")
            stream_file.flush()

        results = adapter.run(args.args, stream)

    with open(args.results_file, "w") as results_file:
        json.dump(results, results_file)
