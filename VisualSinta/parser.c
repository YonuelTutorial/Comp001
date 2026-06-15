#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

char lookahead;

/* Declaraciones de Gramatica */
void E();
void E_prima();
void T();
void T_prima();
void F();
void match(char t);
void error();

/* Analizador Lexico Simulado */
void advance() {
    lookahead = getchar();
    while(lookahead == ' ' || lookahead == '\t' || lookahead == '\n') {
        lookahead = getchar();
    }
}

/* Reglas de Produccion */
void E() {
    T();
    E_prima();
}

void E_prima() {
    if (lookahead == '+') {
        match('+');
        T();
        E_prima();
    } else if (lookahead == '-') {
        match('-');
        T();
        E_prima();
    }
}

void T() {
    F();
    T_prima();
}

void T_prima() {
    if (lookahead == '*') {
        match('*');
        F();
        T_prima();
    } else if (lookahead == '/') {
        match('/');
        F();
        T_prima();
    }
}

void F() {
    if (lookahead == '(') {
        match('(');
        E();
        match(')');
    } else if (isalnum(lookahead)) {
        match(lookahead);
    } else {
        error();
    }
}

/* Validacion y Error */
void match(char t) {
    if (lookahead == t) {
        advance();
    } else {
        error();
    }
}

void error() {
    printf("Error sintactico detectado cerca de: '%c'\n", lookahead);
    exit(1);
}

/* Punto de Entrada */
int main() {
    printf("Ingrese la expresion (finalizada con .): ");
    advance();
    
    E();
    
    if (lookahead == '.') {
        printf("Cadena aceptada. Analisis sintactico exitoso.\n");
    } else {
        error();
    }
    
    return 0;
}