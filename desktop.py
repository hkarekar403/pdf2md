import sys
import os
import threading
import base64
import webview
from app import app


class FileApi:
    def save_file(self, content_base64, suggested_name):
        try:
            content = base64.b64decode(content_base64)
            window = webview.active_window()
            result = window.create_file_dialog(
                dialog_type=webview.SAVE_DIALOG,
                save_filename=suggested_name,
                file_types=('Markdown files (*.md)', 'All files (*.*)'),
            )
            if result and isinstance(result, tuple) and len(result) > 0:
                path = result[0]
                with open(path, 'wb') as f:
                    f.write(content)
                return {"success": True, "path": path}
            return {"success": False, "error": "No file selected"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def start_flask():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    t = threading.Thread(target=start_flask, daemon=True)
    t.start()

    api = FileApi()
    window = webview.create_window(
        title="PDF to MD Converter",
        url="http://127.0.0.1:5000",
        width=1100,
        height=780,
        resizable=True,
        min_size=(900, 600),
        text_select=True,
        background_color="#f5f7fa",
        js_api=api,
        confirm_close=True,
    )
    webview.start()
