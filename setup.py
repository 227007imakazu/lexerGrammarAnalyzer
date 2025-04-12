import PyInstaller.__main__
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'main.py',  # 主程序文件
    '--name=LexSyntaxAnalyzer',  # 可执行文件名
    '--windowed',  # 使用 GUI 模式
    '--onefile',  # 打包成单个文件
    f'--add-data={os.path.join(current_dir, "grammar1.txt")};.',  # 添加文法文件
    f'--add-data={os.path.join(current_dir, "grammar2.txt")};.',
    # '--icon=icon.ico',  # 如果有图标的话
    '--clean',  # 清理临时文件
    '--noconfirm'  # 不询问确认
])