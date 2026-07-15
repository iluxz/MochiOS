package lang

type TokenType int

const (
	ILLEGAL TokenType = iota
	EOF
	NEWLINE
	INDENT
	DEDENT

	IDENTIFIER
	NUMBER
	STRING

	ASSIGN
	PLUS
	MINUS
	STAR
	SLASH
	EQ
	NEQ
	LT
	GT
	LE
	GE
	COMMA
	LPAREN
	RPAREN
	LBRACKET
	RBRACKET

	AND
	OR
	NOT
	IF
	ELSE
	FOR
	WHILE
	FUNCTION
	TRUE
	FALSE
	NIL
	PRINT
)

type Token struct {
	Type    TokenType
	Literal string
	Line    int
	Col     int
}

var keywords = map[string]TokenType{
	"and":      AND,
	"or":       OR,
	"not":      NOT,
	"if":       IF,
	"else":     ELSE,
	"for":      FOR,
	"while":    WHILE,
	"function": FUNCTION,
	"true":     TRUE,
	"false":    FALSE,
	"nil":      NIL,
	"print":    PRINT,
}

func LookupIdent(ident string) TokenType {
	if t, ok := keywords[ident]; ok {
		return t
	}
	return IDENTIFIER
}
