package lang

import (
	"fmt"
	"math"
)

type EvalError struct {
	Msg string
}

func (e *EvalError) Error() string {
	return e.Msg
}

func Eval(node Node, env *Environment) (Object, error) {
	switch n := node.(type) {
	case *Program:
		return evalProgram(n, env)
	case *StmtExpr:
		return Eval(n.Expr, env)
	case *AssignStmt:
		return evalAssign(n, env)
	case *IfStmt:
		return evalIf(n, env)
	case *ForStmt:
		return evalFor(n, env)
	case *WhileStmt:
		return evalWhile(n, env)
	case *FunctionDef:
		return evalFunctionDef(n, env)
	case *CallExpr:
		return evalCall(n, env)
	case *IndexExpr:
		return evalIndex(n, env)
	case *InfixExpr:
		return evalInfix(n, env)
	case *PrefixExpr:
		return evalPrefix(n, env)
	case *Ident:
		return evalIdent(n, env)
	case *NumberLiteral:
		return Object{Type: NUMBER_OBJ, Number: n.Value}, nil
	case *StringLiteral:
		return Object{Type: STRING_OBJ, Value: n.Value}, nil
	case *BoolLiteral:
		return Object{Type: BOOL_OBJ, Bool: n.Value}, nil
	case *NilLiteral:
		return Object{Type: NIL_OBJ}, nil
	case *ListLiteral:
		return evalList(n, env)
	}
	return Object{}, &EvalError{Msg: fmt.Sprintf("unknown node: %T", node)}
}

func NewEvalEnv() *Environment {
	env := NewEnvironment()
	for name, obj := range builtins() {
		env.Set(name, obj)
	}
	return env
}

func evalProgram(prog *Program, env *Environment) (Object, error) {
	var result Object
	result.Type = NIL_OBJ
	for _, stmt := range prog.Statements {
		obj, err := Eval(stmt, env)
		if err != nil {
			return obj, err
		}
		if obj.Type == RETURN_OBJ {
			return obj, nil
		}
		result = obj
	}
	return result, nil
}

func evalAssign(stmt *AssignStmt, env *Environment) (Object, error) {
	val, err := Eval(stmt.Value, env)
	if err != nil {
		return Object{}, err
	}
	env.Set(stmt.Name, val)
	return val, nil
}

func evalIf(stmt *IfStmt, env *Environment) (Object, error) {
	cond, err := Eval(stmt.Condition, env)
	if err != nil {
		return Object{}, err
	}
	if isTruthy(cond) {
		return evalBlock(stmt.Consequent, env)
	}
	return evalBlock(stmt.Alternate, env)
}

func evalFor(stmt *ForStmt, env *Environment) (Object, error) {
	from, err := Eval(stmt.From, env)
	if err != nil {
		return Object{}, err
	}
	to, err := Eval(stmt.To, env)
	if err != nil {
		return Object{}, err
	}
	if from.Type != NUMBER_OBJ || to.Type != NUMBER_OBJ {
		return Object{}, &EvalError{Msg: "for loop range must be numbers"}
	}

	step := 1.0
	if stmt.Step != nil {
		s, err := Eval(stmt.Step, env)
		if err != nil {
			return Object{}, err
		}
		if s.Type != NUMBER_OBJ {
			return Object{}, &EvalError{Msg: "for loop step must be a number"}
		}
		step = s.Number
	}

	start := from.Number
	end := to.Number
	var result Object
	result.Type = NIL_OBJ

	for i := start; (step > 0 && i <= end) || (step < 0 && i >= end); i += step {
		loopEnv := NewEnclosedEnvironment(env)
		loopEnv.Set(stmt.Variable, Object{Type: NUMBER_OBJ, Number: i})
		for _, s := range stmt.Body {
			obj, err := Eval(s, loopEnv)
			if err != nil {
				return Object{}, err
			}
			if obj.Type == RETURN_OBJ {
				return obj, nil
			}
			result = obj
		}
	}
	return result, nil
}

func evalWhile(stmt *WhileStmt, env *Environment) (Object, error) {
	var result Object
	result.Type = NIL_OBJ
	for {
		cond, err := Eval(stmt.Condition, env)
		if err != nil {
			return Object{}, err
		}
		if !isTruthy(cond) {
			break
		}
		for _, s := range stmt.Body {
			obj, err := Eval(s, env)
			if err != nil {
				return Object{}, err
			}
			if obj.Type == RETURN_OBJ {
				return obj, nil
			}
			result = obj
		}
	}
	return result, nil
}

func evalFunctionDef(stmt *FunctionDef, env *Environment) (Object, error) {
	fn := Object{
		Type:   FUNCTION_OBJ,
		Params: stmt.Args,
		Body:   stmt.Body,
		Env:    env,
	}
	env.Set(stmt.Name, fn)
	return fn, nil
}

func evalCall(expr *CallExpr, env *Environment) (Object, error) {
	fn, err := Eval(expr.Function, env)
	if err != nil {
		return Object{}, err
	}

	args := make([]Object, len(expr.Args))
	for i, arg := range expr.Args {
		obj, err := Eval(arg, env)
		if err != nil {
			return Object{}, err
		}
		args[i] = obj
	}

	switch fn.Type {
	case FUNCTION_OBJ:
		if len(args) != len(fn.Params) {
			return Object{}, &EvalError{
				Msg: fmt.Sprintf("function expects %d args, got %d", len(fn.Params), len(args)),
			}
		}
		fnEnv := NewEnclosedEnvironment(fn.Env)
		for i, param := range fn.Params {
			fnEnv.Set(param, args[i])
		}
		result, err := evalBlock(fn.Body, fnEnv)
		if err != nil {
			return Object{}, err
		}
		if result.Type == RETURN_OBJ {
			return result, nil
		}
		return result, nil

	case BUILTIN_OBJ:
		return fn.Builtin(args)
	}

	return Object{}, &EvalError{Msg: "not a function"}
}

func evalIndex(expr *IndexExpr, env *Environment) (Object, error) {
	obj, err := Eval(expr.Object, env)
	if err != nil {
		return Object{}, err
	}
	idx, err := Eval(expr.Index, env)
	if err != nil {
		return Object{}, err
	}

	if obj.Type != LIST_OBJ {
		return Object{}, &EvalError{Msg: "can only index lists"}
	}
	if idx.Type != NUMBER_OBJ {
		return Object{}, &EvalError{Msg: "index must be a number"}
	}

	i := int(idx.Number)
	if i < 0 || i >= len(obj.Elements) {
		return Object{Type: NIL_OBJ}, nil
	}
	return obj.Elements[i], nil
}

func evalInfix(expr *InfixExpr, env *Environment) (Object, error) {
	left, err := Eval(expr.Left, env)
	if err != nil {
		return Object{}, err
	}
	right, err := Eval(expr.Right, env)
	if err != nil {
		return Object{}, err
	}

	switch {
	case left.Type == NUMBER_OBJ && right.Type == NUMBER_OBJ:
		return evalNumberInfix(expr.Operator, left, right)
	case expr.Operator == "+" && left.Type == STRING_OBJ:
		return Object{Type: STRING_OBJ, Value: left.Value + right.String()}, nil
	case expr.Operator == "==":
		return Object{Type: BOOL_OBJ, Bool: objectsEqual(left, right)}, nil
	case expr.Operator == "!=":
		return Object{Type: BOOL_OBJ, Bool: !objectsEqual(left, right)}, nil
	default:
		return Object{}, &EvalError{
			Msg: fmt.Sprintf("type mismatch: %s %s %s", left.Type, expr.Operator, right.Type),
		}
	}
}

func evalNumberInfix(op string, left, right Object) (Object, error) {
	l := left.Number
	r := right.Number
	switch op {
	case "+":
		return Object{Type: NUMBER_OBJ, Number: l + r}, nil
	case "-":
		return Object{Type: NUMBER_OBJ, Number: l - r}, nil
	case "*":
		return Object{Type: NUMBER_OBJ, Number: l * r}, nil
	case "/":
		if r == 0 {
			return Object{Type: NUMBER_OBJ, Number: math.Inf(1)}, nil
		}
		return Object{Type: NUMBER_OBJ, Number: l / r}, nil
	case "<":
		return Object{Type: BOOL_OBJ, Bool: l < r}, nil
	case ">":
		return Object{Type: BOOL_OBJ, Bool: l > r}, nil
	case "<=":
		return Object{Type: BOOL_OBJ, Bool: l <= r}, nil
	case ">=":
		return Object{Type: BOOL_OBJ, Bool: l >= r}, nil
	case "==":
		return Object{Type: BOOL_OBJ, Bool: l == r}, nil
	case "!=":
		return Object{Type: BOOL_OBJ, Bool: l != r}, nil
	}
	return Object{}, &EvalError{Msg: fmt.Sprintf("unknown operator: %s", op)}
}

func evalPrefix(expr *PrefixExpr, env *Environment) (Object, error) {
	right, err := Eval(expr.Right, env)
	if err != nil {
		return Object{}, err
	}
	switch expr.Operator {
	case "-":
		if right.Type != NUMBER_OBJ {
			return Object{}, &EvalError{Msg: "negation requires a number"}
		}
		return Object{Type: NUMBER_OBJ, Number: -right.Number}, nil
	case "not":
		return Object{Type: BOOL_OBJ, Bool: !isTruthy(right)}, nil
	}
	return Object{}, &EvalError{Msg: fmt.Sprintf("unknown prefix: %s", expr.Operator)}
}

func evalIdent(expr *Ident, env *Environment) (Object, error) {
	obj, ok := env.Get(expr.Name)
	if !ok {
		return Object{}, &EvalError{Msg: fmt.Sprintf("undefined variable: %s", expr.Name)}
	}
	return obj, nil
}

func evalList(expr *ListLiteral, env *Environment) (Object, error) {
	elems := make([]Object, len(expr.Elements))
	for i, elem := range expr.Elements {
		obj, err := Eval(elem, env)
		if err != nil {
			return Object{}, err
		}
		elems[i] = obj
	}
	return Object{Type: LIST_OBJ, Elements: elems}, nil
}

func evalBlock(stmts []Node, env *Environment) (Object, error) {
	var result Object
	result.Type = NIL_OBJ
	for _, stmt := range stmts {
		obj, err := Eval(stmt, env)
		if err != nil {
			return Object{}, err
		}
		if obj.Type == RETURN_OBJ {
			return obj, nil
		}
		result = obj
	}
	return result, nil
}

func isTruthy(obj Object) bool {
	switch obj.Type {
	case NIL_OBJ:
		return false
	case BOOL_OBJ:
		return obj.Bool
	case NUMBER_OBJ:
		return obj.Number != 0
	case STRING_OBJ:
		return obj.Value != ""
	default:
		return true
	}
}

func objectsEqual(a, b Object) bool {
	if a.Type != b.Type {
		return false
	}
	switch a.Type {
	case NIL_OBJ:
		return true
	case BOOL_OBJ:
		return a.Bool == b.Bool
	case NUMBER_OBJ:
		return a.Number == b.Number
	case STRING_OBJ:
		return a.Value == b.Value
	case LIST_OBJ:
		if len(a.Elements) != len(b.Elements) {
			return false
		}
		for i := range a.Elements {
			if !objectsEqual(a.Elements[i], b.Elements[i]) {
				return false
			}
		}
		return true
	}
	return false
}

func builtins() map[string]Object {
	return map[string]Object{
		"print": {
			Type: BUILTIN_OBJ,
			Builtin: func(args []Object) (Object, error) {
				for i, arg := range args {
					if i > 0 {
						fmt.Print(" ")
					}
					fmt.Print(arg.String())
				}
				fmt.Println()
				return Object{Type: NIL_OBJ}, nil
			},
		},
	}
}
