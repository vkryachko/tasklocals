import unittest
import gc
import asyncio
import asyncio.test_utils
from tasklocals import local, NoTaskError


class LocalTests(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    def tearDown(self):
        asyncio.test_utils.run_briefly(self.loop)

        self.loop.close()
        gc.collect()

    def test_local(self, strict=True):
        mylocal = local(loop=self.loop, strict=strict)

        log1 = []
        log2 = []

        fut1 = asyncio.Future(loop=self.loop)
        fut2 = asyncio.Future(loop=self.loop)

        @asyncio.coroutine
        def task1():
            # get attributes of the local, must be empty at first
            items = list(mylocal.__dict__.items())
            log1.append(items)
            yield from fut1
            # when the fut1 completes, we have already set mylocal.value to "Task 2" in task2
            # it must not be visible in task1, so the __dict__ should still be empty
            items = list(mylocal.__dict__.items())
            log1.append(items)
            mylocal.value = "Task 1"
            items = list(mylocal.__dict__.items())
            log1.append(items)
            # wake up task2 to ensure that value "Task 1" is not visible in task2
            fut2.set_result(True)

        @asyncio.coroutine
        def task2():
            # get attributes of the local, must be empty at first
            items = list(mylocal.__dict__.items())
            log2.append(items)
            mylocal.value = "Task 2"
            # wake up task1
            fut1.set_result(True)
            # wait for task1 to complete
            yield from fut2
            # value "Task 1" must not be visible in this task
            items = list(mylocal.__dict__.items())
            log2.append(items)

        self.loop.run_until_complete(asyncio.wait((task1(), task2()), loop=self.loop))
        # ensure that the values logged are as expected
        self.assertEqual(log1, [[], [], [('value', 'Task 1')]])
        self.assertEqual(log2, [[], [('value', 'Task 2')]])
        # ensure all task local values have been properly cleaned up
        self.assertEqual(object.__getattribute__(mylocal, '_local__impl').dicts, {})

    def test_local_non_strict_mode(self):
        self.test_local(strict=False)

    def test_local_outside_of_task(self):
        mylocal = local(loop=self.loop)
        try:
            mylocal.foo = 1
            self.fail("NoTaskError has not been raised when tryint to use local object outside of a Task")
        except NoTaskError:
            pass

    def test_local_outside_of_task_non_strict_mode(self):
        mylocal = local(loop=self.loop, strict=False)
        try:
            mylocal.foo = 1
        except NoTaskError:
            self.fail("NoTaskError has been raised when tryint to use non-strict local object outside of a Task")
