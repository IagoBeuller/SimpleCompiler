from lexer import Lexer
from syntax import Sintax
from semantic import Semantic
from operator import attrgetter

if __name__ == '__main__':
    test_type = 2  # 0: test lexer; 1: test syntax; 2: test semantic;
    lexer = Lexer()
    # file_code = open("test_lexer.mylang", "r").read()
    file_code = open("test_syntax.mylang", "r").read()
    tokens, error = lexer.tokenize(file_code)

    print("Resultado do lexer:")
    if error:
        print("Erros:")
        print(error)
    else:
        print("Erros:", 0)
        lexer.showResult()

    if tokens and test_type > 0:
        print("\nResultado da Análise Sintática:")
        syntax_analyser = Sintax(file_code)
        nodes = syntax_analyser.analyse(tokens)
        if nodes:
            print("Syntax Ok...")
            syntax_analyser.showResult()

            if test_type > 1:
                print("\nResultado da Análise Semântica:")
                semantic_analyser = Semantic(file_code)
                error = semantic_analyser.analyse(nodes)
                if not error:
                    print("Semantic Ok...")
                    # print("Global vars:\n", semantic_analyser.global_vars)
                    # print("\nObjects:", semantic_analyser.result)
                    semantic_analyser.showResult()