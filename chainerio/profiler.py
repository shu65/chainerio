import abc
from abc import abstractmethod
import chainerio
from chainerio.profile_writer import ProfileWriter

from typing import Optional, Any, Union, Type

import functools


class Profiler(abc.ABC):
    def __init__(self, profile_writer: Type[ProfileWriter]):
        self.name = "BaseProfiler"
        self.profile_writer = profile_writer

        self.profile_list = []
        self.matrix_dict = dict()
        self.start_time = -1
        self.end_time = -1

    @property
    def recorded_time(self) -> float:
        return self.end_time - self.start_time

    @abstractmethod
    def start_recording(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def stop_recording(self) -> None:
        raise NotImplementedError()

    def clean(self):
        self.reset()
        self.profile_list = []

    def reset(self):
        self.start_time = -1
        self.end_time = -1
        self.reset_matrix()

    def reset_matrix(self) -> None:
        self.matrix_dict = dict()

    def add_matrix(self, key: Any, value: Any) -> None:
        self.matrix_dict[key] = value

    def get_matrix(self) -> dict:
        return self.matrix_dict

    def save_profile(self, matrix: Optional[dict] = None) -> None:
        if not chainerio.context.profiling:
            return

        if None is matrix:
            profile_entry = self.generate_profile_dict()
        else:
            # merge the new profile_dict with the old profile_dict
            profile_entry = {**matrix, **self.matrix_dict}
        self.profile_list.append(profile_entry)

    def show(self) -> dict:
        return self.profile_list

    @abstractmethod
    def generate_profile_dict(self, ts: float = 0,
                              event_type: str = "X") -> dict:
        raise NotImplementedError()

    @abstractmethod
    def get_profile_file_path(self) -> Union[str, None]:
        raise NotImplementedError()

    @abstractmethod
    def dump(self, filepath: Optional[str] = None) -> None:
        raise NotImplementedError()

    def __enter__(self):
        self.start_recording()

    @abstractmethod
    def __exit__(self, typ, value, traceback):
        raise NotImplementedError()


def profiling_decorator(func):
    @functools.wraps(func)
    def inner(self, *args, **kwargs):
        profiler = chainerio.context.profiler
        profiler.add_matrix("name", func.__name__)
        profiler.add_matrix("args", args)
        profiler.add_matrix("kwargs", kwargs)

        with profiler:
            ret = func(self, *args, **kwargs)

        return ret

    return inner


def profiling():
    return chainerio.using_config('profiling', True)


def dump_profile() -> None:
    chainerio.context.profiler.dump()
