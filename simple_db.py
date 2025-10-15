#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простая база данных
SQLite база для хранения записей с веб-интерфейсом
"""

import sqlite3
import json
from datetime import datetime

class SimpleDB:
    def __init__(self, db_name="simple.db"):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """Инициализирует базу данных"""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add_record(self, title, content="", category="общее"):
        """Добавляет новую запись"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute(
                "INSERT INTO records (title, content, category) VALUES (?, ?, ?)",
                (title, content, category)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_records(self, category=None, search=None, limit=50):
        """Получает записи с фильтрацией"""
        query = "SELECT * FROM records WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if search:
            query += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_record(self, record_id):
        """Получает запись по ID"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_record(self, record_id, title=None, content=None, category=None):
        """Обновляет запись"""
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        
        if not updates:
            return False
        
        params.append(record_id)
        query = f"UPDATE records SET {', '.join(updates)} WHERE id = ?"
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_record(self, record_id):
        """Удаляет запись"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_categories(self):
        """Получает список категорий"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute("SELECT DISTINCT category FROM records ORDER BY category")
            return [row[0] for row in cursor.fetchall()]
    
    def get_stats(self):
        """Получает статистику базы"""
        with sqlite3.connect(self.db_name) as conn:
            # Общее количество записей
            total = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
            
            # По категориям
            cursor = conn.execute("SELECT category, COUNT(*) FROM records GROUP BY category")
            categories = dict(cursor.fetchall())
            
            # Последние записи
            cursor = conn.execute("SELECT DATE(created_at) as date, COUNT(*) FROM records GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 7")
            recent_activity = dict(cursor.fetchall())
            
            return {
                'total_records': total,
                'categories': categories,
                'recent_activity': recent_activity
            }
    
    def export_json(self, filename=None):
        """Экспортирует данные в JSON"""
        records = self.get_records(limit=10000)  # Все записи
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2, default=str)
        
        return filename
    
    def import_json(self, filename):
        """Импортирует данные из JSON"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            imported_count = 0
            for record in records:
                if 'title' in record:
                    self.add_record(
                        title=record['title'],
                        content=record.get('content', ''),
                        category=record.get('category', 'импорт')
                    )
                    imported_count += 1
            
            return imported_count
            
        except Exception as e:
            print(f"❌ Ошибка импорта: {e}")
            return 0

def main():
    db = SimpleDB()
    print("=== ПРОСТАЯ БАЗА ДАННЫХ ===\n")
    
    while True:
        print("1. Добавить запись")
        print("2. Показать записи")
        print("3. Найти записи")
        print("4. Редактировать запись")
        print("5. Удалить запись")
        print("6. Статистика")
        print("7. Экспорт в JSON")
        print("8. Импорт из JSON")
        print("9. Выход")
        
        choice = input("\nВыберите действие: ")
        
        if choice == "1":
            title = input("Заголовок: ").strip()
            if not title:
                print("❌ Заголовок обязателен")
                continue
            
            content = input("Содержание (необязательно): ").strip()
            
            categories = db.get_categories()
            if categories:
                print(f"Существующие категории: {', '.join(categories)}")
            
            category = input("Категория (по умолчанию 'общее'): ").strip() or "общее"
            
            record_id = db.add_record(title, content, category)
            print(f"✅ Запись добавлена с ID: {record_id}")
        
        elif choice == "2":
            categories = db.get_categories()
            if categories:
                print(f"Категории: {', '.join(categories)}")
                category_filter = input("Фильтр по категории (или Enter для всех): ").strip()
                category_filter = category_filter if category_filter else None
            else:
                category_filter = None
            
            records = db.get_records(category=category_filter)
            
            if records:
                print(f"\n📋 ЗАПИСИ ({len(records)})")
                print("=" * 60)
                for record in records:
                    created = record['created_at'][:19]  # Без миллисекунд
                    print(f"ID: {record['id']} | {record['category'].upper()}")
                    print(f"📝 {record['title']}")
                    if record['content']:
                        content_preview = record['content'][:80] + "..." if len(record['content']) > 80 else record['content']
                        print(f"   {content_preview}")
                    print(f"   🕒 {created}")
                    print("-" * 40)
            else:
                print("Записей не найдено")
        
        elif choice == "3":
            search_term = input("Поисковый запрос: ").strip()
            if search_term:
                records = db.get_records(search=search_term)
                
                if records:
                    print(f"\n🔍 РЕЗУЛЬТАТЫ ПОИСКА ({len(records)})")
                    print("=" * 60)
                    for record in records:
                        print(f"ID: {record['id']} | {record['title']}")
                        if record['content']:
                            print(f"   {record['content'][:100]}...")
                        print("-" * 30)
                else:
                    print("Ничего не найдено")
        
        elif choice == "4":
            try:
                record_id = int(input("ID записи для редактирования: "))
                record = db.get_record(record_id)
                
                if record:
                    print(f"\nТекущая запись:")
                    print(f"Заголовок: {record['title']}")
                    print(f"Содержание: {record['content']}")
                    print(f"Категория: {record['category']}")
                    
                    new_title = input(f"Новый заголовок (Enter для '{record['title']}'): ").strip()
                    new_content = input(f"Новое содержание (Enter для сохранения): ").strip()
                    new_category = input(f"Новая категория (Enter для '{record['category']}'): ").strip()
                    
                    # Обновляем только измененные поля
                    title = new_title if new_title else None
                    content = new_content if new_content != "" else None
                    category = new_category if new_category else None
                    
                    if db.update_record(record_id, title, content, category):
                        print("✅ Запись обновлена")
                    else:
                        print("❌ Нечего обновлять")
                else:
                    print("❌ Запись не найдена")
                    
            except ValueError:
                print("❌ Некорректный ID")
        
        elif choice == "5":
            try:
                record_id = int(input("ID записи для удаления: "))
                record = db.get_record(record_id)
                
                if record:
                    print(f"Запись: {record['title']}")
                    confirm = input("Удалить? (y/N): ").lower()
                    
                    if confirm == 'y':
                        if db.delete_record(record_id):
                            print("✅ Запись удалена")
                        else:
                            print("❌ Ошибка удаления")
                    else:
                        print("Удаление отменено")
                else:
                    print("❌ Запись не найдена")
                    
            except ValueError:
                print("❌ Некорректный ID")
        
        elif choice == "6":
            stats = db.get_stats()
            print(f"\n📊 СТАТИСТИКА БАЗЫ")
            print("=" * 30)
            print(f"Всего записей: {stats['total_records']}")
            
            if stats['categories']:
                print(f"\nПо категориям:")
                for category, count in stats['categories'].items():
                    print(f"  {category}: {count}")
            
            if stats['recent_activity']:
                print(f"\nАктивность по дням:")
                for date, count in list(stats['recent_activity'].items())[:5]:
                    print(f"  {date}: {count} записей")
        
        elif choice == "7":
            filename = input("Имя файла (или Enter для авто): ").strip()
            filename = filename if filename else None
            
            exported_file = db.export_json(filename)
            print(f"✅ Данные экспортированы в {exported_file}")
        
        elif choice == "8":
            filename = input("Имя файла для импорта: ").strip()
            if filename:
                imported_count = db.import_json(filename)
                if imported_count > 0:
                    print(f"✅ Импортировано записей: {imported_count}")
                else:
                    print("❌ Импорт не удался")
            else:
                print("❌ Не указан файл")
        
        elif choice == "9":
            break
            
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
