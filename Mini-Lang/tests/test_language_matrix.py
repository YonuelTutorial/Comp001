import unittest

from minilang import Compiler


CASES = {
    "addition_int": ("print(1 + 2);", "3"),
    "subtraction_int": ("print(9 - 4);", "5"),
    "multiplication_int": ("print(6 * 7);", "42"),
    "division_int": ("print(9 / 2);", "4"),
    "modulo_int": ("print(17 % 5);", "2"),
    "power_int": ("print(2 ^ 10);", "1024"),
    "precedence": ("print(2 + 3 * 4 ^ 2);", "50"),
    "unary_negative": ("print(-8 + 3);", "-5"),
    "float_addition": ("print(1.5 + 2.25);", "3.75"),
    "float_division": ("print(5.0 / 2);", "2.5"),
    "numeric_promotion": ("float x = 2; print(x + 0.5);", "2.5"),
    "string_concat": ('print("Mini" + "Lang");', "MiniLang"),
    "string_equal": ('print("a" == "a");', "True"),
    "string_not_equal": ('print("a" != "b");', "True"),
    "boolean_and": ("print(true && false);", "False"),
    "boolean_or": ("print(false || true);", "True"),
    "boolean_not": ("print(!false);", "True"),
    "less_equal": ("print(2 <= 2);", "True"),
    "greater_equal": ("print(3 >= 4);", "False"),
    "plus_assign": ("int x=2; x+=3; print(x);", "5"),
    "minus_assign": ("int x=8; x-=3; print(x);", "5"),
    "star_assign": ("int x=4; x*=3; print(x);", "12"),
    "slash_assign": ("int x=9; x/=2; print(x);", "4"),
    "mod_assign": ("int x=9; x%=4; print(x);", "1"),
    "increment": ("int x=1; x++; print(x);", "2"),
    "decrement": ("int x=1; x--; print(x);", "0"),
    "if_true": ("if(true){print(1);}else{print(2);}", "1"),
    "else_branch": ("if(false){print(1);}else{print(2);}", "2"),
    "while_sum": ("int i=0; int s=0; while(i<4){s+=i;i++;} print(s);", "6"),
    "for_sum": ("int s=0; for(int i=1;i<=4;i++){s+=i;} print(s);", "10"),
    "break_loop": ("int i=0; while(true){i++;if(i==3){break;}} print(i);", "3"),
    "continue_loop": ("for(int i=0;i<3;i++){if(i==1){continue;}print(i);}", "0\n2"),
    "zero_parameters": ("int valor(){return 7;} print(valor());", "7"),
    "multiple_parameters": ("int suma(int a,int b){return a+b;} print(suma(2,5));", "7"),
    "recursion": ("int f(int n){if(n<=1){return 1;}return n*f(n-1);}print(f(5));", "120"),
    "mutual_recursion": ("bool p(int n){if(n==0){return true;}return q(n-1);}bool q(int n){if(n==0){return false;}return p(n-1);}print(p(8));", "True"),
    "int_array": ("int a[2];a[0]=3;a[1]=4;print(a[0]+a[1]);", "7"),
    "float_array": ("float a[2];a[0]=1.5;a[1]=2;print(a[0]+a[1]);", "3.5"),
    "string_array": ('string a[2];a[0]="a";a[1]="b";print(a[0]+a[1]);', "ab"),
    "length_builtin": ('print(length("abcd"));', "4"),
    "substring_builtin": ('print(substring("abcdef",2,3));', "cde"),
    "contains_builtin": ('print(contains("abcdef","cd"));', "True"),
    "regex_builtin": ('print(regexMatch("ABC-123","[A-Z]+-[0-9]+"));', "True"),
    "to_int_builtin": ('print(toInt("19")+1);', "20"),
    "to_float_builtin": ('print(toFloat("1.5")+1);', "2.5"),
    "to_string_builtin": ('print(toString(123)+"!");', "123!"),
    "late_initialization": ("int x;x=11;print(x);", "11"),
    "void_function": ('void f(){print("ok");return;}f();', "ok"),
    "forward_function": ("print(f(3));int f(int n){return n+1;}", "4"),
    "computed_array_index": ("int a[3];a[1+1]=9;print(a[2]);", "9"),
}


class LanguageMatrixTests(unittest.TestCase):
    pass


def make_test(source, expected):
    def test(self):
        self.assertEqual(Compiler(max_steps=1_000_000).compile_and_run(source).output, expected)
    return test


for case_name, (case_source, case_expected) in CASES.items():
    setattr(LanguageMatrixTests, f"test_{case_name}", make_test(case_source, case_expected))


if __name__ == "__main__":
    unittest.main()
