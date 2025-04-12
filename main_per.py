import tkinter as tk
from tkinter import ttk, scrolledtext
from work1 import Lexer, Token
from work2 import LR1Parser ,TokenType
import os


class CompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("词法分析与语法分析器")

        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 源代码输入区
        ttk.Label(main_frame, text="输入C/C++源代码:").grid(row=0, column=0, sticky=tk.W)
        self.source_code = scrolledtext.ScrolledText(main_frame, width=60, height=15)
        self.source_code.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))

        # 按钮区
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="词法分析", command=self.perform_lexical_analysis).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="语法分析", command=self.perform_syntax_analysis).grid(row=0, column=1, padx=5)

        # 结果显示区
        ttk.Label(main_frame, text="分析结果:").grid(row=3, column=0, sticky=tk.W)
        self.result_text = scrolledtext.ScrolledText(main_frame, width=60, height=15)
        self.result_text.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))

    def save_source_code(self):
        """保存源代码到临时文件"""
        with open('source.c', 'w', encoding='utf-8') as f:
            f.write(self.source_code.get('1.0', tk.END))

    def perform_lexical_analysis(self):
        """执行词法分析"""
        self.result_text.delete('1.0', tk.END)
        self.save_source_code()

        lexer = Lexer("grammar1.txt")
        tokens = lexer.tokenize_file("source.c")


        # 显示词法分析结果
        self.result_text.insert(tk.END, "词法分析结果：\n\n")
        for token in tokens:
            self.result_text.insert(tk.END, f"{str(token)}\n")

        # 保存词法分析结果
        with open("lexer_output.txt", "w", encoding="utf-8") as f:
            for token in tokens:
                f.write(f"({token.line}, {token.type}, '{token.value}')\n")

    def perform_syntax_analysis(self):
        """执行语法分析"""
        self.result_text.delete('1.0', tk.END)

        # 确保先进行词法分析
        if not os.path.exists('lexer_output.txt'):
            self.result_text.insert(tk.END, "请先进行词法分析！\n")
            return

        # 读取词法分析结果并解析tokens
        tokens = []
        try:
            with open('lexer_output.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            # 解析token字符串
                            tuple_str = line.strip()[1:-1]  # 移除括号
                            parts = [p.strip() for p in tuple_str.split(',', 2)]

                            # 创建token元组
                            line_no = int(parts[0])
                            token_type = TokenType[parts[1].split('.')[-1].strip()]
                            value = parts[2].strip(' "\'')

                            tokens.append((line_no, token_type, value))
                        except (ValueError, KeyError) as e:
                            self.result_text.insert(tk.END, f"解析token出错: {line.strip()}\n")
                            self.result_text.insert(tk.END, f"错误详情: {str(e)}\n")
                            continue

            # 创建并运行语法分析器
            parser = LR1Parser('grammar2.txt')

            success, errors = parser.parse(tokens)

            # 显示分析结果
            # self.result_text.insert(tk.END, "语法分析结果：\n\n")
            if success:
                self.result_text.insert(tk.END, "语法分析成功！\n")
                # 显示生成的分析表和状态
                try:
                    # with open('states.txt', 'r', encoding='utf-8') as f:
                    #     self.result_text.insert(tk.END, "\n状态集：\n" + f.read())
                    # with open('parsing_tables.txt', 'r', encoding='utf-8') as f:
                    #     self.result_text.insert(tk.END, "\n分析表：\n" + f.read())
                    with open('parsing_process.txt', 'r', encoding='utf-8') as f:
                        self.result_text.insert(tk.END, "\n语法处理分析过程：\n" + f.read())
                except FileNotFoundError:
                    pass
            else:
                self.result_text.insert(tk.END, "语法分析失败！\n")
                for error in errors:
                    self.result_text.insert(tk.END, f"{error}\n")

                # 保存错误信息到文件
                with open('syntax_errors.txt', 'w', encoding='utf-8') as f:
                    f.write("编译错误：\n\n")
                    for error in errors:
                        f.write(error + '\n')

        except FileNotFoundError:
            self.result_text.insert(tk.END, "找不到词法分析输出文件 lexer_output.txt\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"分析过程中出现错误：{str(e)}\n")



def main():
    root = tk.Tk()
    app = CompilerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()