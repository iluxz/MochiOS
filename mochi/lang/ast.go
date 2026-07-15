package lang

type Node interface{}

type Program struct {
	Statements []Node
}

type StmtExpr struct {
	Expr Node
}

type AssignStmt struct {
	Name  string
	Value Node
}

type IfStmt struct {
	Condition  Node
	Consequent []Node
	Alternate  []Node
}

type ForStmt struct {
	Variable string
	From     Node
	To       Node
	Step     Node
	Body     []Node
}

type WhileStmt struct {
	Condition Node
	Body      []Node
}

type FunctionDef struct {
	Name string
	Args []string
	Body []Node
}

type InfixExpr struct {
	Left     Node
	Operator string
	Right    Node
}

type PrefixExpr struct {
	Operator string
	Right    Node
}

type CallExpr struct {
	Function Node
	Args     []Node
}

type IndexExpr struct {
	Object Node
	Index  Node
}

type Ident struct {
	Name string
}

type NumberLiteral struct {
	Value float64
	Raw   string
}

type StringLiteral struct {
	Value string
}

type BoolLiteral struct {
	Value bool
}

type NilLiteral struct{}

type ListLiteral struct {
	Elements []Node
}
