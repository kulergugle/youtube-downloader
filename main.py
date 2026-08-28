# -*- coding: utf-8 -*-
import sys
import os
import threading
import traceback

# ========== ЗАЩИЩЁННЫЙ ЗАПУСК ==========
# Если что-то сломается на этапе импорта — покажем на экране
STARTUP_ERROR = None
STARTUP_TRACEBACK = ''

try:
    from kivy.app import App
    from kivy.core.window import Window
    from kivy.clock import Clock
    from kivy.metrics import dp
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.progressbar import ProgressBar
    from kivy.uix.widget import Widget
    KIVY_OK = True
except Exception as e:
    KIVY_OK = False
    STARTUP_ERROR = f'KIVY IMPORT ERROR: {e}'
    STARTUP_TRACEBACK = traceback.format_exc()

# Цвета
BG = (0.06, 0.06, 0.1, 1)
PRIMARY = (0.3, 0.55, 0.95, 1)
PRIMARY_DARK = (0.2, 0.4, 0.8, 1)
TEXT = (0.95, 0.95, 0.97, 1)
TEXT_SEC = (0.55, 0.55, 0.65, 1)
SUCCESS = (0.3, 0.8, 0.5, 1)
ERROR = (0.9, 0.35, 0.35, 1)
WARN = (1, 0.7, 0.3, 1)

# yt-dlp
try:
    import yt_dlp
    YTDLP_OK = True
except Exception as e:
    YTDLP_OK = False
    if not STARTUP_ERROR:
        STARTUP_ERROR = f'YT-DLP IMPORT ERROR: {e}'
        STARTUP_TRACEBACK = traceback.format_exc()

# Android
try:
    from android.permissions import request_permissions, Permission
    IS_ANDROID = True
except:
    IS_ANDROID = False

# pyjnius
try:
    from jnius import autoclass
    JNIUS_OK = True
except:
    JNIUS_OK = False


def get_save_dir():
    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        ctx = PythonActivity.mActivity
        return ctx.getFilesDir().getAbsolutePath()
    except:
        pass
    try:
        from android.storage import app_storage_path
        return app_storage_path()
    except:
        pass
    path = os.path.join(os.path.expanduser('~'), 'Downloads')
    os.makedirs(path, exist_ok=True)
    return path


class DownloaderApp(App):
    def build(self):
        Window.clearcolor = BG

        # Если импорты сломались — показываем ошибку и выходим
        if not KIVY_OK or STARTUP_ERROR:
            return self._error_screen(STARTUP_ERROR or 'Unknown startup error')

        self.downloading = False
        self.selected_fmt = '18'

        root = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(14))

        root.add_widget(Label(
            text='YouTube Downloader',
            font_size=dp(26),
            color=TEXT,
            size_hint_y=None,
            height=dp(50),
            bold=True
        ))

        # Поле ввода
        self.url_input = TextInput(
            hint_text='https://youtube.com/watch?v=...',
            multiline=False,
            font_size=dp(15),
            size_hint_y=None,
            height=dp(50),
            background_color=(0.08, 0.08, 0.14, 1),
            foreground_color=TEXT,
            hint_text_color=(0.35, 0.35, 0.45, 1),
            cursor_color=PRIMARY,
            padding=[dp(14), dp(15)]
        )
        root.add_widget(self.url_input)

        # Качество
        root.add_widget(Label(
            text='Качество:', font_size=dp(14), color=TEXT_SEC,
            size_hint_y=None, height=dp(28), halign='left'
        ))
        qual_grid = GridLayout(cols=3, spacing=dp(10), size_hint_y=None, height=dp(48))
        self.qual_btns = {}
        for label, fmt in [('360p', '18'), ('720p', '22/18'), ('Аудио', 'bestaudio/best')]:
            btn = Button(text=label, font_size=dp(14),
                         background_color=(0.15, 0.15, 0.22, 1), color=TEXT_SEC)
            btn.fmt = fmt
            btn.bind(on_press=self._on_qual)
            self.qual_btns[label] = btn
            qual_grid.add_widget(btn)
        self._select_qual('360p')
        root.add_widget(qual_grid)

        # Кнопка
        self.dl_btn = Button(
            text='СКАЧАТЬ', font_size=dp(18), bold=True,
            size_hint_y=None, height=dp(54),
            background_color=PRIMARY, color=TEXT
        )
        self.dl_btn.bind(on_press=self.start_download)
        root.add_widget(self.dl_btn)

        # Прогресс
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))
        root.add_widget(self.progress)

        # Статус
        self.status = Label(
            text='Готов', font_size=dp(14), color=TEXT_SEC,
            size_hint_y=None, height=dp(36)
        )
        root.add_widget(self.status)

        # Инфо о yt-dlp
        if not YTDLP_OK:
            root.add_widget(Label(
                text='⚠ yt-dlp НЕ загружен!',
                font_size=dp(13), color=ERROR,
                size_hint_y=None, height=dp(30)
            ))

        root.add_widget(Widget())
        return root

    def _error_screen(self, msg):
        """Показывает ошибку импорта — приложение не падает молча"""
        box = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        box.add_widget(Label(
            text='ОШИБКА ЗАПУСКА',
            font_size=dp(22), color=ERROR, bold=True,
            size_hint_y=None, height=dp(50)
        ))
        box.add_widget(Label(
            text=msg,
            font_size=dp(14), color=TEXT,
            size_hint_y=None, height=dp(80)
        ))
        # Полный traceback в ScrollView
        scroll = ScrollView(size_hint=(1, 1))
        tb_label = Label(
            text=STARTUP_TRACEBACK,
            font_size=dp(11), color=TEXT_SEC,
            size_hint_y=None, text_size=(Window.width - dp(40), None)
        )
        tb_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        scroll.add_widget(tb_label)
        box.add_widget(scroll)
        return box

    def _on_qual(self, btn):
        for b in self.qual_btns.values():
            b.background_color = (0.15, 0.15, 0.22, 1)
            b.color = TEXT_SEC
        self._select_qual(btn.text)

    def _select_qual(self, key):
        btn = self.qual_btns.get(key)
        if btn:
            btn.background_color = PRIMARY_DARK
            btn.color = TEXT
            self.selected_fmt = btn.fmt

    def start_download(self, instance):
        if self.downloading:
            return
        url = self.url_input.text.strip()
        if not url:
            self._set_status('Вставь ссылку!', ERROR)
            return
        if not YTDLP_OK:
            self._set_status('yt-dlp не загружен!', ERROR)
            return

        self.downloading = True
        self.dl_btn.disabled = True
        self.dl_btn.background_color = PRIMARY_DARK
        self.dl_btn.text = 'ЗАГРУЗКА...'
        self.progress.value = 0
        self._set_status('Подключение...', WARN)

        t = threading.Thread(target=self._dl_thread, args=(url,), daemon=True)
        t.start()

    def _dl_thread(self, url):
        try:
            save_dir = get_save_dir()
            outtmpl = os.path.join(save_dir, '%(title)s.%(ext)s')

            ydl_opts = {
                'format': self.selected_fmt,
                'outtmpl': outtmpl,
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self._hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            basename = os.path.basename(filename)
            Clock.schedule_once(lambda dt: self._on_success(basename), 0)

        except Exception as e:
            err = traceback.format_exc()
            Clock.schedule_once(lambda dt: self._on_error(f'{str(e)}\n\n{err}'), 0)

    def _hook(self, d):
        if d['status'] == 'downloading':
            try:
                p = float(d.get('_percent_str', '0%').replace('%', '').strip())
                Clock.schedule_once(lambda dt, val=p: self._update(val), 0)
            except:
                pass
        elif d['status'] == 'finished':
            Clock.schedule_once(lambda dt: self._update(100), 0)

    def _update(self, val):
        self.progress.value = val
        self.status.text = f'Загрузка... {val:.0f}%'
        self.status.color = WARN

    def _on_success(self, name):
        self.downloading = False
        self.dl_btn.disabled = False
        self.dl_btn.background_color = PRIMARY
        self.dl_btn.text = 'СКАЧАТЬ'
        self.progress.value = 100
        self._set_status(f'Готово: {name}', SUCCESS)

    def _on_error(self, msg):
        self.downloading = False
        self.dl_btn.disabled = False
        self.dl_btn.background_color = PRIMARY
        self.dl_btn.text = 'СКАЧАТЬ'
        self.progress.value = 0
        # Показываем первую строку ошибки
        first_line = msg.split('\n')[0]
        self._set_status(f'Ошибка: {first_line[:80]}', ERROR)

    def _set_status(self, text, color):
        self.status.text = text
        self.status.color = color


if __name__ == '__main__':
    DownloaderApp().run()
