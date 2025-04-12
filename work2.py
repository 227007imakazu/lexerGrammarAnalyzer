from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from enum import Enum
import sys
from typing import List, Set, Dict, Tuple, FrozenSet


# Token type definition from lexer
class TokenType(Enum):
    KEYWORD = 1
    IDENTIFIER = 2
    DELIMITER = 3
    OPERATOR = 4
    CONSTANT = 5
    ERROR = 6


@dataclass(frozen=True)
class Production:
    """Grammar production rule"""
    left: str
    right: tuple[str, ...]

    def __str__(self):
        return f"{self.left} → {' '.join(self.right)}"


@dataclass(frozen=True)
class LR1Item:
    """LR(1) item with dot position and lookahead"""
    production: Production
    dot_position: int
    lookahead: str

    def __str__(self):
        items = list(self.production.right)
        items.insert(self.dot_position, "•")
        return f"{self.production.left} → {' '.join(items)}, {self.lookahead}"

    def get_next_symbol(self) -> str | None:
        """Get the symbol after the dot"""
        if self.dot_position < len(self.production.right):
            return self.production.right[self.dot_position]
        return None

    def is_complete(self) -> bool:
        """Check if the item is complete (dot at end)"""
        return self.dot_position >= len(self.production.right)


class Grammar:
    """Grammar representation with terminals and non-terminals"""

    def __init__(self, grammar_file: str):
        self.productions: List[Production] = []
        self.terminals: Set[str] = set()
        self.non_terminals: Set[str] = set()
        self.start_symbol: str = None
        self._load_grammar(grammar_file)

    # def _load_grammar(self, filename: str):
    #     """Load grammar from file"""
    #     try:
    #         with open(filename, 'r', encoding='utf-8') as f:
    #             lines = [line.strip() for line in f if line.strip()]
    #
    #             for line in lines:
    #                 left, right = line.split('→')
    #                 left = left.strip()
    #                 self.non_terminals.add(left)
    #
    #                 if not self.start_symbol:
    #                     self.start_symbol = left
    #
    #                 # Split right side on spaces
    #                 symbols = []
    #                 parts = right.strip().split()
    #                 for part in parts:
    #                     if part == 'ε':
    #                         continue
    #                     # Keep quotes for terminals, add them for unquoted terminals
    #                     if (part.startswith("'") and part.endswith("'")) or (
    #                             part.startswith('"') and part.endswith('"')):
    #                         symbol = part
    #                         self.terminals.add(symbol)
    #                     else:
    #                         if part[0].isupper() or part in {'ID', 'CONSTANT'}:
    #                             symbol = part
    #                             self.non_terminals.add(symbol)
    #                         else:
    #                             # Add quotes for unquoted terminals
    #                             symbol = f"'{part}'"
    #                             self.terminals.add(symbol)
    #                     symbols.append(symbol)
    #
    #                 self.productions.append(Production(left, tuple(symbols)))
    #
    #     except FileNotFoundError:
    #         print(f"Error: Grammar file {filename} not found")
    #         sys.exit(1)
    def _load_grammar(self, filename: str):
        """Load grammar from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]

                for line in lines:
                    left, right = line.split('→')
                    left = left.strip()
                    self.non_terminals.add(left)

                    if not self.start_symbol:
                        self.start_symbol = left

                    # Split alternatives on |
                    alternatives = [alt.strip() for alt in right.split('|')]

                    for alternative in alternatives:
                        symbols = []
                        parts = alternative.strip().split()
                        for part in parts:
                            part = part.strip()
                            if part == 'ε':
                                continue
                            if part in {'ID', 'CONSTANT'}:  # Special tokens without quotes
                                symbol = part
                                self.terminals.add(symbol)
                            elif part.startswith("'") and part.endswith("'"):
                                symbol = part
                                self.terminals.add(symbol)
                            elif part[0].isupper():
                                symbol = part
                                self.non_terminals.add(symbol)
                            else:
                                symbol = f"'{part}'"
                                self.terminals.add(symbol)
                            symbols.append(symbol)

                        if symbols:  # Only add non-empty productions
                            self.productions.append(Production(left, tuple(symbols)))
                        else:  # Handle ε-productions
                            self.productions.append(Production(left, ()))

                print("\n语法加载完成：")
                print("终结符：", sorted(self.terminals))
                print("非终结符：", sorted(self.non_terminals))
                print("产生式：")
                for prod in self.productions:
                    print(f"  {prod}")

        except FileNotFoundError:
            print(f"错误：找不到语法文件 {filename}")
            sys.exit(1)


class LR1Parser:
    """LR(1) parser implementation"""

    def __init__(self, grammar_file: str):
        self.grammar = Grammar(grammar_file)
        self.first_sets = self._compute_first_sets()
        self.states, self.goto = self._build_states()
        self.action_table, self.goto_table = self._build_parsing_tables()

    def _compute_first_sets(self) -> Dict[str, Set[str]]:
        """Compute FIRST sets for all symbols"""
        first = {symbol: set() for symbol in
                 self.grammar.terminals | self.grammar.non_terminals}

        # Initialize terminals
        for terminal in self.grammar.terminals:
            first[terminal].add(terminal)

        changed = True
        while changed:
            changed = False
            for prod in self.grammar.productions:
                left = prod.left
                if not prod.right:  # ε-production
                    if 'ε' not in first[left]:
                        first[left].add('ε')
                        changed = True
                    continue

                for symbol in prod.right:
                    first_symbol = first[symbol]
                    prev_size = len(first[left])
                    first[left].update(x for x in first_symbol if x != 'ε')
                    if len(first[left]) > prev_size:
                        changed = True
                    if 'ε' not in first_symbol:
                        break
                else:
                    if 'ε' not in first[left]:
                        first[left].add('ε')
                        changed = True

        return first

    def _closure(self, items: Set[LR1Item]) -> FrozenSet[LR1Item]:
        """Compute closure of LR(1) items"""
        result = set(items)
        while True:
            new_items = set()
            for item in result:
                next_sym = item.get_next_symbol()
                if next_sym in self.grammar.non_terminals:
                    lookaheads = self._compute_lookaheads(item)
                    for prod in self.grammar.productions:
                        if prod.left == next_sym:
                            for la in lookaheads:
                                new_item = LR1Item(prod, 0, la)
                                if new_item not in result:
                                    new_items.add(new_item)
            if not new_items:
                break
            result.update(new_items)
        return frozenset(result)

    def _compute_lookaheads(self, item: LR1Item) -> Set[str]:
        """Compute lookahead symbols for an item"""
        if item.dot_position >= len(item.production.right) - 1:
            return {item.lookahead}

        beta = item.production.right[item.dot_position + 1:]
        first = set()
        for symbol in beta:
            first.update(self.first_sets[symbol])
            if 'ε' not in self.first_sets[symbol]:
                break
        else:
            first.add(item.lookahead)
        return first - {'ε'}

    def _goto(self, items: FrozenSet[LR1Item], symbol: str) -> FrozenSet[LR1Item]:
        """Compute GOTO for a set of items and a symbol"""
        next_items = set()
        for item in items:
            if (next_sym := item.get_next_symbol()) == symbol:
                next_items.add(LR1Item(
                    item.production,
                    item.dot_position + 1,
                    item.lookahead
                ))
        return self._closure(next_items)

    def _build_states(self) -> Tuple[List[FrozenSet[LR1Item]], Dict]:
        """Build LR(1) states and goto function"""
        states = []
        goto = {}

        # Create initial state with augmented grammar
        start_prod = [p for p in self.grammar.productions if p.left == self.grammar.start_symbol][0]
        initial_item = LR1Item(start_prod, 0, '$')
        initial_state = self._closure({initial_item})

        states.append(initial_state)
        state_map = {initial_state: 0}

        # Process states until no new states are found
        index = 0
        while index < len(states):
            state = states[index]

            # Get all symbols that appear after dots
            symbols = set()
            for item in state:
                if (symbol := item.get_next_symbol()):
                    symbols.add(symbol)

            # Sort symbols for deterministic processing
            for symbol in sorted(symbols):
                next_state = self._goto(state, symbol)
                if not next_state:
                    continue

                # Check if this state already exists
                if next_state in state_map:
                    goto[index, symbol] = state_map[next_state]
                else:
                    states.append(next_state)
                    state_map[next_state] = len(states) - 1
                    goto[index, symbol] = len(states) - 1

            index += 1

        print("\n状态集构建完成：")
        states_output = []
        for i, state in enumerate(states):
            states_output.append(f"\n状态 {i}:")
            for item in state:
                states_output.append(f"  {item}")

        states_content = "\n".join(states_output)
        save_to_file(states_content, 'states.txt')
        print(states_content)

        return states, goto

    def _build_parsing_tables(self) -> Tuple[Dict, Dict]:
        """Build ACTION and GOTO tables"""
        action = {}
        goto_table = {}

        print("\n开始构建语法分析表...")
        parsing_output = []
        for i, state in enumerate(self.states):
            parsing_output.append(f"\n状态 {i}:")

            # First handle shifts and gotos
            for symbol in self.grammar.terminals | self.grammar.non_terminals:
                if (i, symbol) in self.goto:
                    next_state = self.goto[i, symbol]
                    if symbol in self.grammar.terminals:
                        action[i, symbol] = ('shift', next_state)
                        parsing_output.append(f"  Adding shift action：({i}, {symbol}) -> 移进到状态 {next_state}")
                    else:
                        goto_table[i, symbol] = next_state
                        parsing_output.append(f"  Adding goto action：({i}, {symbol}) -> goto {next_state}")

            # Then handle reduces and accept
            for item in state:
                if item.is_complete():
                    if item.production.left == self.grammar.start_symbol:
                        action[i, '$'] = ('accept', None)
                        print(f"  Adding accept action: ({i}, $)")
                    else:
                        # Check for shift-reduce conflicts
                        if (i, item.lookahead) in action:
                            existing = action[i, item.lookahead]
                            if existing[0] == 'shift':
                                # Prefer shift over reduce (shift-reduce conflict resolution)
                                print(f"  Shift-reduce conflict at state {i} for {item.lookahead}")
                                print(f"    Existing: {existing}")
                                print(f"    New: reduce {item.production}")
                                print(f"    Choosing shift")
                                continue
                        action[i, item.lookahead] = ('reduce', item.production)
                        print(f"  Adding reduce action: ({i}, {item.lookahead}) -> reduce {item.production}")

        tables_output = ["ACTION："]
        for (state, symbol), (action_type, value) in sorted(action.items()):
            action_str = "接受" if action_type == "accept" else \
                f"移进到状态{value}" if action_type == "shift" else \
                    f"按{value}规约"
            tables_output.append(f"  ({state}, {symbol}) -> {action_str}")

        tables_output.append("\nGOTO表：")
        for (state, symbol), next_state in sorted(goto_table.items()):
            tables_output.append(f"  ({state}, {symbol}) -> {next_state}")

        save_to_file("\n".join(parsing_output), 'parsing_process.txt')
        save_to_file("\n".join(tables_output), 'parsing_tables.txt')

        return action, goto_table

    # def _build_parsing_tables(self) -> Tuple[Dict, Dict]:
    #     """Build ACTION and GOTO tables"""
    #     action = {}
    #     goto_table = {}
    #
    #     print("\nBuilding parsing tables...")
    #     for i, state in enumerate(self.states):
    #         print(f"\nState {i}:")
    #         for item in state:
    #             print(f"  {item}")
    #
    #             if item.is_complete():
    #                 # Reduce or accept
    #                 if item.production.left == self.grammar.start_symbol:
    #                     action[i, '$'] = ('accept', None)
    #                     print(f"    Adding accept action for $")
    #                 else:
    #                     action[i, item.lookahead] = ('reduce', item.production)
    #                     print(f"    Adding reduce action for {item.lookahead}")
    #             else:
    #                 # Shift action
    #                 next_sym = item.get_next_symbol()
    #                 if next_sym in self.grammar.terminals and (i, next_sym) in self.goto:
    #                     next_state = self.goto[i, next_sym]
    #                     action[i, next_sym] = ('shift', next_state)
    #                     print(f"    Adding shift action for {next_sym} to state {next_state}")
    #
    #         # Build goto table for non-terminals
    #         for symbol in self.grammar.non_terminals:
    #             if (i, symbol) in self.goto:
    #                 goto_table[i, symbol] = self.goto[i, symbol]
    #                 print(f"    Adding goto action for {symbol} to state {self.goto[i, symbol]}")
    #
    #     print("\nAction table:")
    #     for (state, symbol), (action_type, value) in action.items():
    #         print(f"  ({state}, {symbol}) -> ({action_type}, {value})")
    #
    #     return action, goto_table

    def parse(self, tokens: List[Tuple[int, TokenType, str]]) -> Tuple[bool, List[str]]:
        """Parse input tokens and return success status and errors"""
        stack = [(0, '$')]  # (state, symbol) pairs
        input_tokens = self._convert_tokens(tokens) + ['$']
        errors = []
        pos = 0

        print("\n开始语法分析...")
        print(f"输入 token: {input_tokens}")

        parse_steps = []
        while True:
            state = stack[-1][0]
            current_token = input_tokens[pos]

            parse_steps.append(f"\n当前状态：{state}")
            parse_steps.append(f"当前记号：{current_token}")
            parse_steps.append(f"栈内容：{stack}")
            parse_steps.append(f"剩余输入：{input_tokens[pos:]}")

            if (state, current_token) not in self.action_table:
                print(f"\nError: No action found for state {state} and token {current_token}")
                print("Available actions for state {state}:")
                for (s, t), (action_type, value) in self.action_table.items():
                    if s == state:
                        print(f"  Token: {t}, Action: ({action_type}, {value})")
                line_no = tokens[pos][0] if pos < len(tokens) else tokens[-1][0]
                errors.append(f"Line {line_no}: Syntax error, unexpected token '{current_token}'")
                return False, errors

            action, value = self.action_table[state, current_token]
            print(f"Action: {action}, Value: {value}")

            if action == 'shift':
                stack.append((value, current_token))
                pos += 1
            elif action == 'reduce':
                for _ in range(len(value.right)):
                    stack.pop()
                prev_state = stack[-1][0]
                goto_state = self.goto_table[prev_state, value.left]
                stack.append((goto_state, value.left))
                print(f"Reduced by {value}, goto state {goto_state}")
            elif action == 'accept':
                print("\nInput accepted!")
                return True, errors
            else:
                line_no = tokens[pos][0]
                errors.append(f"Line {line_no}: Invalid action in parser")
                return False, errors
            save_to_file("\n".join(parse_steps), 'parse_steps.txt')
    def _convert_tokens(self, tokens: List[Tuple[int, TokenType, str]]) -> List[str]:
        """Convert lexer tokens to parser symbols"""
        converted = []
        for _, type_, value in tokens:
            if type_ == TokenType.KEYWORD:
                converted.append(f"'{value}'")
            elif type_ == TokenType.IDENTIFIER:
                converted.append("ID")  # No quotes for special tokens
            elif type_ == TokenType.CONSTANT:
                converted.append("CONSTANT")  # No quotes for special tokens
            elif type_ == TokenType.DELIMITER:
                converted.append(f"'{value}'")
            elif type_ == TokenType.OPERATOR:
                converted.append(f"'{value}'")
            else:
                converted.append(f"'{value}'")
        return converted

def save_to_file(content: str, filename: str):
    """Save content to file with UTF-8 encoding"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
def main():
    # Load tokens from lexer output
    tokens = []
    try:
        with open('lexer_output.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    # Parse the tuple string safely
                    try:
                        tuple_str = line.strip()
                        # Remove parentheses
                        tuple_str = tuple_str[1:-1]
                        # Split on comma and strip
                        parts = [p.strip() for p in tuple_str.split(',', 2)]

                        line_no = int(parts[0])
                        token_type = TokenType[parts[1].split('.')[-1].strip()]
                        value = parts[2].strip(' "\'')

                        tokens.append((line_no, token_type, value))
                    except (ValueError, KeyError) as e:
                        print(f"Error parsing line: {line.strip()}")
                        print(f"Error details: {e}")
                        continue

    except FileNotFoundError:
        print("错误：找不到词法分析输出文件 lexer_output.txt")
        return

    # Create and run parser
    parser = LR1Parser('grammar2.txt')
    success, errors = parser.parse(tokens)

    # Output results
    print("语法分析结果:", "YES" if success else "NO")
    if errors:
        print("\n发现错误:")
        for error in errors:
            print(error)

        with open('syntax_errors.txt', 'w', encoding='utf-8') as f:
            f.write("编译错误:\n\n")
            for error in errors:
                f.write(error + '\n')



if __name__ == "__main__":
    main()