%{
#include <stdio.h>
%}
%option noyywrap

DIGITO      [0-9]
LETRA       [a-zA-Z]
ID          {LETRA}({LETRA}|{DIGITO})*
NUMERO      {DIGITO}+

%%
"if"|"else"|"while"|"int"|"return"  { printf("KEYWORD: %s\n", yytext); }
{ID}                                { printf("IDENTIFIER: %s\n", yytext); }
{NUMERO}                            { printf("NUMBER: %s\n", yytext); }
"+"|"-"|"*"|"/"|"="                 { printf("OPERATOR: %s\n", yytext); }
"{"|"}"|"("|")"|";"                 { printf("SYMBOL: %s\n", yytext); }
[ \t\n\r]+                          { }
.                                   { printf("UNKNOWN: %s\n", yytext); }
%%

int main(int argc, char **argv) {
    yylex();
    return 0;
}