from typing import Callable, Union

from common.entities import WorkerType


def factory_worker(worker_type: WorkerType) -> Union[Callable, None]:
    if worker_type is WorkerType.ZIP:
        from workers.zip import ZipWorker
        return ZipWorker
    elif worker_type is WorkerType.IMAGE:
        return None
    else:
        return None
