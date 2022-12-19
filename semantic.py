from lexer import Token
from syntax import isNode

class Base:
    __semantic_analyser__ = None
    __attrs__ = {}
    type = "unknown"
    token = None
    def getLastTokenError(self, other_token):
        token = self.token
        if other_token and other_token.source_pos.idx > token.source_pos.idx:
            return other_token
        return token
    def type_cast(self, type):
        self.__semantic_analyser__.sendErrorMsg(self.token, f"TypeError: could not convert value '{self.value}' of type '{self.type}' to type '{type}'")
        exit()
    def sum(self, to):
        token = self.getLastTokenError(to.token)
        self.__semantic_analyser__.sendErrorMsg(token, f"TypeError: unsupported operand type(s) for +: '{self.type}' and '{to.type}'")
        exit()

    def sub(self, to):
        token = self.getLastTokenError(to.token)
        self.__semantic_analyser__.sendErrorMsg(token or self.token, f"TypeError: unsupported operand type(s) for -: '{self.type}' and '{to.type}'")
        exit()

    def mul(self, to):
        token = self.getLastTokenError(to.token)
        self.__semantic_analyser__.sendErrorMsg(token or self.token, f"TypeError: unsupported operand type(s) for *: '{self.type}' and '{to.type}'")
        exit()

    def div(self, to):
        token = self.getLastTokenError(to.token)
        self.__semantic_analyser__.sendErrorMsg(token or self.token, f"TypeError: unsupported operand type(s) for /: '{self.type}' and '{to.type}'")
        exit()

class Number(Base):
    def __repr__(self):
        return f"Number({self.value})"
    def __init__(self, token, type="int"):
        self.type = type
        if isinstance(token, Token):
            self.value = (int if type == "int" else float)(token.value)
            self.token = token
        else:
            self.value = token
            self.type = "int" if isinstance(self.value, int) is int else "float"
            self.token = None

    def type_cast(self, type):
        if type == "int":
            self.value = int(self.value)
            self.type = "int"
        elif type == "float":
            self.value = float(self.value)
            self.type = "float"
        else:
            super().type_cast(type)

    def sum(self, to):
        if type(to) == Object:
            to = to.value
        if type(to) == Number:
            r = Number(self.value + to.value)
            r.type = "float" if "float" in [self.type, to.type] else "int"
            r.token = self.token
            return r
        super().sum(to)

    def sub(self, to):
        if type(to) == Object:
            to = to.value
        if type(to) == Number:
            r = Number(self.value - to.value)
            r.type = "float" if "float" in [self.type, to.type] else "int"
            r.token = self.token
            return r
        super().sub(to)

    def mul(self, to):
        if type(to) == Object:
            to = to.value
        if type(to) == Number:
            r = Number(self.value * to.value)
            r.type = "float" if "float" in [self.type, to.type] else "int"
            r.token = self.token
            return r
        super().mul(to)

    def div(self, to):
        if type(to) == Object:
            to = to.value
        if type(to) == Number:
            r = Number(self.value / to.value)
            r.type = "float" if "float" in [self.type, to.type] else "int"
            r.token = self.token
            return r
        super().div(to)

class String(Base):
    def __repr__(self):
        return f'String("{self.value}")'
    def __init__(self, value):
        self.type = "str"
        if type(value) is Token:
            self.value = value.value[1:-1]
            self.token = value
        elif type(value) == Object:
            self.value = value.value
            self.token = value.token
        else:
            self.value = value
            self.token = None

    def _sum(self, to):
        """ Concatenate without check types to get performance """
        return String(self.value + to)
    def sum(self, to):
        if type(to) == Object:
            to = to.value
        if type(to) == String:
            r = self._sum(to.value)
            r.token = self.token
            return r
        super().sum(to)
    def mul(self, to):
        if type(to) == Object:
            to = to.value
        if type(to) == Number:
            new_string = String("")
            for i in range(0, to.value):
                new_string = new_string._sum(self.value)

            new_string.token = self.token
            return new_string
        super().mul(to)

class List(Base):
    def __repr__(self):
        return f"List({self.value})"
    def __init__(self, value):
        self.type = "list"
        self.content = value

    def _sum(self, to):
        """ Concatenate without check types to get performance """
        return List([*self.value, *to])
    def sum(self, to):
        if type(to) == Object:
            to = to.value
        if type(to) in (List, Tuple):
            r = self._sum(to.value)
            r.token = self.token
            return r
        super().sum(to)
    def mul(self, to):
        if type(to) == Object:
            to = to.value
        if type(to) == Number:
            new_list = List([])
            for i in range(0, to.value):
                new_list = new_list._sum(self.value)

            new_list.token = self.token
            return new_list
        super().mul(to)

class Tuple(Base):
    def __repr__(self):
        return f"Tuple({self.value})"
    def __init__(self, value):
        self.type = "tuple"
        self.value = value

    def _sum(self, to):
        """ Sum without check types to get performance """
        return Tuple([*self.value, *to])
    def sum(self, to):
        if type(to) == Object:
            to = to.value
        if type(to) in (Tuple, List):
            r = self._sum(to.value)
            r.token = self.token
            return r
        super().sum(to)
    def mul(self, to):
        if type(to) == Object:
            to = to.value
        if type(to) == Number:
            new_tuple = Tuple([])
            for i in range(0, to.value):
                new_tuple = new_tuple._sum(self.value)

            new_tuple.token = self.token
            return new_tuple
        super().mul(to)

class Null(Base):
    def __repr__(self):
        return f"Null"
    value = None
    type = "null"

class Object(Base):
    def __repr__(self):
        if self.type in ["unknown", "var"]:
            return f"Object(name: {self.name}, value: {self.value})"
        else:
            return f"Object[{self.type}](name: {self.name}, value: {self.value})"
    def __init__(self, token, value=None):
        self.type = "unknown"
        self.name = token.value
        self.value = value
        self.token = token

    def sum(self, to):
        return self.value.sum(to)
        #super().sum(to)

    def sub(self, to):
        return self.value.sub(to)
        #super().sub(to)

    def mul(self, to):
        return self.value.mul(to)
        #super().mul(to)

    def div(self, to):
        return self.value.div(to)
        #super().div(to)

class Semantic:
    def __init__(self, source_file):
        Base.__semantic_analyser__ = self
        self.source_file = source_file

    def visit(self, node):
        # print("Node:", node)
        # Convert Token to Object
        if type(node) is Token:
            if node.name == "STRING":
                return String(node)
            elif node.name in ("INT", "FLOAT"):
                return Number(node, type=node.name.lower())
            elif node.name == "NAME":
                return Object(node)
            else:
                return Null()
        elif node is None:
            return Null()

        # Get the objects for the left and operator part of the node
        left = self.visit(node.left)
        operator = node.operator
        if type(left) is Object:
            node_type = node.type.value if node.type else None
            # Check if object is already declared
            if left.name in self.global_vars:
                if operator and operator.name == "IS":
                    if node_type:
                        if node_type == "var":
                            self.global_vars[left.name][1] = "unknown"
                        else:
                            self.sendErrorMsg(left.token, "variable already declared.")
                            exit()

                    left.type = self.global_vars[left.name][1]
                else:
                    token = left.token
                    left = self.global_vars[left.name][0]
                    left.token = token
            else:
                if node_type and node_type != "var":
                    left.type = node_type
                    self.global_vars[left.name] = [left, left.type]
                elif operator and operator.name == "IS":
                    self.global_vars[left.name] = [left, "unknown"]
                else:
                    self.sendErrorMsg(left.token, f"name '{left.name}' is not defined.")
                    exit()

        if operator:
            if operator.name == "PLUS":
                right = self.visit(node.right)
                return left.sum(right) if type(left) != Null else right
            elif operator.name == "MINUS":
                right = self.visit(node.right)
                if node.left is None:
                    right.value = -right.value
                    return right
                return left.sub(right)
            elif operator.name == "MUL":
                right = self.visit(node.right)
                return left.mul(right)
            elif operator.name == "DIV":
                if isNode(node.right.left):
                    right = self.visit(node.right.left)
                    left = left.div(right)
                    operator = node.right.operator
                    if node.right.operator:
                        right = self.visit(node.right.right)
                        if operator.name == "PLUS":
                            left = left.sum(right)
                        elif operator.name == "MINUS":
                            left = left.sub(right)
                        elif operator.name == "MUL":
                            left = left.mul(right)
                        elif operator.name == "DIV":
                            if type(right) is Number and right.value == 0:
                                self.sendErrorMsg(right.token, "cannot divide a number by zero.")
                                exit()
                            left = left.div(right)
                        elif operator.name == "IS":
                            self.sendErrorMsg(operator, "")
                            exit()
                else:
                    right = self.visit(node.right)
                    if type(right) is Number and right.value == 0:
                        self.sendErrorMsg(right.token, "cannot divide a number by zero.")
                        exit()
                    left = left.div(right)
                return left
            elif operator.name == "IS":
                if type(left) is Object:
                    right = self.visit(node.right)
                    declared_obj_value, declared_obj_type = self.global_vars[left.name]
                    if declared_obj_type == "unknown" or declared_obj_type == right.type:
                        left.type = right.type
                        left.value = right
                        self.global_vars[left.name] = [left, declared_obj_type]

                    # Allow variables of type int/float to assign to int/float by type casting.
                    elif declared_obj_type in ["int", "float"] and right.type in ["int", "float"]:
                        left.type = right.type
                        left.value = right
                        self.global_vars[left.name] = [left, declared_obj_type]
                    else:
                        self.sendErrorMsg(right.token, f"Cannot assign the value '{right.value}' of type '{right.type}' to a variable of type '{left.type}'.")
                        exit()
                else:
                    print(f"A problem ocurred in semantic: wrong left object[{left}] type for operator: ", operator.value)
            elif operator.name == "ACCESS":
                # Is case of method call, get its name
                if isNode(node.right):
                    name_token = node.right.left
                else:
                    name_token = node.right

                if name_token.name == "NAME":
                    right = Null()
                    # token = node.right.left
                    # if token.value in left.__attrs__:
                    #     right = left.__attrs__[token.value]
                    # else:
                    #     self.sendErrorMsg(token, f"object '{left.name}' has no attribute named '{token.value}'.")
                    #     exit()
                else:
                    self.sendErrorMsg(operator, "")
                    exit()
                return right
        return left

    def sendErrorMsg(self, token, error_msg=""):
        line_id = token.source_pos.lineno
        col_id = token.source_pos.colno
        error_type = "invalid type on attribution."
        _error_msg = self.source_file.splitlines()[line_id-1]

        if token.name in ("RPAR", "RBKT", "RBRC", "LPAR", "LBKT", "LBRC", "PLUS", "MINUS", "MUL", "DIV", "IS"):
            col_id += 1

        _error_msg += "\n" + " " * (col_id - 1) + "^ "
        print(f"At line {line_id}, column {col_id}:")
        print(_error_msg + error_msg)
        print(f"SemanticError: {error_type}")

    def analyse(self, nodes):
        # Format: {var_name: [value, type]}
        self.global_vars = {}

        self.result = "Objects:"
        for node in nodes:
            obj = self.visit(node)
            self.result += "\n\t" + str(obj)
        return False

    def showResult(self):
        # Show Global Variables
        print("Global vars:\n{")
        # Get the max char globlal vars names have for align the result.
        max_chars_len = max([len(g) for g in self.global_vars])

        for g in self.global_vars:
            spaces = " " * (max_chars_len - len(g))
            print(f"\t{g+spaces}: {self.global_vars[g]}")
        print("}")

        # Show generated objects
        print(self.result)