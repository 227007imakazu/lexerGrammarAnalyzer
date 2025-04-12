# C/C++ 词法及语法分析器

一个由Python实现，基于LR(1)文法的C/C++编译器，包含词法分析器、语法分析器和图形界面。

## 功能特点

- C/C++源代码词法分析
- LR(1)语法分析器
- 基于tkinter的图形界面
- 实时分析结果显示
- 错误处理与报告
- 支持复数字面量

## 项目结构

```
.
├── main_per.py     # GUI程序入口，不打包直接运行请用这个
├── main.py    		# 用于打包的main文件，仅在资源路径上与前者区分
├── work1.py        # 词法法分析器实现
├── work2.py        # LR(1)语法分析器实现
├── grammar1.txt    # 词法文法定义
├── grammar2.txt    # 语法文法定义
└── setup.py        # PyInstaller打包脚本
```

## 实现细节

### 词法分析器 (`work1.py`)

- 词法单元类型：关键字、标识符、常量、分隔符、运算符
- 基于DFA的扫描器实现
- 支持以下类型：
  - 数值字面量（整数、浮点数、科学计数法）
  - 复数
  - 字符串字面量 
  - 标识符和关键字
  - 运算符和分隔符

### 语法分析器 (`work2.py`)

- LR(1)分析算法实现
- 主要组件：
  - First集计算
  - LR(1)项目集闭包
  - 状态机构建
  - 分析表生成
  - 基于栈的语法分析驱动程序

### 图形界面 (`main_per.py`)

- 源代码输入区
- 分析控制按钮
- 结果显示区
- 基于文件的中间存储

## 使用方法

1. 运行程序：
```bash
python main_per.py
```

2. 在输入区输入C/C++源代码

3. 点击"词法分析"进行词法分析

4. 点击"语法分析"进行语法分析

## 生成可执xing文件

使用PyInstaller打包生成可执行文件：
```bash
python setup.py
```

> 可在setup.py对打包进行配置更改

## 输出文件

- `lexer_output.txt`: 词法分析结果
- `parsing_process.txt`: 语法分析过程
- `states.txt`: LR(1)状态集
- `parsing_tables.txt`: ACTION和GOTO表
- `syntax_errors.txt`: 语法错误报告

## 依赖项

- Python 3.8.5
- tkinter
- PyInstaller (用于打包)

## 错误处理

- 无效词法单元检测
- 语法错误报告（含行号）
- GUI中的详细错误信息

## 作者

[Imak](https://github.com/227007imakazu)

