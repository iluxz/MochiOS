package cmd

import (
	"fmt"
	"os"

	"mochi/lang"
)

func runFile(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: mochi run <file.mochi>")
	}

	src, err := os.ReadFile(args[0])
	if err != nil {
		return fmt.Errorf("reading file: %v", err)
	}

	prog, err := lang.Parse(string(src))
	if err != nil {
		return fmt.Errorf("parse error: %v", err)
	}

	env := lang.NewEvalEnv()
	_, err = lang.Eval(prog, env)
	if err != nil {
		return fmt.Errorf("runtime error: %v", err)
	}

	return nil
}
