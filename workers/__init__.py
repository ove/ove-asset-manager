from typing import Callable, Union

from common.entities import WorkerType


def factory_worker(worker_type: WorkerType) -> Union[Callable, None]:
    if worker_type is WorkerType.EXTRACT:
        from workers.zip import ZipWorker
        return ZipWorker
    elif worker_type is WorkerType.DZ_IMAGE:
        return None
    else:
        return None
