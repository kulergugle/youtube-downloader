# -*- coding: utf-8 -*-
import os
import sys
import threading
import traceback

# Отключаем аргументы Kivy — иногда вызывают краш на Android
os.environ['KIVY_NO_ARGS'] = '1'
os.environ['KIVY_NO_CONSOLELOG'] = '1'

# ========== ИМПОРТЫ С ЗАЩИТОЙ ==========
KIVY_OK = False
YTDLP_OK = False
STARTUP_ERROR = ''
STARTUP_TRACEBACK = ''

try:
    from kivy.app import App
    from kivy.core.window import Window
    from kivy.clock import Clock
    from kivy.metrics import dp
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.progressbar import ProgressBar
    from kivy.uix.widget import Widget
    KIVY_OK = True
except Exception as e:
    STARTUP_ERROR = 'KIVY: ' + str(e)
    STARTUP_TRACEBACK = traceback.format_exc()

try:
    import yt_dlp
    YTDLP_OK = True
except Exception as e:
    if not STARTUP_ERROR:
        STARTUP_ERROR = 'YT-DLP: ' + str(e)
        STARTUP_TRACEBACK = traceback.format_exc()
    else:
        STARTUP_ERROR += ' | YT-DLP: ' + str(e)

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

# ========== ФУНКЦИИ ==========
def get_save_dir():
    if JNIUS_OK:
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


# ========== ПРИЛОЖЕНИЕ ==========
class DownloaderApp(App):
    def build(self):
        # Window можно трогать только тут!
        Window.clearcolor = (0.06, 0.06, 0.1, 1)

        if not KIVY_OK:
            return self._error_ui()

        self.downloading = False
        self.selected_fmt = '18'

        root = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(14))

        root.add_widget(Label(
            text='YouTube Downloader',
            font_size=dp(26),
            color=(0.95, 0.95, 0.97, 1),
            size_hint_y=None,
            height=dp(50)
        ))

        self.url_input = TextInput(
            hint_text='https://youtube.com/watch?v=...',
            multiline=False,
            font_size=dp(15),
            size_hint_y=None,
            height=dp(50),
            background_color=(0.08, 0.08, 0.14, 1),
            foreground_color=(0.95, 0.95, 0.97, 1),
            hint_text_color=(0.35, 0.35, 0.45, 1),
            padding=[dp(14), dp(15)]
        )
        root.add_widget(self.url_input)

        root.add_widget(Label(
            text='Качество:', font_size=dp(14), color=(0.55, 0.55, 0.65, 1),
            size_hint_y=None, height=dp(28)
        ))

        qual_grid = GridLayout(cols=3, spacing=dp(10), size_hint_y=None, height=dp(48))
        self.qual_btns = {}
        colors = {
            '360p': ('18', (0.15, 0.15, 0.22, 1), (0.55, 0.55, 0.65, 1)),
            '720p': ('22/18', (0.15, 0.15, 0.22, 1), (0.55, 0.55, 0.65, 1)),
            'Аудио': ('bestaudio/best', (0.15, 0.15, 0.22, 1), (0.55, 0.55, 0.65, 1)),
        }
        for label, (fmt, bg, fg) in colors.items():
            btn = Button(text=label, font_size=dp(14), background_color=bg, color=fg)
            btn.fmt = fmt
            btn.bind(on_press=self._on_qual)
            self.qual_btns[label] = btn
            qual_grid.add_widget(btn)
        self._select_qual('360p')
        root.add_widget(qual_grid)

        self.dl_btn = Button(
            text='СКАЧАТЬ', font_size=dp(18),
            size_hint_y=None, height=dp(54),
            background_color=(0.3, 0.55, 0.95, 1),
            color=(0.95, 0.95, 0.97, 1)
        )
        self.dl_btn.bind(on_press=self.start_download)
        root.add_widget(self.dl_btn)

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))
        root.add_widget(self.progress)

        self.status = Label(
            text='Готов', font_size=dp(14), color=(0.55, 0.55, 0.65, 1),
            size_hint_y=None, height=dp(36)
        )
        root.add_widget(self.status)

        if not YTDLP_OK:
            root.add_widget(Label(
                text='yt-dlp не загружен',
                font_size=dp(13), color=(0.9, 0.35, 0.35, 1),
                size_hint_y=None, height=dp(30)
            ))

        root.add_widget(Widget())
        return root

    def _error_ui(self):
        """Максимально простой UI для ошибки — никаких ScrollView, bold, halign"""
        box = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        box.add_widget(Label(
            text='ERROR',
            font_size=dp(20),
            color=(0.9, 0.35, 0.35, 1),
            size_hint_y=None,
            height=dp(40)
        ))
        box.add_widget(Label(
            text=STARTUP_ERROR,
            font_size=dp(14),
            color=(0.95, 0.95, 0.97, 1),
            size_hint_y=None,
            height=dp(60)
        ))
        box.add_widget(Label(
            text=STARTUP_TRACEBACK[:500],
            font_size=dp(11),
            color=(0.6, 0.6, 0.7, 1)
        ))
        return box

    def _on_qual(self, btn):
        for b in self.qual_btns.values():
            b.background_color = (0.15, 0.15, 0.22, 1)
            b.color = (0.55, 0.55, 0.65, 1)
        self._select_qual(btn.text)

    def _select_qual(self, key):
        btn = self.qual_btns.get(key)
        if btn:
            btn.background_color = (0.2, 0.4, 0.8, 1)
            btn.color = (0.95, 0.95, 0.97, 1)
            self.selected_fmt = btn.fmt

    def start_download(self, instance):
        if self.downloading:
            return
        url = self.url_input.text.strip()
        if not url:
            self._set_status('Вставь ссылку!', (0.9, 0.35, 0.35, 1))
            return
        if not YTDLP_OK:
            self._set_status('yt-dlp не загружен!', (0.9, 0.35, 0.35, 1))
            return

        self.downloading = True
        self.dl_btn.disabled = True
        self.dl_btn.background_color = (0.2, 0.4, 0.8, 1)
        self.dl_btn.text = 'ЗАГРУЗКА...'
        self.progress.value = 0
        self._set_status('Подключение...', (1, 0.7, 0.3, 1))

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
            first = str(e).split('\n')[0]
            Clock.schedule_once(lambda dt: self._on_error(first + ' | ' + err[:100]), 0)

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
        self.status.color = (1, 0.7, 0.3, 1)

    def _on_success(self, name):
        self.downloading = False
        self.dl_btn.disabled = False
        self.dl_btn.background_color = (0.3, 0.55, 0.95, 1)
        self.dl_btn.text = 'СКАЧАТЬ'
        self.progress.value = 100
        self._set_status(f'Готово: {name}', (0.3, 0.8, 0.5, 1))

    def _on_error(self, msg):
        self.downloading = False
        self.dl_btn.disabled = False
        self.dl_btn.background_color = (0.3, 0.55, 0.95, 1)
        self.dl_btn.text = 'СКАЧАТЬ'
        self.progress.value = 0
        self._set_status(f'Ошибка: {msg[:100]}', (0.9, 0.35, 0.35, 1))

    def _set_status(self, text, color):
        self.status.text = text
        self.status.color = color


if __name__ == '__main__':
    DownloaderApp().run()
