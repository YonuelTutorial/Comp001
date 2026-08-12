"use strict";

const __ml_not_declared = Symbol("no declarado");
const __ml_uninitialized = Symbol("sin inicializar");
const __ml_max_steps = 1000000;
const __ml_max_call_depth = 500;
let __ml_steps = 0;
let __ml_call_depth = 0;
let __ml_inputs = null;

function __ml_error(message, line, column) {
    const position = line > 0 ? ` [línea ${line}, columna ${column}]` : "";
    throw new Error(`Error de ejecución${position}: ${message}`);
}

function __ml_tick(line, column) {
    __ml_steps += 1;
    if (__ml_steps > __ml_max_steps) {
        __ml_error(`se superó el límite de ${__ml_max_steps} instrucciones; posible ciclo infinito`, line, column);
    }
}

function __ml_call(callback, line, column) {
    if (__ml_call_depth >= __ml_max_call_depth) {
        __ml_error(`se superó la profundidad máxima de ${__ml_max_call_depth} llamadas`, line, column);
    }
    __ml_call_depth += 1;
    try {
        return callback();
    } finally {
        __ml_call_depth -= 1;
    }
}

function __ml_format(value, type) {
    if (type === "bool") {
        return value ? "True" : "False";
    }
    if (type === "float") {
        if (Object.is(value, -0)) {
            return "-0.0";
        }
        if (Number.isInteger(value)) {
            return value.toFixed(1);
        }
    }
    return String(value);
}

function __ml_print(value, type) {
    console.log(__ml_format(value, type));
}

function __ml_load(name, value, line, column) {
    if (value === __ml_not_declared) {
        __ml_error(`'${name}' no está declarado`, line, column);
    }
    if (value === __ml_uninitialized) {
        __ml_error(`'${name}' se usó antes de inicializarse`, line, column);
    }
    return value;
}

function __ml_div(left, right, integer, line, column) {
    if (integer) {
        if (right === 0n) {
            __ml_error("división por cero", line, column);
        }
        let result = left / right;
        if (left % right !== 0n && (left < 0n) !== (right < 0n)) {
            result -= 1n;
        }
        return result;
    }
    if (right === 0) {
        __ml_error("división por cero", line, column);
    }
    return left / right;
}

function __ml_mod(left, right, line, column) {
    if (right === 0n) {
        __ml_error("módulo por cero", line, column);
    }
    let result = left % right;
    if (result !== 0n && (result < 0n) !== (right < 0n)) {
        result += right;
    }
    return result;
}

function __ml_pow(left, right, integer, line, column) {
    if (integer && right < 0n) {
        __ml_error("un exponente entero no puede ser negativo", line, column);
    }
    return left ** right;
}

function __ml_check_index(name, array, index, line, column) {
    if (typeof index !== "bigint" || index < 0n || index >= BigInt(array.length)) {
        __ml_error(`índice ${index} fuera de rango para '${name}' (tamaño ${array.length})`, line, column);
    }
    return Number(index);
}

function __ml_array_get(name, array, index, line, column) {
    const position = __ml_check_index(name, array, index, line, column);
    return array[position];
}

function __ml_array_set(name, array, index, value, line, column) {
    const position = __ml_check_index(name, array, index, line, column);
    array[position] = value;
    return value;
}

function __ml_read_input(name, line, column) {
    if (__ml_inputs === null) {
        if (typeof process !== "undefined" && process.versions && process.versions.node) {
            const data = require("fs").readFileSync(0, "utf8");
            __ml_inputs = data.length === 0 ? [] : data.split(/\r?\n/);
            if (__ml_inputs.length > 0 && __ml_inputs[__ml_inputs.length - 1] === "") {
                __ml_inputs.pop();
            }
        } else {
            __ml_inputs = [];
        }
    }
    if (__ml_inputs.length > 0) {
        return __ml_inputs.shift();
    }
    if (typeof prompt === "function") {
        const value = prompt(`${name}> `);
        if (value !== null) {
            return value;
        }
    }
    __ml_error(`faltan datos de entrada para ${name}`, line, column);
}

function __ml_input_int(line, column) {
    const value = __ml_read_input("inputInt", line, column).trim();
    if (!/^[+-]?\d+$/.test(value)) {
        __ml_error("inputInt: se esperaba un entero", line, column);
    }
    return BigInt(value);
}

function __ml_input_float(line, column) {
    const text = __ml_read_input("inputFloat", line, column).trim();
    const value = Number(text);
    if (text === "" || !Number.isFinite(value)) {
        __ml_error("inputFloat: se esperaba un decimal", line, column);
    }
    return value;
}

function __ml_input_string(line, column) {
    return __ml_read_input("inputString", line, column);
}

function __ml_input_bool(line, column) {
    const value = __ml_read_input("inputBool", line, column).trim().toLowerCase();
    if (value !== "true" && value !== "false") {
        __ml_error("inputBool: se esperaba true o false", line, column);
    }
    return value === "true";
}

function __ml_length(text) {
    return BigInt(Array.from(text).length);
}

function __ml_substring(text, start, count, line, column) {
    const chars = Array.from(text);
    if (typeof start !== "bigint" || typeof count !== "bigint" || start < 0n || count < 0n || start + count > BigInt(chars.length)) {
        __ml_error("substring: rango inválido para substring", line, column);
    }
    return chars.slice(Number(start), Number(start + count)).join("");
}

function __ml_to_string(value, type) {
    return __ml_format(value, type);
}

function __ml_to_int(value, line, column) {
    if (typeof value === "boolean") {
        return value ? 1n : 0n;
    }
    if (typeof value === "bigint") {
        return value;
    }
    if (typeof value === "number" && Number.isFinite(value)) {
        return BigInt(Math.trunc(value));
    }
    if (typeof value === "string" && /^[+-]?\d+$/.test(value.trim())) {
        return BigInt(value.trim());
    }
    __ml_error("toInt: conversión inválida", line, column);
}

function __ml_to_float(value, line, column) {
    if (typeof value === "boolean") {
        return value ? 1.0 : 0.0;
    }
    const text = typeof value === "string" ? value.trim() : value;
    const result = Number(text);
    if (text === "" || !Number.isFinite(result)) {
        __ml_error("toFloat: conversión inválida", line, column);
    }
    return result;
}

function __ml_contains(text, search) {
    return text.includes(search);
}

function __ml_regex_match(text, pattern, line, column) {
    try {
        return new RegExp(pattern).test(text);
    } catch (error) {
        __ml_error(`regexMatch: ${error.message}`, line, column);
    }
}

function __ml_run(main) {
    try {
        main();
    } catch (error) {
        if (typeof process !== "undefined" && process.versions && process.versions.node) {
            console.error(error.message);
            process.exitCode = 1;
            return;
        }
        throw error;
    }
}

__ml_run(() => {
    let __ml_v_6c69737461 = __ml_not_declared;
    
    __ml_tick(2, 5);
    __ml_v_6c69737461 = Array(5).fill(0n);
    __ml_tick(3, 1);
    __ml_array_set("lista", __ml_v_6c69737461, 0n, 8n, 3, 1);
    __ml_tick(4, 1);
    __ml_array_set("lista", __ml_v_6c69737461, 1n, 3n, 4, 1);
    __ml_tick(5, 1);
    __ml_array_set("lista", __ml_v_6c69737461, 2n, 5n, 5, 1);
    __ml_tick(6, 1);
    __ml_array_set("lista", __ml_v_6c69737461, 3n, 1n, 6, 1);
    __ml_tick(7, 1);
    __ml_array_set("lista", __ml_v_6c69737461, 4n, 9n, 7, 1);
    __ml_tick(9, 1);
    for (let __ml_v_69 = 0n; (__ml_load("i", __ml_v_69, 9, 17) < 5n); __ml_v_69 = (__ml_load("i", __ml_v_69, 9, 24) + 1n)) {
        __ml_tick(9, 1);
        __ml_tick(10, 5);
        for (let __ml_v_6a = 0n; (__ml_load("j", __ml_v_6a, 10, 21) < (4n - __ml_load("i", __ml_v_69, 10, 29))); __ml_v_6a = (__ml_load("j", __ml_v_6a, 10, 32) + 1n)) {
            __ml_tick(10, 5);
            __ml_tick(11, 9);
            if ((__ml_array_get("lista", __ml_v_6c69737461, __ml_load("j", __ml_v_6a, 11, 19), 11, 13) > __ml_array_get("lista", __ml_v_6c69737461, (__ml_load("j", __ml_v_6a, 11, 30) + 1n), 11, 24))) {
                __ml_tick(12, 17);
                let __ml_v_74656d70 = __ml_array_get("lista", __ml_v_6c69737461, __ml_load("j", __ml_v_6a, 12, 30), 12, 24);
                __ml_tick(13, 13);
                __ml_array_set("lista", __ml_v_6c69737461, __ml_load("j", __ml_v_6a, 13, 19), __ml_array_get("lista", __ml_v_6c69737461, (__ml_load("j", __ml_v_6a, 13, 30) + 1n), 13, 24), 13, 13);
                __ml_tick(14, 13);
                __ml_array_set("lista", __ml_v_6c69737461, (__ml_load("j", __ml_v_6a, 14, 19) + 1n), __ml_load("temp", __ml_v_74656d70, 14, 28), 14, 13);
            }
        }
    }
    __ml_tick(19, 1);
    __ml_print("Lista ordenada:", "string");
    __ml_tick(20, 1);
    for (let __ml_v_69 = 0n; (__ml_load("i", __ml_v_69, 20, 17) < 5n); __ml_v_69 = (__ml_load("i", __ml_v_69, 20, 24) + 1n)) {
        __ml_tick(20, 1);
        __ml_tick(21, 5);
        __ml_print(__ml_array_get("lista", __ml_v_6c69737461, __ml_load("i", __ml_v_69, 21, 17), 21, 11), "int");
    }
});