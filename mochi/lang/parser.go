package lang

import (
	"fmt"
	"strconv"
)

type Parser struct {
	tokens []Token
	pos    int
}

type ParseError struct {
	Token Token
	Msg   string
}

func (e *ParseError) Error() string {
	return fmt.Sprintf("parse error at line %d:%d: %s", e.Token.Line, e.Token.Col, e.Msg)
}

func Parse(input string) (*Program, error) {
	tokens := Lex(input)
	p := &Parser{tokens: tokens, pos: 0}
	prog := &Program{}

	for p.peek().Type != EOF {
		stmt, err := p.parseStmt()
		if err != nil {
			return nil, err
		}
		if stmt != nil {
			prog.Statements = append(prog.Statements, stmt)
		}
	}
	return prog, nil
}

func (p *Parser) peek() Token {
	if p.pos >= len(p.tokens) {
		return Token{Type: EOF}
	}
	return p.tokens[p.pos]
}

func (p *Parser) advance() Token {
	tok := p.peek()
	if tok.Type != EOF {
		p.pos++
	}
	return tok
}

func (p *Parser) expect(tt TokenType) (Token, error) {
	tok := p.peek()
	if tok.Type != tt {
		return tok, &ParseError{Token: tok, Msg: fmt.Sprintf("expected %d, got %s", tt, tok.Literal)}
	}
	return p.advance(), nil
}

func (p *Parser) peekN(n int) Token {
	idx := p.pos + n
	if idx >= len(p.tokens) {
		return Token{Type: EOF}
	}
	return p.tokens[idx]
}

func (p *Parser) skipNewlines() {
	for p.peek().Type == NEWLINE {
		p.advance()
	}
}

func (p *Parser) parseStmt() (Node, error) {
	tok := p.peek()

	switch tok.Type {
	case NEWLINE:
		p.advance()
		return nil, nil
	case DEDENT:
		return nil, nil
	case INDENT:
		return nil, &ParseError{Token: tok, Msg: "unexpected indent"}
	case EOF:
		return nil, nil
	case IF:
		return p.parseIf()
	case FOR:
		return p.parseFor()
	case WHILE:
		return p.parseWhile()
	case FUNCTION:
		return p.parseFunction()
	case PRINT:
		return p.parsePrint()
	}

	if tok.Type == IDENTIFIER && p.peekN(1).Type == ASSIGN {
		return p.parseAssign()
	}

	expr, err := p.parseExpr(0)
	if err != nil {
		return nil, err
	}
	return &StmtExpr{Expr: expr}, nil
}

const (
	LOWEST = iota
	OR_LEVEL
	AND_LEVEL
	COMPARE_LEVEL
	SUM_LEVEL
	PROD_LEVEL
	PREFIX_LEVEL
	CALL_LEVEL
)

var precedences = map[TokenType]int{
	OR:        OR_LEVEL,
	AND:       AND_LEVEL,
	EQ:        COMPARE_LEVEL,
	NEQ:       COMPARE_LEVEL,
	LT:        COMPARE_LEVEL,
	GT:        COMPARE_LEVEL,
	LE:        COMPARE_LEVEL,
	GE:        COMPARE_LEVEL,
	PLUS:      SUM_LEVEL,
	MINUS:     SUM_LEVEL,
	STAR:      PROD_LEVEL,
	SLASH:     PROD_LEVEL,
	LPAREN:    CALL_LEVEL,
	LBRACKET:  CALL_LEVEL,
}

func (p *Parser) parseExpr(prec int) (Node, error) {
	left, err := p.parsePrefix()
	if err != nil {
		return nil, err
	}

	for {
		tok := p.peek()
		if tok.Type == NEWLINE || tok.Type == EOF || tok.Type == COMMA || tok.Type == DEDENT ||
			tok.Type == RPAREN || tok.Type == RBRACKET || tok.Type == ELSE {
			break
		}

		opPrec, ok := precedences[tok.Type]
		if !ok || opPrec <= prec {
			break
		}

		switch tok.Type {
		case LPAREN:
			p.advance()
			left, err = p.parseCallArgs(left)
			if err != nil {
				return nil, err
			}
		case LBRACKET:
			p.advance()
			left, err = p.parseIndex(left)
			if err != nil {
				return nil, err
			}
		default:
			left, err = p.parseInfix(left, opPrec)
			if err != nil {
				return nil, err
			}
		}
	}

	return left, nil
}

func (p *Parser) parsePrefix() (Node, error) {
	tok := p.advance()

	switch tok.Type {
	case NUMBER:
		val, err := strconv.ParseFloat(tok.Literal, 64)
		if err != nil {
			return nil, &ParseError{Token: tok, Msg: "invalid number: " + tok.Literal}
		}
		return &NumberLiteral{Value: val, Raw: tok.Literal}, nil

	case STRING:
		return &StringLiteral{Value: tok.Literal}, nil

	case TRUE:
		return &BoolLiteral{Value: true}, nil

	case FALSE:
		return &BoolLiteral{Value: false}, nil

	case NIL:
		return &NilLiteral{}, nil

	case IDENTIFIER:
		return &Ident{Name: tok.Literal}, nil

	case MINUS:
		right, err := p.parseExpr(PREFIX_LEVEL)
		if err != nil {
			return nil, err
		}
		return &PrefixExpr{Operator: "-", Right: right}, nil

	case NOT:
		right, err := p.parseExpr(PREFIX_LEVEL)
		if err != nil {
			return nil, err
		}
		return &PrefixExpr{Operator: "not", Right: right}, nil

	case LPAREN:
		expr, err := p.parseExpr(LOWEST)
		if err != nil {
			return nil, err
		}
		if _, err := p.expect(RPAREN); err != nil {
			return nil, err
		}
		return expr, nil

	case LBRACKET:
		var elems []Node
		for p.peek().Type != RBRACKET && p.peek().Type != EOF {
			elem, err := p.parseExpr(LOWEST)
			if err != nil {
				return nil, err
			}
			elems = append(elems, elem)
			if p.peek().Type == COMMA {
				p.advance()
			}
		}
		if _, err := p.expect(RBRACKET); err != nil {
			return nil, err
		}
		return &ListLiteral{Elements: elems}, nil

	case PRINT:
		return nil, &ParseError{Token: tok, Msg: "print used as expression"}
	}

	return nil, &ParseError{Token: tok, Msg: fmt.Sprintf("unexpected token: %s", tok.Literal)}
}

func (p *Parser) parseInfix(left Node, prec int) (Node, error) {
	tok := p.advance()

	switch tok.Type {
	case PLUS:
		right, err := p.parseExpr(prec)
		if err != nil {
			return nil, err
		}
		return &InfixExpr{Left: left, Operator: "+", Right: right}, nil

	case MINUS:
		right, err := p.parseExpr(prec)
		if err != nil {
			return nil, err
		}
		return &InfixExpr{Left: left, Operator: "-", Right: right}, nil

	case STAR:
		right, err := p.parseExpr(prec)
		if err != nil {
			return nil, err
		}
		return &InfixExpr{Left: left, Operator: "*", Right: right}, nil

	case SLASH:
		right, err := p.parseExpr(prec)
		if err != nil {
			return nil, err
		}
		return &InfixExpr{Left: left, Operator: "/", Right: right}, nil

	case EQ:
		right, err := p.parseExpr(prec)
		if err != nil {
			return nil, err
		}
		return &InfixExpr{Left: left, Operator: "==", Right: right}, nil

	case NEQ:
		right, err := p.parseExpr(prec)
		if err != nil {
			return nil, err
		}
		return &InfixExpr{Left: left, Operator: "!=", Right: right}, nil

	case LT:
		right, err := p.parseExpr(prec)
		if err != nil {
			return nil, err
		}
		return &InfixExpr{Left: left, Operator: "<", Right: right}, nil

	case GT:
		right, err := p.parseExpr(prec)
		if err != nil {
			return nil, err
		}
		return &InfixExpr{Left: left, Operator: ">", Right: right}, nil

	case LE:
		right, err := p.parseExpr(prec)
		if err != nil {
			return nil, err
		}
		return &InfixExpr{Left: left, Operator: "<=", Right: right}, nil

	case GE:
		right, err := p.parseExpr(prec)
		if err != nil {
			return nil, err
		}
		return &InfixExpr{Left: left, Operator: ">=", Right: right}, nil

	case AND:
		right, err := p.parseExpr(prec)
		if err != nil {
			return nil, err
		}
		return &InfixExpr{Left: left, Operator: "and", Right: right}, nil

	case OR:
		right, err := p.parseExpr(prec)
		if err != nil {
			return nil, err
		}
		return &InfixExpr{Left: left, Operator: "or", Right: right}, nil
	}

	return nil, &ParseError{Token: tok, Msg: fmt.Sprintf("unknown infix operator: %s", tok.Literal)}
}

func (p *Parser) parseCallArgs(fn Node) (Node, error) {
	var args []Node
	for p.peek().Type != RPAREN && p.peek().Type != EOF {
		arg, err := p.parseExpr(LOWEST)
		if err != nil {
			return nil, err
		}
		args = append(args, arg)
		if p.peek().Type == COMMA {
			p.advance()
		}
	}
	if _, err := p.expect(RPAREN); err != nil {
		return nil, err
	}
	return &CallExpr{Function: fn, Args: args}, nil
}

func (p *Parser) parseIndex(left Node) (Node, error) {
	index, err := p.parseExpr(LOWEST)
	if err != nil {
		return nil, err
	}
	if _, err := p.expect(RBRACKET); err != nil {
		return nil, err
	}
	return &IndexExpr{Object: left, Index: index}, nil
}

func (p *Parser) parseAssign() (Node, error) {
	nameTok := p.advance()
	p.advance()
	val, err := p.parseExpr(LOWEST)
	if err != nil {
		return nil, err
	}
	return &AssignStmt{Name: nameTok.Literal, Value: val}, nil
}

func (p *Parser) parseBlock() ([]Node, error) {
	if p.peek().Type != NEWLINE {
		return nil, &ParseError{Token: p.peek(), Msg: "expected newline before block"}
	}
	p.advance()

	if _, err := p.expect(INDENT); err != nil {
		return nil, err
	}

	var stmts []Node
	for p.peek().Type != DEDENT && p.peek().Type != EOF {
		stmt, err := p.parseStmt()
		if err != nil {
			return nil, err
		}
		if stmt != nil {
			stmts = append(stmts, stmt)
		}
	}

	if _, err := p.expect(DEDENT); err != nil {
		return nil, err
	}
	return stmts, nil
}

func (p *Parser) parseIf() (Node, error) {
	p.advance()

	cond, err := p.parseExpr(LOWEST)
	if err != nil {
		return nil, err
	}

	consequent, err := p.parseBlock()
	if err != nil {
		return nil, err
	}

	var alternate []Node
	if p.peek().Type == DEDENT {
		return nil, &ParseError{Token: p.peek(), Msg: "unexpected dedent"}
	}
	if p.peek().Type == ELSE {
		p.advance()
		if p.peek().Type == IF {
			elseIf, err := p.parseIf()
			if err != nil {
				return nil, err
			}
			alternate = []Node{elseIf}
		} else {
			alternate, err = p.parseBlock()
			if err != nil {
				return nil, err
			}
		}
	}

	return &IfStmt{Condition: cond, Consequent: consequent, Alternate: alternate}, nil
}

func (p *Parser) parseFor() (Node, error) {
	p.advance()

	varTok := p.advance()
	if varTok.Type != IDENTIFIER {
		return nil, &ParseError{Token: varTok, Msg: "expected variable name after 'for'"}
	}

	if _, err := p.expect(ASSIGN); err != nil {
		return nil, err
	}

	from, err := p.parseExpr(LOWEST)
	if err != nil {
		return nil, err
	}

	if _, err := p.expect(COMMA); err != nil {
		return nil, err
	}

	to, err := p.parseExpr(LOWEST)
	if err != nil {
		return nil, err
	}

	var step Node
	if p.peek().Type == COMMA {
		p.advance()
		step, err = p.parseExpr(LOWEST)
		if err != nil {
			return nil, err
		}
	}

	body, err := p.parseBlock()
	if err != nil {
		return nil, err
	}

	return &ForStmt{
		Variable: varTok.Literal,
		From:     from,
		To:       to,
		Step:     step,
		Body:     body,
	}, nil
}

func (p *Parser) parseWhile() (Node, error) {
	p.advance()

	cond, err := p.parseExpr(LOWEST)
	if err != nil {
		return nil, err
	}

	body, err := p.parseBlock()
	if err != nil {
		return nil, err
	}

	return &WhileStmt{Condition: cond, Body: body}, nil
}

func (p *Parser) parseFunction() (Node, error) {
	p.advance()

	nameTok := p.advance()
	if nameTok.Type != IDENTIFIER {
		return nil, &ParseError{Token: nameTok, Msg: "expected function name"}
	}

	var args []string
	for p.peek().Type == IDENTIFIER {
		args = append(args, p.advance().Literal)
	}

	body, err := p.parseBlock()
	if err != nil {
		return nil, err
	}

	return &FunctionDef{Name: nameTok.Literal, Args: args, Body: body}, nil
}

func (p *Parser) parsePrint() (Node, error) {
	p.advance()

	if p.peek().Type == LPAREN {
		p.advance()
		var args []Node
		for p.peek().Type != RPAREN && p.peek().Type != EOF {
			arg, err := p.parseExpr(LOWEST)
			if err != nil {
				return nil, err
			}
			args = append(args, arg)
			if p.peek().Type == COMMA {
				p.advance()
			}
		}
		if _, err := p.expect(RPAREN); err != nil {
			return nil, err
		}
		return &StmtExpr{Expr: &CallExpr{
			Function: &Ident{Name: "print"},
			Args:     args,
		}}, nil
	}

	arg, err := p.parseExpr(LOWEST)
	if err != nil {
		return nil, err
	}
	return &StmtExpr{Expr: &CallExpr{
		Function: &Ident{Name: "print"},
		Args:     []Node{arg},
	}	}, nil
}
