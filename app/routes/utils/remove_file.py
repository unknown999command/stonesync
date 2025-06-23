import os

def remove_file(directory, filename):
    if filename:  # Проверка, что имя файла не None и не пустое
        file_path = os.path.join(directory, filename)  # Формирование полного пути к файлу
        if os.path.exists(file_path):  # Проверка существования файла
            os.remove(file_path)  # Удаление файла