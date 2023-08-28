# Reference https://superfastpython.com/multiprocessing-in-python/

import multiprocessing
import time


def test_barrier():
    def task(barrier):
        print("task")
        time.sleep(2)
        barrier.wait(timeout=10)

    # need to configure the barrier to wait the main process and the 10 subprocesses
    barrier = multiprocessing.Barrier(10 + 1)
    processes = [multiprocessing.Process(target=task, args=(barrier,)) for _ in range(10)]

    for process in processes:
        process.start()

    barrier.wait()
    print("main finished")

def test_event():
    def task(event):
        # 
        print("task waiting")
        event.wait()
        print(multiprocessing.current_process().name)

    def other_task():
        time.sleep(1)
        print("other task")

    event = multiprocessing.Event()
    processes = [multiprocessing.Process(target=task, args=(event,)) for _ in range(10)]

    for process in processes:
        # all processes are started, but stop waiting the event.set()
        process.start()

    for _ in range(3):
        # is executed while the task wait 
        other_process = multiprocessing.Process(target=other_task)
        other_process.start()
        other_process.join()

    time.sleep(3)
    # release the task to run
    event.set()

    for process in processes:
        process.join()

    print("main finished")

    # Output
    # task waiting
    # task waiting
    # task waiting
    # task waiting
    # task waiting
    # task waiting
    # task waiting
    # task waiting
    # task waiting
    # task waiting
    # other task
    # other task
    # other task
    # Process-3
    # Process-2
    # Process-1
    # Process-6
    # Process-4
    # Process-5
    # Process-10
    # Process-9
    # Process-7
    # Process-8
    # main finished



def test_semaphore():
    # Runs 3 processes each time
    # if put a "with semaphore" before the creation of the processes
    # the main process is counted in semaphore
    def task(semaphore):
        with semaphore:
            time.sleep(1)
            print(multiprocessing.current_process().name)

    semaphore = multiprocessing.Semaphore(3)
    processes = [multiprocessing.Process(target=task, args=(semaphore,)) for _ in range(10)]

    for process in processes:
        process.start()

    for process in processes:
        process.join()

    print("main finished")

def test_conditions_with_task_generating_many_processes():
    # if MY_NUM bigger than RANGE, the subprocesses does not notify the main process
    # the main process waits until timeout
    # the subprocesses are died after the timeout, because each subproce waits 1s and the timeout is 2s
    # so the subprocess dies in 1s, but the main process keeps runnig for 1s more (2s) 
    #
    # if MY_NUM smaller than RANGE, subprocess notify the main process, but the main process runs after 1s
    # of execution of subprocesses. The noification does not runs the main process immediately 
    MY_NUM = 30
    RANGE = range(5)

    def task(my_num, condition):
        print("running task")
        time.sleep(1)
        # need to be called inside a task executed by a Process, otherwise does not notify the waiter process
        with condition:
            if my_num >= MY_NUM:
                print(multiprocessing.current_process().name, " notify")
                # just notifies. it is not related with the "is_alive" value of each task
                # if it notifies, it may be alive or dead at the end of the Main process
                condition.notify()

    def task_generator(condition):
        processes = [multiprocessing.Process(target=task, args=(i, condition,)) for i in RANGE]
        for process in processes:
            process.start()
        return processes

    condition = multiprocessing.Condition()
    with condition:
        processes = task_generator(condition)
        # when the subprocess notifies immediately, the timeout is not used
        condition.wait(timeout=2)

    time.sleep(2)
    for process in processes:
        print(process.name, " is alive:", process.is_alive())

    print("done")



def test_conditions_with_task_generator():

    # if the number is not 3, the subprocess does not notify, so the timeout in wait is used
    num_tasks = 3

    def task(qtde_tasks, condition):
        print("do something")
        # need to be called inside a task executed by a Process, otherwise does not notify the waiter process
        with condition:
            print("in condition")
            if qtde_tasks == 3:
                print("notify")
                condition.notify()

    def task_generator(qtde_tasks, condition):
        print("running task")
        print("process: ", multiprocessing.current_process())
        process = multiprocessing.Process(target=task, args=(qtde_tasks, condition,))
        process.start()


    condition = multiprocessing.Condition()
    with condition:
        task_generator(num_tasks, condition)
        # the subprocess notifies immediately, so the timeout is not used
        condition.wait(timeout=2)

    print("done")

def test_conditions_with_queue():

    def send(message, queue, condition):
        with condition:
            print("message: ", message)
            queue.put(message)
            time.sleep(1)
            if queue.qsize() < 3:
                print("notify")
                # notify every time the "if" is True, but does not release the Condition
                condition.notify()

    def receive(queue):
        print("get message: ", queue.get())

    queue = multiprocessing.Queue()
    condition = multiprocessing.Condition()
    senders = [multiprocessing.Process(target=send, args=(f"m{i}", queue, condition,)) for i in range(10)]
    receiver = multiprocessing.Process(target=receive, args=(queue,))
    
    with condition:
        for sender in senders:
            sender.start()
    
        # wait the processes are finished and continues if the Condition is released
        condition.wait()

    for sender in senders:
        print("name: ", sender.name, " is alive: ", sender.is_alive())

    receiver.start()
    print("queue size: ", queue.qsize())

def test_many_conditions_with_many_processes():
    def task(timer, condition):
        with condition:
            print("process name: ", multiprocessing.current_process().name)
            if timer >= 4:
                condition.notify_all()
            time.sleep(timer)
            print("process name: ", multiprocessing.current_process().name, " current state ", multiprocessing.current_process().is_alive())

    condition = multiprocessing.Condition()
    processes = [multiprocessing.Process(name=f"process_{i}", target=task, args=(i, condition)) for i in range(5)]
    
    with condition:
        for process in processes:
            process.start()
            
        for process in processes:
            print("name: ", process.name, " is alive ", process.is_alive())
    
        condition.wait()

        for process in processes:
            print("name: ", process.name, " is alive ", process.is_alive())


def test_condition_with_many_processes():
    def task(timer, condition):
        with condition:
            print("process: ", timer)
            time.sleep(timer)
            if timer >= 3:
                condition.notify()

    condition = multiprocessing.Condition()
    with condition:
        processes = [multiprocessing.Process(target=task, args=(i, condition)) for i in range(5)]
        
        for process in processes:
            process.start()
        condition.wait()
    

def test_condition():
    def task(timer, condition):
        with condition:
            time.sleep(timer)
            condition.notify()

    condition = multiprocessing.Condition()
    with condition:
        process = multiprocessing.Process(target=task, args=(3, condition))
        process.start()
        condition.wait()

    assert process.is_alive() is True
    
def test_return_process_value_with_pipe():
    conn1, conn2 = multiprocessing.Pipe()
    def task(data, conn2):
        conn2.send([data, data])

    process = multiprocessing.Process(target=task, args=(0, conn2, ))
    process.start()
    assert conn1.recv() == [0,0]

def test_lock():
    print("current process: ", multiprocessing.current_process())
    database = multiprocessing.Queue()
    lock = multiprocessing.Lock()

    def task(data, database, lock):
        with lock:
            print("child process: ", multiprocessing.current_process())
            database.put(data)
            print("database: ", database.qsize())

    processes = []
    for i in range(10):
        processes.append(multiprocessing.Process(target=task, args=(i, database, lock,)))

    for process in processes:    
        process.start()
    
    for process in processes:
        process.join()

    for process in processes:
        print("assert: ", database.get())
        print("qsize:", database.qsize())


def test_start_mathod():
    assert multiprocessing.get_start_method() in ["spawn", "forkserver", "fork"]


def teste_cpu_cont():
    assert multiprocessing.cpu_count() >= 1
