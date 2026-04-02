# coding: utf-8

"""
pretty printing class
"""

from __future__ import annotations
import os.path as osp
from typing import Tuple


def make_abs_path(fn):
    import os
    base_dir = osp.dirname(osp.realpath(__file__))
    # 确保路径使用正确的编码
    abs_path = osp.join(base_dir, fn)
    # 规范化路径，处理..和.
    abs_path = osp.normpath(abs_path)
    # 确保路径使用正确的编码
    if isinstance(abs_path, bytes):
        abs_path = abs_path.decode('utf-8')
    return abs_path


class PrintableConfig:  # pylint: disable=too-few-public-methods
    """Printable Config defining str function"""

    def __repr__(self):
        lines = [self.__class__.__name__ + ":"]
        for key, val in vars(self).items():
            if isinstance(val, Tuple):
                flattened_val = "["
                for item in val:
                    flattened_val += str(item) + "\n"
                flattened_val = flattened_val.rstrip("\n")
                val = flattened_val + "]"
            lines += f"{key}: {str(val)}".split("\n")
        return "\n    ".join(lines)
