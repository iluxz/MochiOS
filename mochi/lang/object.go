package lang

import "fmt"

type ObjectType string

const (
	NUMBER_OBJ  ObjectType = "NUMBER"
	STRING_OBJ  ObjectType = "STRING"
	BOOL_OBJ    ObjectType = "BOOL"
	NIL_OBJ     ObjectType = "NIL"
	LIST_OBJ    ObjectType = "LIST"
	FUNCTION_OBJ ObjectType = "FUNCTION"
	BUILTIN_OBJ ObjectType = "BUILTIN"
	RETURN_OBJ  ObjectType = "RETURN"
)

type Object struct {
	Type ObjectType

	Number  float64
	String  string
	Bool    bool
	Elements []Object
	Params  []string
	Body    []Node
	Env     *Environment

	Builtin func(args []Object) (Object, error)
}

type Environment struct {
	store  map[string]Object
	outer  *Environment
}

func NewEnvironment() *Environment {
	return &Environment{store: make(map[string]Object)}
}

func NewEnclosedEnvironment(outer *Environment) *Environment {
	env := NewEnvironment()
	env.outer = outer
	return env
}

func (e *Environment) Get(name string) (Object, bool) {
	obj, ok := e.store[name]
	if !ok && e.outer != nil {
		return e.outer.Get(name)
	}
	return obj, ok
}

func (e *Environment) Set(name string, obj Object) {
	e.store[name] = obj
}

func (o Object) String() string {
	switch o.Type {
	case NIL_OBJ:
		return "nil"
	case NUMBER_OBJ:
		if o.Number == float64(int64(o.Number)) {
			return fmt.Sprintf("%.0f", o.Number)
		}
		return fmt.Sprintf("%g", o.Number)
	case STRING_OBJ:
		return o.String
	case BOOL_OBJ:
		if o.Bool {
			return "true"
		}
		return "false"
	case LIST_OBJ:
		elems := make([]string, len(o.Elements))
		for i, e := range o.Elements {
			elems[i] = e.String()
		}
		return "[" + join(elems, ", ") + "]"
	case FUNCTION_OBJ:
		return fmt.Sprintf("<function %s>", o.String)
	case BUILTIN_OBJ:
		return "<builtin>"
	case RETURN_OBJ:
		return "return"
	}
	return "<object>"
}

func join(elems []string, sep string) string {
	if len(elems) == 0 {
		return ""
	}
	result := elems[0]
	for _, e := range elems[1:] {
		result += sep + e
	}
	return result
}
