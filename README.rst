Task locals support for tulip/asyncio
~~~~~~~~~~~~~~~~~~~~~

It provides Task local storage similar to python's threading.local
but for Tasks in asyncio.

Using task locals has some caveats:

* Unlike thread locals, where you are always sure that at least one thread is running(namely main thread), Task locals are available only in the context of a running Task. So if you try to access a task local from outside a Task you will get a RuntimeError.
* Be aware that using asyncio.async, asyncio.wait, asyncio.gather, asyncio.shield and friends launches a new task, so these coroutines will have its own local storage.

For more information on using locals see the docs for threading.local in python's standard library
