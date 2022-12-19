from rply import Token


class SourcePos:
    def __init__(self, lineno):
        self.lineno = lineno


class Node:
    def __repr__(self):
        if self.type:
            return f"Node[{self.type.value}](l: {self.left}, op: {self.operator}, r: {self.right})"
        else:
            return f"Node(l: {self.left}, op: {self.operator}, r: {self.right})"

    def __init__(self, left, operator, right):
        self.left, self.operator, self.right = (left, operator, right)
        self.type = None
        self.source_pos = SourcePos((left or operator).source_pos.lineno)

    @property
    def isJustAToken(self):
        return not self.operator and not self.right and not self.type


class Array:
    def __init__(self, os, content, cs, type="array"):
        self.open_symbol, self.content, self.close_symbol = (os, list(content) if content else [], cs)
        self.type = type.lower()
        self.source_pos = SourcePos(os.source_pos.lineno)

    def add_content(self, obj):
        if obj is None:
            return False
        # Check if it's a function call with parameters.
        # if self.type == "param":
        #     if type(obj) is Node:
        #         if obj.operator.name in ["INC", "DEC"] or (obj.operator.name == "IS" and obj.type != None):
        #             return False
        #
        #     self.content.add(obj)
        #
        # # Check if it's a function parameter declaration.
        # elif self.type == "param2":
        #     if type(obj) is Node:
        #         if obj.operator.name in ["INC", "DEC"]:# or (obj.operator.name == "IS" and obj.type is None):
        #             return False
        #
        #     self.content.add(obj)
        # else:
        #     if type(obj) is Node and obj.operator.name in ["EQUAL", ]:
        #         return False
        self.content.append(obj)
        return True

    @property
    def isJustAToken(self):
        return False


def getTokenLineNum(token):
    return token.source_pos.lineno


def isNode(obj):
    return type(obj) is Node


def isJustAToken(obj):
    is_token = False
    if type(obj) is Token:
        is_token = True
    else:
        is_token = obj.isJustAToken
    return is_token


class Sintax:
    def __init__(self, source_file):
        self.context_keys = {
            "LPAR": "RPAR",
            "LBKT": "RBKT",
            "LBRC": "RBRC",
            "ACCESS": "NAME",
        }
        self.source_file = source_file

    def analyse(self, tokens):
        prev_token = None
        curr_line = tokens[0].source_pos.lineno
        error = False
        opened_par, opened_bkt, opened_brc = [], [], []

        for id, token in enumerate(tokens):
            if token.name in self.context_keys:
                if token.name == "ACCESS":
                    if id >= len(tokens) - 1 or not prev_token or prev_token.name != "NAME" or \
                            curr_line != token.source_pos.lineno:
                        self.sendErrorMsg(token)
                        error = True
                        break
                    else:
                        next_token = tokens[id + 1]
                        if next_token.name != "NAME" or next_token.source_pos.lineno != curr_line:
                            self.sendErrorMsg(token)
                            error = True
                            break
                else:
                    if token.name == "LPAR":
                        opened_par.append(token)
                    elif token.name == "LBKT":
                        opened_bkt.append(token)
                    elif token.name == "LBRC":
                        opened_brc.append(token)
            else:
                if token.name == "RPAR":
                    if len(opened_par):
                        opened_par.pop()
                    else:
                        self.sendErrorMsg(token, "Parenthesis was never opened.")
                        error = True
                        break

                elif token.name == "RBKT":
                    if len(opened_bkt):
                        opened_bkt.pop()
                    else:
                        self.sendErrorMsg(token, "Bracket was never opened.")
                        error = True
                        break
                elif token.name == "RBRC":
                    if len(opened_brc):
                        opened_brc.pop()
                    else:
                        self.sendErrorMsg(token, "Bracer was never opened.")
                        error = True
                        break

            prev_token = token
            curr_line = token.source_pos.lineno

        if opened_par:
            self.sendErrorMsg(opened_par[-1], "Parenthesis was never closed.")
            error = True
        elif opened_bkt:
            self.sendErrorMsg(opened_bkt[-1], "Bracket was never closed.")
            error = True
        elif opened_brc:
            self.sendErrorMsg(opened_brc[-1], "Bracer was never closed.")
            error = True
        return error

    def analyse(self, tokens):
        # PLUS, MINUS, MUL, DIV, EQUAL, GEQUAL, LEQUAL, GREATER, LOWER, SEPARATE, ABSTRACT
        contexts = []
        VAR_TYPES = ["int", "float", "str", "var"]
        TREAT_AS_NAME = ["NAME", "PRINT"]
        FORB_TOKENS = ["INC", "DEC", "RPAR", "RBKT", "RBRC", "IS", "NOT", "SCOPE", "NAME"]
        is_declaring_var = False
        last_node = None

        def getToken(token_index):
            try:
                return tokens[token_index]
            except IndexError:
                pass

        def get_ArrayContent(array, start_index):
            open_symbol = array.open_symbol.name
            # cur_token = tokens[start_index]

            if open_symbol == "LPAR":
                token_name = "Parenthesis"
                # while cur_token.name != "RPAR" and start_index < len(tokens):
                while not array.close_symbol and start_index < len(tokens):
                    node, start_index = get_nextNode(start_index)
                    if type(node) is Node:
                        if node.operator.name in ["INC", "DEC"]:
                            self.sendErrorMsg(node.operator)
                            exit()
                    elif type(node) is Token and node.name == "RPAR":
                        array.close_symbol = node
                    else:
                        array.add_content(node)

            elif open_symbol == "LBKT":
                token_name = "Bracket"
                while not array.close_symbol and start_index < len(tokens):
                    node, start_index = get_nextNode(start_index)
                    if type(node) is Node and node.operator in ["INC", "DEC", "IS"]:
                        self.sendErrorMsg(node.operator)
                        exit()
                    elif type(node) is Token and node.name == "RBKT":
                        array.close_symbol = node
                    else:
                        array.add_content(node)

            else:
                token_name = "Bracer"
                while not array.close_symbol and start_index < len(tokens):
                    node, start_index = get_nextNode(start_index)
                    if type(node) is Node and node.operator != "SCOPE":
                        self.sendErrorMsg(node.operator)
                        exit()
                    elif type(node) is Token and node.name == "RBRC":
                        array.close_symbol = node
                    else:
                        array.add_content(node)

            if not array.close_symbol:
                self.sendErrorMsg(array.open_symbol, f"{token_name} was never opened.")
                exit()
            return start_index + 1

        def get_nextNode(start_index: int = 0):
            if start_index > len(tokens) - 1:
                return None, start_index

            global last_node
            current_node = None
            skip_tks = 0
            id = 0
            for token in tokens[start_index:]:
                print("Token:", token)

                if token.value in ["+", "-", "*", "/", "=", "==", ">=", "<=", ">", "<"]:
                    if last_node:
                        last_node.operator = token
                        next_node, id = get_nextNode(id + 1)
                        last_node.right = next_node

                # VAR_TYPES: ["int", "float", "str", "var"]
                if token.value in VAR_TYPES or token.name in TREAT_AS_NAME:
                    current_node = Node(token, None, None)
                    next_token = getToken(id + 1)

                    # Check if next token is at the same line
                    if getTokenLineNum(next_token) == getTokenLineNum(current_node.left):

                        # Check for variable declaration
                        if next_token.name == "NAME":
                            current_node.type = current_node.left.value
                            current_node.left = next_token
                            next_token = getToken(id + 1)

                            if next_token.name == "Is":
                                current_node.operator = next_token
                                next_node, id = get_nextNode(id + 2)
                                if next_node is None or (isNode(next_node) and next_node.type):
                                    # self.sendErrorMsg(token, "variable declaration over another.")
                                    self.sendErrorMsg(next_token, 'wrong variable declaration.')
                                    exit()

                                if isJustAToken(next_token):
                                    current_node.right = next_node.left
                                else:
                                    current_node.right = next_node

                            elif next_token.name == "ABSTRACT":
                                current_node.operator = next_token
                            else:
                                # self.sendErrorMsg(token, "variable declaration over another.")
                                self.sendErrorMsg(next_token, 'wrong variable declaration.')
                                exit()

                        # Check for function call
                        elif next_token.name == "LPAR":
                            if token.name == "VARIABLE":
                                self.sendErrorMsg(next_token, f'"{token.value}" is not callable.')
                                exit()
                            parameters = Array(next_token, None, None)
                            contexts.append(parameters)
                            get_ArrayContent(parameters, id + 2)
                            contexts.remove(parameters)
                            current_node.operator = parameters

                        else:
                            if next_token.name == "LBRC" or next_token.name in FORB_TOKENS and tokens[
                                max(0, id - 1)].name == "IS":
                                self.sendErrorMsg(token)
                                exit()

                elif token.name in ["INT", "FLOAT", "STRING"]:
                    return token, id + 1

                # Open contexts
                elif token.name in ["LPAR", "LBKT", "LBRC"]:
                    current_node = Array(token, None, None)
                    contexts.append(current_node)
                    get_ArrayContent(current_node, id + 1)
                    contexts.remove(current_node)
                    # get_nextNode(id+1)

                # Close contexts
                elif token.name in ["RPAR", "RBKT", "RBRC"]:
                    close_context = None
                    for context in reversed(contexts):
                        if context.open_symbol.name == "L" + token.name[1:]:
                            close_context = context
                            break
                    if close_context:
                        return token, id + 1
                    else:
                        token_name = "Parenthesis" if token.name == "RPAR" else "Bracket" if token.name == "RBKT" else "Bracer"
                        self.sendErrorMsg(token, f"{token_name} was never opened.")
                        exit()

                id += 1

                if current_node:
                    break

            return current_node, id

        self.nodes = []
        while len(tokens):
            current_node, id = get_nextNode(0)
            self.nodes.append(current_node)
            # print(">>>>>>", id)
            tokens = tokens[id:]

        return None
        # for id, token in enumerate(tokens):
        #
        #     if token.value in ["int", "float", "str", "var"]:
        #         current_node = Node(token, None, None)
        #         if tkid+1 < qt_tokens:
        #             token = tokens[tkid+1]
        #
        #             if token.name == "NAME":
        #                 current_node.type = current_node.left
        #                 current_node.left = token
        #                 if tkid+2 < qt_tokens:
        #                     token = tokens[tkid+1]
        #             elif token.name == "LPAR":
        #                 parameters = Array(token, )
        #                 contexts.append(parameters)
        #             else:
        #                 self.sendErrorMsg(token)
        #
        #     # Close contexts
        #     if token.name in ["RPAR", "RBKT", "RBRC"]:
        #         context_closed = None
        #         for context in reversed(contexts):
        #             if context.open_symbol.name == "L"+token.name[1:]:
        #                 context.close_symbol = token
        #                 context_closed = context
        #                 break
        #
        #         if not context_closed:
        #             if token.name == "RPAR":
        #                 token_name = "Parenthesis"
        #             elif token.name == "RBKT":
        #                 token_name = "Bracket"
        #             else:
        #                 token_name = "Bracer"
        #             self.sendErrorMsg(token, f"{token_name} was never opened.")
        #             break
        #         continue
        #
        #     # If there is some opened context(tuple, list, dictionary, func params), add the current node to it
        #     if contexts and current_node:
        #         # if current_node.operator == "??":
        #         contexts[-1].content.append(current_node)
        #
        #     # if not current_node.left:
        #     #     if current_node.type:
        #     #
        #     #
        #     #     if token.value in ["int", "float", "str", "var"]:
        #     #         current_node.type = token.value

    def analyse(self, tokens):
        def areInSameLine(obj1, obj2):
            # def getLeftObj(obj):
            #     if isNode(obj):
            #         return getLeftObj(obj)
            #     return obj.left

            return obj1.source_pos.lineno == obj2.source_pos.lineno

        def getNextToken(cur_tkid):
            next_id = cur_tkid + 1
            return tokens[next_id] if next_id < len(tokens) else None
        def createNewLineNode(left, operator, right, type=None):
            if len(self.nodes):
                ln = self.nodes[-1]
                if isNode(ln.right):
                    if ln.right.right is None and ln.right.operator is None:
                        ln.right = ln.right.left
            new_node = Node(left, operator, right)
            new_node.type = type
            return new_node

        signs = ["PLUS", "MINUS", "NOT"]
        math_ops = ["INC", "DEC", "MUL", "DIV"]
        comp_ops = ["EQUAL", "GREATER", "LOWER", "GEQUAL", "LEQUAL"]
        open_cont = ["LPAR", "LBKT", "LBRC"]
        conditions = ["IFSTATE", "ELIFSTATE", "ELSESTATE"]
        decl_types = ["NAME", "VARIABLE", "INTTYPE", "FLOATTYPE", "STRINGTYPE", "TUPLE", "LIST", "DICT"]
        obj_types = ["NAME", "INT", "FLOAT", "STRING", "TUPLE", "LIST", "DICT"]
        apart = ["SEPARATE", "SCOPE", "ABSTRACT"]

        self.nodes = []
        last_node, last_token = None, None

        for id, token in enumerate(tokens):
            # Check + & - operator/sign
            if token.name in signs:
                if last_node:
                    if last_node.operator is None and token.name != "NOT":
                        last_node.operator = token
                    else:
                        last_node.right = Node(None, token, None)
                        last_node = last_node.right
                else:
                    last_node = Node(None, token, None)
                    self.nodes.append(last_node)

                # Check if next token is at the same line
                next_token = getNextToken(id)
                if not next_token or not areInSameLine(token, next_token) or (
                        token.name == "NOT" and next_token.name not in [*obj_types, *open_cont]):
                    self.sendErrorMsg(token, "")
                    exit()

            # Check other math operators
            elif token.name in math_ops:
                if token.name in ["INC", "DEC"]:
                    if last_node:
                        if last_node.operator is None:
                            last_node.operator = token
                        else:
                            self.sendErrorMsg(token, "")
                            exit()
                    else:
                        last_node = Node(None, token, None)
                        self.nodes.append(last_node)

                    # Check if next token is at the same line and is a valid token
                    next_token = getNextToken(id)
                    if not next_token or not areInSameLine(token, next_token) or next_token not in [*obj_types, *open_cont]:
                        self.sendErrorMsg(token, "")
                        exit()
                else:
                    # Check if there is a last token/node and if it's at the same line
                    if not last_node or not areInSameLine(last_node.left, token):
                        self.sendErrorMsg(token, "")
                        exit()

                    if last_node.operator is None:
                        if type(last_node.left) is Token:
                            last_node.left = Node(last_node.left, None, None)
                        last_node.operator = token

                    elif last_node.right != None:
                        last_node.right = Node(last_node.right, token, None)
                        last_node = last_node.right
                    else:
                        self.sendErrorMsg(token, "")
                        exit()

                    # Check if next token is at the same line
                    next_token = getNextToken(id)
                    if not next_token or not areInSameLine(token, next_token):
                        self.sendErrorMsg(token, "")
                        exit()

            elif token.name in open_cont:
                last_node = Node(Node(token, None, None), None, None)
                self.nodes.append(last_node)

            # Check other operators
            elif token.name in ["IS", "ACCESS", *comp_ops]:
                if token.name == "ACCESS":
                    # Assert that there is a last token/node, and it's not an operator, is at the same line, and it's a name token.
                    if not last_node or last_node.operator != None or not areInSameLine(last_node, token) or \
                            not (type(last_node.left) is Token and last_node.left.name == "NAME"):
                        self.sendErrorMsg(token, "")
                        exit()

                    last_node.operator = token

                    # Check if next token is at the same line, and it's a name token.
                    next_token = getNextToken(id)
                    if not next_token or not areInSameLine(token, next_token) or next_token.name != "NAME":
                        self.sendErrorMsg(token, "")
                        exit()
                else:
                    # Assert that there is a last token/node, and it's not an operator, is at the same line, and it's a name token.
                    if not last_node or last_node.operator != None or not areInSameLine(last_node, token) or \
                            (type(last_node.left) is Token and last_node.left.name != "NAME"):
                        self.sendErrorMsg(token, "")
                        exit()

                    last_node.operator = token
                    # Check if next token is at the same line.
                    next_token = getNextToken(id)
                    if not next_token or not areInSameLine(token, next_token):
                        self.sendErrorMsg(token, "")
                        exit()

            # Check for object type
            elif token.name in decl_types:
                if token.name == "VARIABLE":
                    # Check if there isn't a last token/node or if it's not at the same line
                    if not last_node or not areInSameLine(last_node.left, token):
                        last_node = createNewLineNode(token, None, None)
                        self.nodes.append(last_node)
                    else:
                        self.sendErrorMsg(token, "")
                        exit()

                elif last_node and last_node.right is None:
                    if last_node.operator != None:
                        last_node.right = Node(token, None, None)
                        last_node = last_node.right
                    else:
                        # Check if last token is at the same line and is a valid token
                        if areInSameLine(last_node.left, token):
                            if last_node.type is None and token.name == "NAME":
                                last_node.type = last_node.left
                                last_node.left = token
                            else:
                                self.sendErrorMsg(token, "")
                                exit()
                        else:
                            last_node = createNewLineNode(token, None, None)
                            self.nodes.append(last_node)
                else:
                    last_node = createNewLineNode(token, None, None)
                    self.nodes.append(last_node)

            # Check for object
            elif token.name in obj_types:
                if last_node and last_node.right is None:
                    if last_node.operator is None and last_node.type is None:
                        if not areInSameLine(last_node.left, token):
                            last_node = createNewLineNode(token, None, None)
                            self.nodes.append(last_node)
                        else:
                            self.sendErrorMsg(token, "")
                            exit()
                    else:
                        last_node.right = Node(token, None, None)
                        last_node = last_node.right
                else:
                    last_node = createNewLineNode(token, None, None)
                    self.nodes.append(last_node)

            # elif token.name in conditions:
            # if token.name == "ELSE":
            #     # Check if next token is SCOPE and if it's at the same line
            #     next_token = getNextToken(id)
            #     if next_token and token.name == "SCOPE" and areInSameLine(token, next_token):
            #         last_node = createNewLineNode(token, next_token, None)
            #         last_node.type = "ELSE"
            #     else:
            #         self.sendErrorMsg(token, "")
            #         exit()
            # else:
            #     last_node = createNewLineNode(Node|Array, "SCOPE", None)
            #     last_node.type = "IF"
            else:
                self.sendErrorMsg(token, "")
                exit()

            last_token = token

        # Take last_node.right's Token out of its Node parent if possible.
        if len(self.nodes):
            last_node = self.nodes[-1]
            if isNode(last_node.right):
                if last_node.right.right is None and last_node.right.operator is None:
                    last_node.right = last_node.right.left

        return self.nodes

    def sendErrorMsg(self, token, error_msg=""):
        line_id = token.source_pos.lineno
        col_id = token.source_pos.colno
        error_type = "invalid sintax."
        _error_msg = self.source_file.splitlines()[line_id - 1]

        if token.name in ("RPAR", "RBKT", "RBRC", "LPAR", "LBKT", "LBRC", "PLUS", "MINUS", "MUL", "DIV", "IS"):
            col_id += 1

        _error_msg += "\n" + " " * (col_id - 1) + "^"
        print(f"At line {line_id}, column {col_id}:")
        print(_error_msg + error_msg)
        print(f"SyntaxError: {error_type}")

    def showResult(self):
        print("Nodes:")
        for node in self.nodes:
            print(f"\t{node}")