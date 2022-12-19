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
        def areInSameLine(obj1, obj2):
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
        decl_types = ["NAME", "VARIABLE", "INTTYPE", "FLOATTYPE", "STRINGTYPE", "TUPLE", "LIST", "DICT"]
        obj_types = ["NAME", "INT", "FLOAT", "STRING", "TUPLE", "LIST", "DICT"]
        conditions = ["IFSTATE", "ELIFSTATE", "ELSESTATE"]
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