import re
import sys
from enum import Enum
from collections import defaultdict


class TokenType(Enum):
    KEYWORD = 1 # 关键字
    IDENTIFIER = 2 # 标识符
    CONSTANT = 3 # 常量
    DELIMITER = 4  # 分隔符
    OPERATOR = 5 # 运算符
    ERROR = -1 # 错误



class GrammarParser: # 语法解析器: 用于解析文法文件, 构建正则表达式
    def __init__(self, grammar_path):
        self.grammar = defaultdict(list)  # 默认值为list的字典，存储非终结符及其对应产生式
        self.keywords = set() # 关键字集合，用于快速判断是否为关键字
        self.regex_rules = [] # list保存正则表达式规则
        self.load_grammar(grammar_path) # 加载文法文件

    def load_grammar(self, path): # 调用该方法加载文法文件，填充self.grammar和self.keywords
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f: # 逐行读取文法文件
                    line = line.strip() # 去除首尾空白字符
                    if not line or line.startswith('#'): # 空行或注释行
                        continue
                    lhs, rhs = line.split('→', 1) # 以→为分隔符分割产生式
                    lhs = lhs.strip() # 去除首尾空白字符
                    rhs = [s.strip().strip("'") for s in rhs.split('|')] # 以|为分隔符分割右部产生式，去除首尾空白字符和单引号

                    if lhs == 'Keyword':
                        self.keywords.update(rhs) # 如果左边是KeyWord，更新关键字集合
                    else:
                        pattern = self.build_regex(rhs) # 构建正则表达式
                        self.regex_rules.append((lhs, re.compile(pattern))) # 编译正则表达式并添加到规则列表
        except FileNotFoundError:
            print(f"文法文件 {path} 未找到")
            sys.exit(1)

    def build_regex(self, expressions):
        regex_parts = []
        for expr in expressions:
            parts = []
            i = 0
            while i < len(expr):
                if expr[i] == '\\' and i + 1 < len(expr):  # 处理转义字符（如 \d）
                    parts.append(re.escape(expr[i + 1]))  # 转义为 \\d
                    i += 2
                else:
                    if expr[i] in ['+', '*', '?', '(', ')', '[', ']', '.']:
                        parts.append(f'\\{expr[i]}')  # 转义正则元字符
                    else:
                        parts.append(expr[i])
                    i += 1
            regex_parts.append(''.join(parts))
        return '^(' + '|'.join(regex_parts) + ')$'  # 拼接正则表达式


class Lexer:
    def __init__(self, grammar_path):
        self.grammar = GrammarParser(grammar_path) # 解析文法文件
        self.line = 1 # 行号
        self.pos = 0 # 位置指针
        self.tokens = []

        # 构建DFA状态表
        self.dfa_states = {
            'START': self.handle_start, # 初始状态
            'IDENTIFIER': self.handle_identifier, # 标识符状态
            'NUMBER': self.handle_number, # 数字状态
            'SCIENTIFIC': self.handle_scientific, # 科学计数法状态
            'COMPLEX': self.handle_complex,# 复数状态
            'STRING': self.handle_string, # 字符串状态
        }

    def tokenize_file(self, source_path): # 读取源代码文件，返回词法分析结果
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                source = f.read()
                return self.tokenize(source)
        except FileNotFoundError:
            print(f"源代码文件 {source_path} 未找到")
            return []

    def tokenize(self, code):
        self.current_state = 'START'
        self.buffer = []
        self.pos = 0
        self.current_input = code  # Store the input for reference

        while self.pos < len(code):
            char = code[self.pos]
            self.pos += 1

            if char == '\n':
                self.line += 1
            handler = self.dfa_states.get(self.current_state, self.handle_unknown)
            handler(char)

        if self.buffer:
            self.finalize_token()

        return self.tokens

    def handle_start(self, char):
        if char.isalpha() or char == '_': # 标识符首字符
            self.current_state = 'IDENTIFIER'
            self.buffer.append(char)
        elif char.isdigit(): # 数字首字符
            self.current_state = 'NUMBER'
            self.buffer.append(char)
        elif char == '"':  # 检测到引号，进入字符串状态
            self.current_state = 'STRING'
            self.buffer.append(char)
        elif char in {'+', '-', '*', '/', '=', '<', '>', '!', '&', '|'}: # 运算符
            self.add_operator(char)
        elif char in {';', ',', '(', ')', '{', '}', '[', ']'}: # 分隔符
            self.add_delimiter(char)
        elif char in {' ', '\t', '\r'}: # 空白字符
            pass  # 忽略空白字符
        # else:
        #     self.add_error(char)

    def handle_string(self, char):
        """处理字符串状态"""
        self.buffer.append(char)
        if char == '"' and self.buffer[-2] != '\\':  # 检测到未转义的引号
            self.finalize_token()
            self.current_state = 'START'
        elif char == '\n':  # 字符串中出现换行，视为错误
            self.add_error(''.join(self.buffer))
            self.buffer = []
            self.current_state = 'START'
    def handle_identifier(self, char):
        if char.isalnum() or char == '_':
            self.buffer.append(char)
        else:
            self.finalize_token()
            self.pos -= 1  # 回退字符
            self.current_state = 'START'


    def handle_number(self, char):
        buffer_str = ''.join(self.buffer)

        # 处理首位为0的情况
        if len(buffer_str) == 1 and buffer_str[0] == '0' and char.isdigit():
            # 把0和后续数字作为一个错误token处理
            self.buffer.append(char)
            while self.pos < len(self.current_input) and self.current_input[self.pos].isdigit():
                self.buffer.append(self.current_input[self.pos])
                self.pos += 1
            self.add_error(''.join(self.buffer))
            self.buffer = []
            self.current_state = 'START'
            return

        if char.isdigit():
            self.buffer.append(char)
        elif char == '.' and '.' not in buffer_str and 'e' not in buffer_str.lower():
            self.buffer.append(char)
        elif char.lower() == 'e' and 'e' not in buffer_str.lower():
            self.buffer.append(char)
            self.current_state = 'SCIENTIFIC'
        elif char in {'+', '-'}:
            if buffer_str[-1].lower() == 'e':
                self.buffer.append(char)
            else:
                # 可能是复数的开始
                self.buffer.append(char)
                self.current_state = 'COMPLEX'
        else:
            self.finalize_token()
            self.pos -= 1
            self.current_state = 'START'

    def handle_scientific(self, char):
        if char.isdigit() or char in {'+', '-'}:
            self.buffer.append(char)
        else:
            self.finalize_token()
            self.pos -= 1
            self.current_state = 'START'

    def handle_complex(self, char):
        buffer_str = ''.join(self.buffer)

        if char.isdigit():
            self.buffer.append(char)
        elif char == '.' and not any(c == '.' for c in buffer_str.split('+')[-1].split('-')[-1]):
            self.buffer.append(char)
        elif char == 'i' and len(buffer_str) > 1:
            self.buffer.append(char)
            self.finalize_token()
            self.current_state = 'START'
        else:
            # 如果不是复数的模式，回退并重新解析
            value = buffer_str[:-1]  # 移除最后的 + 或 -
            if value:
                self.buffer = list(value)
                self.finalize_token()
            self.pos -= 2  # 回退两个字符
            self.current_state = 'START'
            self.buffer = []

    def handle_unknown(self, char):
        self.add_error(char)
        self.current_state = 'START'
    def finalize_token(self):
        value = ''.join(self.buffer) # 合并字符缓冲区
        token_type = self.determine_token_type(value) # 确定token类型
        self.tokens.append(Token(self.line, token_type, value)) # 添加token
        self.buffer = [] # 清空缓冲区


    def determine_token_type(self, value):
        # 关键字检查
        if value in self.grammar.keywords:
            return TokenType.KEYWORD

        # 标识符检查
        if re.match(r'^[a-zA-Z_]\w*$', value):
            return TokenType.IDENTIFIER

        # 科学计数法检查
        scientific_pattern = r'^[+-]?(\d+\.\d+|\d+)[Ee][+-]?\d+$'
        if re.match(scientific_pattern, value):
            return TokenType.CONSTANT

        # 复数检查
        complex_pattern = r'^[+-]?(\d+\.\d+|\d+)[+-](\d+\.\d+|\d+)i$'
        if re.match(complex_pattern, value):
            return TokenType.CONSTANT

        # 整数检查
        if re.match(r'^([1-9]\d*|0)$', value):
            return TokenType.CONSTANT

        # 浮点数检查
        if re.match(r'^[+-]?\d+\.\d+$', value):
            return TokenType.CONSTANT

        # 字符串检查
        if re.match(r'^".*"$', value) or re.match(r"^'.*'$", value):
            return TokenType.CONSTANT

        return TokenType.ERROR

    def add_operator(self, char): # 添加运算符
        self.tokens.append(Token(self.line, TokenType.OPERATOR, char))

    def add_delimiter(self, char): # 添加分隔符
        self.tokens.append(Token(self.line, TokenType.DELIMITER, char))

    def add_error(self, char): # 添加错误
        self.tokens.append(Token(self.line, TokenType.ERROR, char))


class Token:
    def __init__(self, line, token_type, value):
        self.line = line # 行号
        self.type = token_type # token类型
        self.value = value # token值

    def __str__(self):
        return f"({self.line}, {self.type.name}, '{self.value}')"


if __name__ == "__main__":
    Author = "922106840528 卢梓佳"
    print(f"""词法分析程序  --- By {Author}""")


    LEXER = Lexer("grammar1.txt")  # 文法文件路径
    TOKENS = LEXER.tokenize_file("source.c")  # 源代码路径

    print("词法分析结果：")
    for token in TOKENS:
        print(token)

    # 保存到文件
    output_file = "lexer_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for token in TOKENS:
            f.write(f"({token.line}, {token.type}, '{token.value}')\n")
