from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
import threading
import os
import yt_dlp

Window.clearcolor = (0.06, 0.05, 0.16, 1)

class DownloaderApp(App):
    def build(self):
        self.downloading = False
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        layout.add_widget(Label(text="📥 YouTube Downloader", font_size=dp(22), bold=True, size_hint_y=None, height=dp(50)))
        layout.add_widget(Label(text="Вставь ссылку и скачивай", font_size=dp(14), size_hint_y=None, height=dp(30)))
        
        self.url_input = TextInput(hint_text="🔗 Вставь ссылку...", multiline=False, font_size=dp(16), size_hint_y=None, height=dp(55), background_color=(0.1, 0.1, 0.2, 1), foreground_color=(1, 1, 1, 1))
        layout.add_widget(self.url_input)
        
        self.quality_spinner = Spinner(text="1080p (Full HD)", values=["4K (2160p)", "1080p (Full HD)", "720p (HD)", "480p", "Только аудио (MP3)"], font_size=dp(15), size_hint_y=None, height=dp(50), background_color=(0.1, 0.1, 0.2, 1))
        layout.add_widget(self.quality_spinner)
        
        playlist_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        self.playlist_check = CheckBox(active=False)
        playlist_box.add_widget(self.playlist_check)
        playlist_box.add_widget(Label(text="📋 Скачать плейлист", font_size=dp(14)))
        layout.add_widget(playlist_box)
        
        self.download_btn = Button(text="⬇ СКАЧАТЬ", font_size=dp(18), bold=True, size_hint_y=None, height=dp(60), background_color=(0.42, 0.39, 1, 1))
        self.download_btn.bind(on_press=self.start_download)
        layout.add_widget(self.download_btn)
        
        self.progress = ProgressBar(max=100, size_hint_y=None, height=dp(20))
        layout.add_widget(self.progress)
        
        self.status = Label(text="⏳ Ожидание...", font_size=dp(14), size_hint_y=None, height=dp(40))
        layout.add_widget(self.status)
        
        return layout
    
    def start_download(self, instance):
        if self.downloading:
            return
        url = self.url_input.text.strip()
        if not url:
            self.status.text = "❌ Вставь ссылку!"
            return
        
        quality_map = {
            "4K (2160p)": "bestvideo[height<=2160]+bestaudio/best",
            "1080p (Full HD)": "bestvideo[height<=1080]+bestaudio/best",
            "720p (HD)": "bestvideo[height<=720]+bestaudio/best",
            "480p": "bestvideo[height<=480]+bestaudio/best",
            "Только аудио (MP3)": "bestaudio/best",
        }
        
        self.downloading = True
        self.download_btn.disabled = True
        self.download_btn.text = "⏳ СКАЧИВАНИЕ..."
        self.status.text = "⏳ Начинаем..."
        
        thread = threading.Thread(target=self._download, args=(url, quality_map[self.quality_spinner.text], self.playlist_check.active), daemon=True)
        thread.start()
    
    def _download(self, url, format_str, is_playlist):
        try:
            os.makedirs("/storage/emulated/0/Download/YouTube", exist_ok=True)
            ydl_opts = {
                "outtmpl": "/storage/emulated/0/Download/YouTube/%(title)s.%(ext)s",
                "format": format_str,
                "merge_output_format": "mp4",
                "noplaylist": not is_playlist,
                "quiet": True,
                "progress_hooks": [self._hook],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            Clock.schedule_once(lambda dt: self._done("✅ Готово!"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._done(f"❌ Ошибка: {str(e)[:100]}"))
    
    def _hook(self, d):
        if d["status"] == "downloading":
            percent = float(d.get("_percent_str", "0%").replace("%", ""))
            Clock.schedule_once(lambda dt, p=percent: self._update(p))
    
    def _update(self, percent):
        self.progress.value = percent
        self.status.text = f"📥 {percent:.1f}%"
    
    def _done(self, text):
        self.downloading = False
        self.download_btn.disabled = False
        self.download_btn.text = "⬇ СКАЧАТЬ"
        self.status.text = text

if __name__ == "__main__":
    DownloaderApp().run()
