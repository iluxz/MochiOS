package cmd

import "fmt"

func search(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: mochi search <query>")
	}
	return runPacman(append([]string{"-Ss"}, args...)...)
}
