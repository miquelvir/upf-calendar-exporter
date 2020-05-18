import csv
from typing import List


def export_csv(rows: List[list], file_path: str) -> bool:
    """

    :param rows: list of dict representing valid sessions (with title, start time and end time at least)
    :param file_path: a valid verified path
    :return true if successful, false otherwise
    """
    try:
        with open(file_path, 'w', newline='', encoding='utf8') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
        print("exported csv successfully")
        return True
    except Exception as e:
        print("error exporting csv... see details below")
        print(e)
        return False
