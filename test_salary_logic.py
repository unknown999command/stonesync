#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from datetime import datetime

def test_comment_parsing():
    """Тестируем парсинг комментариев"""
    
    # Тестовые комментарии (как в примере пользователя)
    test_comments = [
        "👷 Исполнитель: Акишин -> Система",
        "⏳ Статус: Монтаж -> Завершено",
        "💵 Цена за монтаж: 10000 -> None",
        "💵 Цена за изготовление: 10000 -> None",
        "👷 Исполнитель: Виталик -> Акишин",
        "⏳ Статус: Изготовление -> Монтаж",
        "👷 Исполнитель: Скуридин -> Виталик",
        "💵 Цена за монтаж: None -> 10000",
        "💵 Цена за изготовление: None -> 10000",
        "👷 Исполнитель: Устимов -> Скуридин",
        "⏳ Статус: Замер -> Изготовление"
    ]
    
    print("=== Тест парсинга комментариев ===\n")
    
    # Тестируем регулярные выражения
    for comment in test_comments:
        print(f"Комментарий: {comment}")
        
        # Поиск назначения исполнителя
        executor_match = re.search(r'👷 Исполнитель: (.+?) -> (.+)', comment)
        if executor_match:
            old_executor = executor_match.group(1).strip()
            new_executor = executor_match.group(2).strip()
            print(f"  Исполнитель: {old_executor} -> {new_executor}")
        
        # Поиск изменения статуса
        status_match = re.search(r'⏳ Статус: (.+?) -> (.+)', comment)
        if status_match:
            old_status = status_match.group(1).strip()
            new_status = status_match.group(2).strip()
            print(f"  Статус: {old_status} -> {new_status}")
        
        # Поиск изменения цен
        price_match = re.search(r'💵 Цена за (изготовление|монтаж): (.+?) -> (.+)', comment)
        if price_match:
            work_type = price_match.group(1)
            old_price = price_match.group(2).strip()
            new_price = price_match.group(3).strip()
            print(f"  Цена за {work_type}: {old_price} -> {new_price}")
        
        print()

def test_improved_logic():
    """Тестируем улучшенную логику определения исполнителей"""
    
    print("=== Тест улучшенной логики ===\n")
    
    # Симулируем комментарии в хронологическом порядке (как в примере пользователя)
    comments = [
        "👷 Исполнитель: Устимов -> Скуридин\n⏳ Статус: Замер -> Изготовление",
        "💵 Цена за монтаж: None -> 10000",
        "💵 Цена за изготовление: None -> 10000",
        "👷 Исполнитель: Скуридин -> Виталик",
        "👷 Исполнитель: Виталик -> Акишин\n⏳ Статус: Изготовление -> Монтаж",
        "👷 Исполнитель: Акишин -> Система\n⏳ Статус: Монтаж -> Завершено"
    ]
    
    izgotovlenie_worker = None
    montaj_worker = None
    last_workers = {}
    current_status = None
    
    print("Анализ комментариев по порядку:")
    
    for i, comment in enumerate(comments):
        print(f"\nШаг {i+1}: {comment}")
        
        # Поиск изменения статуса
        status_match = re.search(r'⏳ Статус: (.+?) -> (.+)', comment)
        if status_match:
            old_status = status_match.group(1).strip()
            new_status = status_match.group(2).strip()
            current_status = new_status
            print(f"  Статус: {old_status} -> {new_status}")
        
        # Поиск назначения исполнителя
        executor_match = re.search(r'👷 Исполнитель: (.+?) -> (.+)', comment)
        if executor_match:
            old_executor = executor_match.group(1).strip()
            new_executor = executor_match.group(2).strip()
            print(f"  Исполнитель: {old_executor} -> {new_executor}")
            
            # Сохраняем последнего исполнителя для каждого статуса
            if current_status:
                last_workers[current_status] = new_executor
                print(f"  Сохраняем {new_executor} для статуса '{current_status}'")
            
            # Если в том же комментарии есть изменение статуса
            if status_match:
                if new_status == "Изготовление":
                    izgotovlenie_worker = new_executor
                    print(f"  => {new_executor} назначен изготовителем")
                elif new_status == "Монтаж":
                    montaj_worker = new_executor
                    print(f"  => {new_executor} назначен монтажником")
    
    print(f"\nПоследние исполнители по статусам: {last_workers}")
    
    # Если не определили исполнителей через изменения статуса,
    # берем последних исполнителей для соответствующих статусов
    if not izgotovlenie_worker and "Изготовление" in last_workers:
        izgotovlenie_worker = last_workers["Изготовление"]
        print(f"Берем последнего изготовителя: {izgotovlenie_worker}")
    
    if not montaj_worker and "Монтаж" in last_workers:
        montaj_worker = last_workers["Монтаж"]
        print(f"Берем последнего монтажника: {montaj_worker}")
    
    # Если заказ завершен, проверяем последних исполнителей
    if "Завершено" in last_workers:
        print("Заказ завершен, проверяем последних исполнителей...")
        # Если не определили изготовителя, берем последнего исполнителя перед завершением
        if not izgotovlenie_worker:
            # Ищем последнего исполнителя для статуса "Изготовление" или "Монтаж"
            for status in ["Изготовление", "Монтаж"]:
                if status in last_workers:
                    if status == "Изготовление":
                        izgotovlenie_worker = last_workers[status]
                        print(f"Берем изготовителя из статуса '{status}': {izgotovlenie_worker}")
                    elif status == "Монтаж":
                        montaj_worker = last_workers[status]
                        print(f"Берем монтажника из статуса '{status}': {montaj_worker}")
    
    print(f"\n=== РЕЗУЛЬТАТ ===")
    print(f"Изготовитель: {izgotovlenie_worker}")
    print(f"Монтажник: {montaj_worker}")
    print(f"Ожидаемый результат: Виталик (изготовление), Акишин (монтаж)")

if __name__ == "__main__":
    test_comment_parsing()
    test_improved_logic() 