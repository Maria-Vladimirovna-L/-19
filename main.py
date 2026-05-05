import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import webbrowser
import os

# --- Настройки ---
FAVORITES_FILE = 'favorites.json'
GITHUB_API_URL = 'https://api.github.com/search/users'

# --- Функции работы с данными ---
def load_favorites():
    """Загружает избранных пользователей из файла JSON."""
    try:
        with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_favorites(favorites):
    """Сохраняет список избранных пользователей в файл JSON."""
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)

# --- Функции интерфейса ---
def search_users():
    """Выполняет поиск пользователей по введенному запросу."""
    query = search_entry.get().strip()
    if not query:
        messagebox.showerror('Ошибка', 'Поле поиска не должно быть пустым')
        return

    try:
        response = requests.get(GITHUB_API_URL, params={'q': query})
        response.raise_for_status()
        data = response.json()
        users = data.get('items', [])
        update_search_results(users)
    except requests.exceptions.RequestException as e:
        messagebox.showerror('Ошибка сети', f'Не удалось подключиться к GitHub API: {e}')

def update_search_results(users):
    """Обновляет виджет Treeview с результатами поиска."""
    for i in results_tree.get_children():
        results_tree.delete(i)
    
    for user in users:
        login = user.get('login', '')
        avatar_url = user.get('avatar_url', '')
        html_url = user.get('html_url', '')
        
        # Проверяем, есть ли пользователь в избранном
        is_favorite = any(fav.get('login') == login for fav in favorites)
        
        results_tree.insert('', 'end', 
                           values=(login, avatar_url, html_url), 
                           tags=('favorite' if is_favorite else 'not_favorite'))

def on_user_click(event):
    """Открывает профиль пользователя в браузере при двойном клике."""
    item = results_tree.identify('item', event.x, event.y)
    if item:
        values = results_tree.item(item, 'values')
        if values and values[2]: # values[2] - это html_url
            webbrowser.open(values[2])

def toggle_favorite(event):
    """Добавляет или удаляет пользователя из избранного по правому клику."""
    item = results_tree.identify('item', event.x, event.y)
    if not item:
        return

    values = results_tree.item(item, 'values')
    if not values:
        return

    login = values[0]
    
    # Ищем пользователя в глобальном списке избранного
    found_index = next((i for i, fav in enumerate(favorites) if fav.get('login') == login), -1)

    if found_index != -1:
        del favorites[found_index]
        messagebox.showinfo('Успех', f'Пользователь {login} удален из избранного.')
    else:
        try:
            user_data = requests.get(f'https://api.github.com/users/{login}').json()
            favorites.append(user_data)
            messagebox.showinfo('Успех', f'Пользователь {login} добавлен в избранное.')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось добавить в избранное: {e}')
            return

    save_favorites(favorites)
    update_search_results(get_current_search_results())

def get_current_search_results():
    """Возвращает текущие данные из таблицы для обновления статуса избранного."""
    items = []
    for child in results_tree.get_children():
        vals = results_tree.item(child, 'values')
        if vals:
            items.append({'login': vals[0], 'avatar_url': vals[1], 'html_url': vals[2]})
    return items

# --- Инициализация приложения ---
root = tk.Tk()
root.title('GitHub User Finder')
root.geometry('800x600')

# Загружаем избранное при старте
favorites = load_favorites()

# Поле поиска и кнопка
top_frame = ttk.Frame(root)
top_frame.pack(pady=10, fill='x')

search_entry = ttk.Entry(top_frame, width=50)
search_entry.pack(side='left', padx=5, expand=True, fill='x')

search_btn = ttk.Button(top_frame, text='Поиск', command=search_users)
search_btn.pack(side='left', padx=5)

# Таблица результатов
results_tree = ttk.Treeview(root, columns=('Login', 'Avatar URL', 'Profile URL'), show='headings')
results_tree.heading('Login', text='Логин')
results_tree.column('Login', width=150)
results_tree.heading('Avatar URL', text='Аватар')
results_tree.column('Avatar URL', width=200)
results_tree.heading('Profile URL', text='Ссылка')
results_tree.column('Profile URL', width=200)
results_tree.pack(padx=10, pady=10, fill='both', expand=True)

# Стили для избранного
style = ttk.Style()
style.configure('favorite.Treeview', background='#FFFACD') 
results_tree.tag_configure('favorite', background='#FFFACD')
results_tree.tag_configure('not_favorite', background='white')

# Привязка событий
results_tree.bind('<Double-1>', on_user_click)  # Двойной клик
results_tree.bind('<Button-3>', toggle_favorite) # Правый клик

root.mainloop()
