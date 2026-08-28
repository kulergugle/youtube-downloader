# -*- coding: utf-8 -*-
"""
YouTube Downloader for Android
Kivy + yt-dlp
"""
import os
import sys
import threading
import traceback
import time

# ========== ЛОГИРОВАНИЕ ==========
LOG_FILE = ''
try:
    from android.storage import app_storage_path
    LOG_DIR = app_storage_path()
except:
    LOG_DIR = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(LOG_DIR):
        LOG_DIR = os.getcwd()

LOG_FILE = os.path.join(LOG_DIR, 'app_log.txt')

def log(msg):
    try:
        ts = time.strftime('%H:%M:%S')
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f'[{ts}] {msg}\n')
    except:
        pass

log('\n========== APP START ==========')

# ========== ANDROID ==========
IS_ANDROID = False
try:
    from android.permissions import request_permissions, Permission
    from jnius import autoclass
    IS_ANDROID = True
    log('Android detected')
except Exception as e:
    log(f'Not Android: {e}')

# ========== KIVY ==========
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.properties import ListProperty, NumericProperty
from kivy.animation import Animation

Window.clearcolor = (0.05, 0.05, 0.08, 1)

# ========== ЦВЕТА ==========
COLORS = {
    'bg': (0.05, 0.05, 0.08, 1),
    'card': (0.1, 0.1, 0.15, 1),
    'card_border': (0.2, 0.2, 0.3, 1),
    'primary': (0.35, 0.55, 1, 1),
    'primary_dark': (0.25, 0.4, 0.85, 1),
    'text': (0.95, 0.95, 0.97, 1),
    'text_secondary': (0.6, 0.6, 0.7, 1),
    'success': (0.3, 0.85, 0.5, 1),
    'error': (0.95, 0.35, 0.35, 1),
    'warning': (1, 0.75, 0.3, 1),
}

# ========== КАСТОМНЫЕ ВИДЖЕТЫ ==========
class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(16)
        self.spacing = dp(12)
        self.size_hint_y = None
        self.bind(pos=self._update_rect, size=self._update_rect)
        with self.canvas.before:
            Color(*COLORS['card'])
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
            Color(*COLORS['card_border'])
            self.border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(16)), width=dp(1.2))

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(16))

class StyledButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = COLORS['primary']
        self.color = COLORS['text']
        self.font_size = dp(16)
        self.bold = True
        self.size_hint_y = None
        self.height = dp(52)

class QualityButton(Button):
    selected = False
    def __init__(self, text='', **kwargs):
        super().__init__(text=text, **kwargs)
        self.background_normal = ''
        self.background_color = (0.15, 0.15, 0.22, 1)
        self.color = COLORS['text_secondary']
        self.font_size = dp(13)
        self.size_hint_y = None
        self.height = dp(40)
        self.bind(on_press=self._toggle)

    def _toggle(self, *args):
        pass

# ========== ГЛАВНОЕ ПРИЛОЖЕНИЕ ==========
class DownloaderApp(App):
    def build(self):
        log('build()')
        if IS_ANDROID:
            try:
                request_permissions([Permission.INTERNET])
            except Exception as e:
                log(f'Permission error: {e}')

        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        # === ШАПКА ===
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        header.add_widget(Label(
            text='[b]YouTube[/b] Downloader',
            markup=True,
            font_size=dp(24),
            color=COLORS['text'],
            halign='left',
            valign='center'
        ))
        root.add_widget(header)

        # === КАРТОЧКА ВВОДА ===
        card_input = Card()
        card_input.add_widget(Label(
            text='Ссылка на видео',
            font_size=dp(14),
            color=COLORS['text_secondary'],
            size_hint_y=None,
            height=dp(20),
            halign='left'
        ))
        self.url_input = TextInput(
            hint_text='https://youtube.com/watch?v=...',
            multiline=False,
            font_size=dp(15),
            size_hint_y=None,
            height=dp(50),
            background_color=(0.06, 0.06, 0.1, 1),
            foreground_color=COLORS['text'],
            hint_text_color=(0.3, 0.3, 0.4, 1),
            cursor_color=COLORS['primary'],
            padding=[dp(12), dp(14)],
            background_normal='',
            background_active=''
        )
        card_input.add_widget(self.url_input)
        card_input.height = dp(90)
        root.add_widget(card_input)

        # === КАРТОЧКА КАЧЕСТВА ===
        card_quality = Card()
        card_quality.add_widget(Label(
            text='Качество видео',
            font_size=dp(14),
            color=COLORS['text_secondary'],
            size_hint_y=None,
            height=dp(20),
            halign='left'
        ))
        quality_grid = GridLayout(cols=3, spacing=dp(8), size_hint_y=None, height=dp(90))

        self.quality_buttons = {}
        qualities = [
            ('360p', '18'),
            ('720p', '22/18'),
            ('Аудио', 'bestaudio/best'),
        ]
        for label, fmt in qualities:
            btn = QualityButton(text=label)
            btn.fmt = fmt
            btn.bind(on_press=self._on_quality)
            self.quality_buttons[label] = btn
            quality_grid.add_widget(btn)

        # Выбираем 360p по умолчанию
        self._select_quality('360p')
        card_quality.add_widget(quality_grid)
        card_quality.height = dp(130)
        root.add_widget(card_quality)

        # === КНОПКА СКАЧАТЬ ===
        self.download_btn = StyledButton(text='⬇  СКАЧАТЬ')
        self.download_btn.bind(on_press=self.start_download)
        root.add_widget(self.download_btn)

        # === ПРОГРЕСС ===
        progress_card = Card()
        self.status = Label(
            text='Готов к работе',
            font_size=dp(14),
            color=COLORS['text_secondary'],
            size_hint_y=None,
            height=dp(24)
        )
        progress_card.add_widget(self.status)

        self.progress = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(8)
        )
        progress_card.add_widget(self.progress)

        self.log_label = Label(
            text='',
            font_size=dp(10),
            color=(0.4, 0.4, 0.5, 1),
            size_hint_y=None,
            height=dp(30),
            halign='center'
        )
        progress_card.add_widget(self.log_label)
        progress_card.height = dp(90)
        root.add_widget(progress_card)

        # === ИНФО ===
        root.add_widget(Widget())  # spacer
        info = Label(
            text='Файлы сохраняются в папку приложения',
            font_size=dp(11),
            color=(0.35, 0.35, 0.45, 1),
            size_hint_y=None,
            height=dp(30)
        )
        root.add_widget(info)

        self.downloading = False
        return root

    def _on_quality(self, btn):
        for b in self.quality_buttons.values():
            b.background_color = (0.15, 0.15, 0.22, 1)
            b.color = COLORS['text_secondary']
            b.selected = False
        self._select_quality(btn.text)

    def _select_quality(self, key):
        btn = self.quality_buttons.get(key)
        if btn:
            btn.background_color = COLORS['primary_dark']
            btn.color = COLORS['text']
            btn.selected = True
            self.selected_format = btn.fmt
            log(f'Selected quality: {key} -> {btn.fmt}')

    def start_download(self, instance):
        if self.downloading:
            return
        url = self.url_input.text.strip()
        if not url:
            self._set_status('Вставь ссылку!', 'error')
            return

        self.downloading = True
        self.download_btn.disabled = True
        self.download_btn.background_color = COLORS['primary_dark']
        self.download_btn.text = '⏳  ЗАГРУЗКА...'
        self.progress.value = 0
        self._set_status('Подключение...', 'warning')

        t = threading.Thread(target=self._download_thread, args=(url,), daemon=True)
        t.start()

    def _download_thread(self, url):
        try:
            # Путь сохранения
            save_dir = self._get_save_dir()
            log(f'Save dir: {save_dir}')

            # Проверка записи
            test_file = os.path.join(save_dir, '.test')
            with open(test_file, 'w') as f:
                f.write('ok')
            os.remove(test_file)
            log('Directory writable')

            outtmpl = os.path.join(save_dir, '%(title)s.%(ext)s')
            fmt = getattr(self, 'selected_format', '18')
            log(f'Format: {fmt}, URL: {url}')

            ydl_opts = {
                'format': fmt,
                'outtmpl': outtmpl,
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self._progress_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                log(f'Downloaded: {filename}')

            basename = os.path.basename(filename)
            Clock.schedule_once(lambda dt: self._on_success(basename), 0)

        except Exception as e:
            err = traceback.format_exc()
            log(f'ERROR: {err}')
            Clock.schedule_once(lambda dt: self._on_error(str(e)), 0)

    def _get_save_dir(self):
        # Способ 1: pyjnius
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            ctx = PythonActivity.mActivity
            path = ctx.getFilesDir().getAbsolutePath()
            log(f'Path via pyjnius: {path}')
            return path
        except Exception as e:
            log(f'pyjnius failed: {e}')

        # Способ 2: app_storage_path
        try:
            from android.storage import app_storage_path
            path = app_storage_path()
            log(f'Path via app_storage: {path}')
            return path
        except Exception as e:
            log(f'app_storage failed: {e}')

        # Fallback
        path = os.path.join(os.path.expanduser('~'), 'Downloads', 'YT')
        os.makedirs(path, exist_ok=True)
        log(f'Path fallback: {path}')
        return path

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                percent_str = d.get('_percent_str', '0%')
                percent = float(percent_str.replace('%', '').strip())
                Clock.schedule_once(lambda dt, p=percent: self._update_progress(p), 0)
            except:
                pass
        elif d['status'] == 'finished':
            Clock.schedule_once(lambda dt: self._update_progress(100), 0)

    def _update_progress(self, percent):
        self.progress.value = percent
        self.status.text = f'Загрузка... {percent:.0f}%'
        self.status.color = COLORS['warning']

    def _on_success(self, filename):
        self.downloading = False
        self.download_btn.disabled = False
        self.download_btn.background_color = COLORS['primary']
        self.download_btn.text = '⬇  СКАЧАТЬ'
        self.progress.value = 100
        self._set_status(f'Сохранено: {filename}', 'success')
        self.log_label.text = f'Папка: {LOG_FILE}'

    def _on_error(self, error):
        self.downloading = False
        self.download_btn.disabled = False
        self.download_btn.background_color = COLORS['primary']
        self.download_btn.text = '⬇  СКАЧАТЬ'
        self.progress.value = 0
        self._set_status(f'Ошибка: {error[:80]}', 'error')
        self.log_label.text = f'Лог: {LOG_FILE}'

    def _set_status(self, text, mode='normal'):
        self.status.text = text
        if mode == 'success':
            self.status.color = COLORS['success']
        elif mode == 'error':
            self.status.color = COLORS['error']
        elif mode == 'warning':
            self.status.color = COLORS['warning']
        else:
            self.status.color = COLORS['text_secondary']

if __name__ == '__main__':
    DownloaderApp().run()
