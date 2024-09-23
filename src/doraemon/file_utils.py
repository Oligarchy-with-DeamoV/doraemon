import os
from typing import Any, Dict, List, Literal

from numbers_parser import Document
import pandas as pd


def load_numbers(numbers_filepath: str) -> List[Dict[str, Any]]:
    """
    加载 Numbers 文件并将其转换为 pd.DataFrame。

    参数:
    numbers_filepath (str): Numbers 文件的路径。

    返回:
    List[Dict[str, Any]]: 包含每个表格名称和对应数据框的字典列表。
    每个字典包含两个键：
    - "name": 表格的名称。
    - "data": 表格内容的 pd.DataFrame。
    """
    doc = Document(numbers_filepath)
    dataframe_lists = list()
    sheets = doc.sheets
    for sheet in sheets:
        tables = sheet.tables
        dataframe_lists.extend(
            [
                {
                    "name": t.name,
                    "data": pd.DataFrame(
                        t.rows(values_only=True)[1:],
                        columns=t.rows(values_only=True)[0],
                    ),
                }
                for t in tables
            ]
        )
    return dataframe_lists


def find_all_filepaths(
    source_folder: str, filetype: Literal["csv", "numbers", "xlsx"]
) -> List[str]:
    """
    获取指定文件夹中所有特定类型的文件路径。

    参数:
    source_folder (str): 要搜索的源文件夹路径。
    filetype (Literal["csv", "numbers", "xlsx"]): 要查找的文件类型。

    返回:
    List[str]: 包含所有符合条件的文件的完整路径列表。
    """
    return_file_paths = []
    for root, _, files in os.walk(source_folder):
        for filename in files:
            if filename.endswith(f".{filetype}"):
                # Construct full file path
                source_file = os.path.join(root, filename)
                return_file_paths.append(source_file)
    return return_file_paths
